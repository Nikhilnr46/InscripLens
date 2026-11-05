"""GPU-accelerated training of Line-Segmentation U-Net on the EpiSAM line dataset (117 train, 31 val inscriptions)."""
import json
import time
import random
from pathlib import Path
import numpy as np
from PIL import Image
import torch
from torch import nn

ROOT = Path(__file__).resolve().parent.parent

class DoubleConv(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True)
        )
    def forward(self, x):
        return self.conv(x)

class LineUNet(nn.Module):
    def __init__(self, in_channels=1, out_channels=1):
        super().__init__()
        self.inc = DoubleConv(in_channels, 16)
        self.down1 = nn.Sequential(nn.MaxPool2d(2), DoubleConv(16, 32))
        self.down2 = nn.Sequential(nn.MaxPool2d(2), DoubleConv(32, 64))
        self.down3 = nn.Sequential(nn.MaxPool2d(2), DoubleConv(64, 128))

        self.up1 = nn.ConvTranspose2d(128, 64, 2, stride=2)
        self.conv_up1 = DoubleConv(128, 64)

        self.up2 = nn.ConvTranspose2d(64, 32, 2, stride=2)
        self.conv_up2 = DoubleConv(64, 32)

        self.up3 = nn.ConvTranspose2d(32, 16, 2, stride=2)
        self.conv_up3 = DoubleConv(32, 16)

        self.outc = nn.Conv2d(16, out_channels, 1)

    def forward(self, x):
        x1 = self.inc(x)
        x2 = self.down1(x1)
        x3 = self.down2(x2)
        x4 = self.down3(x3)

        d3 = self.up1(x4)
        d3 = torch.cat([d3, x3], dim=1)
        d3 = self.conv_up1(d3)

        d2 = self.up2(d3)
        d2 = torch.cat([d2, x2], dim=1)
        d2 = self.conv_up2(d2)

        d1 = self.up3(d2)
        d1 = torch.cat([d1, x1], dim=1)
        d1 = self.conv_up3(d1)

        logits = self.outc(d1)
        return torch.sigmoid(logits)

def load_line_dataset(split='train', target_size=(256, 256)):
    episam_root = ROOT / 'episam/episam_dataset/episam_dataset'
    lines_dir = episam_root / f'lines/{split}'
    bin_dir = episam_root / f'binary_images/{split}'

    inputs = []
    targets = []
    names = []

    folders = sorted(list(lines_dir.iterdir()))
    for folder in folders:
        if not folder.is_dir():
            continue
        mask_file = bin_dir / (folder.name + '.png')
        if not mask_file.exists():
            continue
        line_files = list(folder.glob('line_*_mask.png'))
        if not line_files:
            continue

        # Composite ground-truth line band
        composite = None
        for lf in line_files:
            with Image.open(lf) as lim:
                arr = (np.array(lim.convert('L')) > 128).astype(np.uint8)
                if composite is None:
                    composite = arr
                else:
                    composite = np.maximum(composite, arr)

        # Load input stroke mask
        with Image.open(mask_file) as im:
            input_pil = im.convert('L').resize(target_size, Image.Resampling.BILINEAR)
            target_pil = Image.fromarray(composite * 255).resize(target_size, Image.Resampling.NEAREST)

        in_tensor = np.array(input_pil, dtype=np.float32)[None] / 255.0
        tar_tensor = (np.array(target_pil, dtype=np.float32)[None] > 128).astype(np.float32)

        inputs.append(in_tensor)
        targets.append(tar_tensor)
        names.append(folder.name)

    return np.stack(inputs), np.stack(targets), names

class DiceBCELoss(nn.Module):
    def __init__(self, smooth=1.0):
        super().__init__()
        self.smooth = smooth
        self.bce = nn.BCELoss()

    def forward(self, pred, target):
        bce_loss = self.bce(pred, target)
        pred_flat = pred.view(-1)
        target_flat = target.view(-1)
        intersection = (pred_flat * target_flat).sum()
        dice = (2.0 * intersection + self.smooth) / (pred_flat.sum() + target_flat.sum() + self.smooth)
        return bce_loss + (1.0 - dice)

def compute_metrics(pred_probs, targets, threshold=0.5):
    preds = (pred_probs > threshold).float()
    intersection = (preds * targets).sum().item()
    total_pred = preds.sum().item()
    total_target = targets.sum().item()
    union = total_pred + total_target - intersection

    dice = (2.0 * intersection + 1e-6) / (total_pred + total_target + 1e-6)
    iou = (intersection + 1e-6) / (union + 1e-6)
    return dice, iou

