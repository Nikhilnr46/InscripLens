"""GPU-accelerated training of CharacterCNN on the full EpiSAM dataset (10,281 training crops, 781 classes)."""
import json
import time
import random
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps
import torch
from torch import nn

ROOT = Path(__file__).resolve().parent.parent

class CharacterCNN(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),  # 32 x 32

            nn.Conv2d(32, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2),  # 16 x 16

            nn.Conv2d(64, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2),  # 8 x 8
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 8 * 8, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes)
        )

    def forward(self, x):
        return self.classifier(self.features(x))

def extract_crops_and_labels(chars_dir, bin_dir):
    crops = []
    labels = []
    folders = sorted(list(chars_dir.iterdir()))
    for folder in folders:
        if not folder.is_dir():
            continue
        mask_file = bin_dir / (folder.name + '.png')
        if not mask_file.exists():
            continue
        jf = folder / 'character_polygons.json'
        if not jf.exists():
            continue
        data = json.loads(jf.read_text(encoding='utf-8'))
        with Image.open(mask_file) as im:
            w, h = im.size
            for k, v in data.items():
                if not isinstance(v, dict):
                    continue
                lbl = str(v.get('char_name', '')).strip()
                if not lbl or lbl in ('NaNl', 'None', 'nan', 'null'):
                    continue
                tl, br = v.get('top_left'), v.get('bottom_right')
                if not tl or not br or len(tl) != 2 or len(br) != 2:
                    continue
                x1 = max(0, min(tl[0], w - 2))
                y1 = max(0, min(tl[1], h - 2))
                x2 = max(x1 + 1, min(br[0], w))
                y2 = max(y1 + 1, min(br[1], h))
                crop = im.crop((x1, y1, x2, y2))
                crop = ImageOps.contain(crop.convert('L'), (64, 64), Image.Resampling.BILINEAR)
                canvas = Image.new('L', (64, 64), 0)
                canvas.paste(crop, ((64 - crop.width) // 2, (64 - crop.height) // 2))
                crops.append(np.array(canvas, dtype=np.float32)[None] / 255.0)
                labels.append(lbl)
    return crops, labels

def evaluate_model(model, x, y, device, batch_size=128):
    model.eval()
    top1_correct = 0
    top3_correct = 0
    total = len(y)
    with torch.inference_mode():
        for i in range(0, total, batch_size):
            bx = x[i:i + batch_size].to(device)
            by = y[i:i + batch_size].to(device)
            out = model(bx)
            preds = out.argmax(dim=1)
            top1_correct += (preds == by).sum().item()
            # top-3
            _, top3_indices = out.topk(min(3, out.size(1)), dim=1)
            top3_correct += (top3_indices == by.unsqueeze(1)).any(dim=1).sum().item()
    return top1_correct, top3_correct

def main():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print("=" * 60)
    print("TRAINING BROAD EPISAM CHARACTER CNN ON GPU")
    print(f"Device target: {device}")
    if device.type == 'cuda':
        print(f"GPU Name: {torch.cuda.get_device_name(0)}")
        print(f"VRAM Total: {torch.cuda.get_device_properties(0).total_memory / (1024**2):.1f} MB")
        torch.backends.cudnn.benchmark = True
    print("=" * 60, flush=True)

    start_total = time.perf_counter()
    episam_root = ROOT / 'episam/episam_dataset/episam_dataset'
    out = ROOT / 'outputs/cnn_study'
    out.mkdir(exist_ok=True)

    # 1. Extract training crops
    print("Extracting training crops from episam/chars/train...", flush=True)
    t0 = time.perf_counter()
    train_crops, train_labels = extract_crops_and_labels(
        episam_root / 'chars/train', episam_root / 'binary_images/train'
    )
    print(f"Extracted {len(train_crops)} training crops in {time.perf_counter() - t0:.2f}s", flush=True)

    # Build class index
    classes = sorted(set(train_labels))
    class_to_idx = {c: i for i, c in enumerate(classes)}
    print(f"Total character classes: {len(classes)}", flush=True)

    # 2. Extract validation crops
    print("Extracting validation crops from episam/chars/val...", flush=True)
    t1 = time.perf_counter()
    val_crops, val_labels = extract_crops_and_labels(
        episam_root / 'chars/val', episam_root / 'binary_images/val'
    )
    # Filter validation to seen classes
    seen_val_indices = [i for i, lbl in enumerate(val_labels) if lbl in class_to_idx]
    val_crops_seen = [val_crops[i] for i in seen_val_indices]
    val_labels_seen = [val_labels[i] for i in seen_val_indices]
    print(f"Extracted {len(val_crops)} total val crops ({len(val_crops_seen)} with seen classes) in {time.perf_counter() - t1:.2f}s", flush=True)

    # Convert to PyTorch tensors
    x_train = torch.from_numpy(np.stack(train_crops))
    y_train = torch.tensor([class_to_idx[lbl] for lbl in train_labels])
    x_val = torch.from_numpy(np.stack(val_crops_seen))
    y_val = torch.tensor([class_to_idx[lbl] for lbl in val_labels_seen])

    # Dataset & DataLoader
    train_dataset = torch.utils.data.TensorDataset(x_train, y_train)
    train_loader = torch.utils.data.DataLoader(
        train_dataset, batch_size=64, shuffle=True, pin_memory=(device.type == 'cuda'), drop_last=False
    )

    # Initialize model
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    if device.type == 'cuda':
        torch.cuda.manual_seed_all(42)

    model = CharacterCNN(len(classes)).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.0001)
    criterion = nn.CrossEntropyLoss()
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=20)

    epochs = 20
    print(f"Training CharacterCNN for {epochs} epochs on GPU...", flush=True)
    logs = []
    best_val_correct = 0

    for epoch in range(1, epochs + 1):
        ep_start = time.perf_counter()
        model.train()
        train_loss = 0.0

        for bx, by in train_loader:
            bx = bx.to(device, non_blocking=True)
            by = by.to(device, non_blocking=True)
            optimizer.zero_grad()
            out_logits = model(bx)
            loss = criterion(out_logits, by)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * len(by)

        scheduler.step()
        train_loss /= len(y_train)
        ep_seconds = time.perf_counter() - ep_start

        # Evaluate validation set
        val_top1, val_top3 = evaluate_model(model, x_val, y_val, device)
        val_acc = val_top1 / len(y_val)
        val_top3_acc = val_top3 / len(y_val)

        row = {
            'epoch': epoch,
            'train_loss': round(train_loss, 4),
            'val_top1_correct': val_top1,
            'val_top1_accuracy': round(val_acc, 4),
            'val_top3_correct': val_top3,
            'val_top3_accuracy': round(val_top3_acc, 4),
            'epoch_seconds': round(ep_seconds, 2)
        }
        logs.append(row)
        print(f"Epoch {epoch:2d}/{epochs} - Loss: {train_loss:.4f} | Val Top-1: {val_top1}/{len(y_val)} ({val_acc*100:.1f}%) | Val Top-3: {val_top3}/{len(y_val)} ({val_top3_acc*100:.1f}%) | Time: {ep_seconds:.2f}s", flush=True)

        if val_top1 > best_val_correct:
            best_val_correct = val_top1
            # Save best checkpoint
            torch.save({
                'state_dict': model.state_dict(),
                'classes': classes,
                'input': 'predicted_mask_64_letterbox',
                'epoch': epoch,
                'val_accuracy': val_acc,
                'val_top3_accuracy': val_top3_acc
            }, out / 'character_cnn_episam_gpu.pth')

    peak_vram_mb = 0.0
    if device.type == 'cuda':
        peak_vram_mb = torch.cuda.max_memory_allocated() / (1024**2)

    total_time = time.perf_counter() - start_total
    summary = {
        'model': 'Broad EpiSAM CharacterCNN (GPU)',
        'device': str(device),
        'gpu_name': torch.cuda.get_device_name(0) if device.type == 'cuda' else 'CPU',
        'peak_vram_mb': round(peak_vram_mb, 2),
        'training_samples': len(train_crops),
        'classes': len(classes),
        'validation_samples_total': len(val_crops),
        'validation_samples_seen': len(val_crops_seen),
        'best_val_top1_correct': best_val_correct,
        'best_val_top1_accuracy': round(best_val_correct / len(y_val), 4),
        'final_val_top3_accuracy': round(val_top3_acc, 4),
        'epochs': epochs,
        'total_training_seconds': round(total_time, 2),
        'checkpoint_path': str(out / 'character_cnn_episam_gpu.pth')
    }

    (out / 'summary_episam_gpu.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print("=" * 60)
    print("EPISAM BROAD TRAINING COMPLETE:")
    print(json.dumps(summary, indent=2))
    print("=" * 60, flush=True)

if __name__ == '__main__':
    main()