def main():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print("=" * 60)
    print("TRAINING EPISAM LINE-SEGMENTATION U-NET ON GPU")
    print(f"Device target: {device}")
    if device.type == 'cuda':
        print(f"GPU Name: {torch.cuda.get_device_name(0)}")
        print(f"VRAM Total: {torch.cuda.get_device_properties(0).total_memory / (1024**2):.1f} MB")
        torch.backends.cudnn.benchmark = True
    print("=" * 60, flush=True)

    start_total = time.perf_counter()
    out = ROOT / 'outputs/line_study'
    out.mkdir(exist_ok=True)

    print("Loading training line datasets (117 inscriptions, 912 line masks)...", flush=True)
    t0 = time.perf_counter()
    x_train_np, y_train_np, train_names = load_line_dataset('train', target_size=(256, 256))
    print(f"Loaded {len(train_names)} train records in {time.perf_counter() - t0:.2f}s", flush=True)

    print("Loading validation line datasets (31 inscriptions, 254 line masks)...", flush=True)
    t1 = time.perf_counter()
    x_val_np, y_val_np, val_names = load_line_dataset('val', target_size=(256, 256))
    print(f"Loaded {len(val_names)} val records in {time.perf_counter() - t1:.2f}s", flush=True)

    x_train = torch.from_numpy(x_train_np)
    y_train = torch.from_numpy(y_train_np)
    x_val = torch.from_numpy(x_val_np)
    y_val = torch.from_numpy(y_val_np)

    train_dataset = torch.utils.data.TensorDataset(x_train, y_train)
    train_loader = torch.utils.data.DataLoader(
        train_dataset, batch_size=4, shuffle=True, pin_memory=(device.type == 'cuda')
    )

    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    if device.type == 'cuda':
        torch.cuda.manual_seed_all(42)

    model = LineUNet(1, 1).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=1e-4)
    criterion = DiceBCELoss()
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=20)

    epochs = 20
    print(f"Training LineUNet for {epochs} epochs on GPU...", flush=True)
    logs = []
    best_dice = 0.0

    for epoch in range(1, epochs + 1):
        ep_start = time.perf_counter()
        model.train()
        train_loss = 0.0

        for bx, by in train_loader:
            bx = bx.to(device, non_blocking=True)
            by = by.to(device, non_blocking=True)
            optimizer.zero_grad()
            out_preds = model(bx)
            loss = criterion(out_preds, by)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * len(by)

        scheduler.step()
        train_loss /= len(x_train)
        ep_seconds = time.perf_counter() - ep_start

        # Evaluate validation set
        model.eval()
        with torch.inference_mode():
            val_preds_list = []
            for i in range(0, len(x_val), 4):
                bvx = x_val[i:i + 4].to(device)
                val_preds_list.append(model(bvx).cpu())
            all_val_preds = torch.cat(val_preds_list, dim=0)

        val_dice, val_iou = compute_metrics(all_val_preds, y_val)
        row = {
            'epoch': epoch,
            'train_loss': round(train_loss, 4),
            'val_dice': round(val_dice, 4),
            'val_iou': round(val_iou, 4),
            'epoch_seconds': round(ep_seconds, 2)
        }
        logs.append(row)
        print(f"Epoch {epoch:2d}/{epochs} - Loss: {train_loss:.4f} | Val Dice: {val_dice:.4f} | Val IoU: {val_iou:.4f} | Time: {ep_seconds:.2f}s", flush=True)

        if val_dice > best_dice:
            best_dice = val_dice
            torch.save({
                'state_dict': model.state_dict(),
                'input': 'binary_stroke_mask_256x256',
                'epoch': epoch,
                'val_dice': val_dice,
                'val_iou': val_iou
            }, out / 'line_segmentation_episam_gpu.pth')

    peak_vram_mb = 0.0
    if device.type == 'cuda':
        peak_vram_mb = torch.cuda.max_memory_allocated() / (1024**2)

    total_time = time.perf_counter() - start_total
    summary = {
        'model': 'LineUNet Segmentation (GPU accelerated)',
        'device': str(device),
        'gpu_name': torch.cuda.get_device_name(0) if device.type == 'cuda' else 'CPU',
        'peak_vram_mb': round(peak_vram_mb, 2),
        'training_inscriptions': len(train_names),
        'training_individual_lines': 912,
        'validation_inscriptions': len(val_names),
        'validation_individual_lines': 254,
        'best_validation_dice': round(best_dice, 4),
        'final_validation_iou': round(val_iou, 4),
        'epochs': epochs,
        'total_training_seconds': round(total_time, 2),
        'checkpoint_path': str(out / 'line_segmentation_episam_gpu.pth')
    }

    (out / 'summary_lines_gpu.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print("=" * 60)
    print("LINE SEGMENTATION TRAINING COMPLETE:")
    print(json.dumps(summary, indent=2))
    print("=" * 60, flush=True)

if __name__ == '__main__':
    main()
