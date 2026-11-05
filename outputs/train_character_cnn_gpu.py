"""GPU-accelerated training and evaluation of CharacterCNN for historical Kannada epigraphy."""
import json
import re
import time
import random
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps
import torch
from torch import nn

ROOT = Path(__file__).resolve().parent.parent

class CharacterCNN(nn.Module):
    def __init__(self, classes):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Conv2d(1, 16, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Flatten(),
            nn.Linear(64 * 8 * 8, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, classes)
        )

    def forward(self, x):
        return self.layers(x)

def pixels(path):
    with Image.open(path) as im:
        im = ImageOps.contain(im.convert('L'), (64, 64), Image.Resampling.BILINEAR)
        canvas = Image.new('L', (64, 64), 0)
        canvas.paste(im, ((64 - im.width) // 2, (64 - im.height) // 2))
        return np.array(canvas, dtype=np.float32)[None] / 255.0

def seed():
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(42)

def predict_gpu(model, x, device, batch_size=64):
    model.eval()
    preds = []
    with torch.inference_mode():
        for i in range(0, len(x), batch_size):
            batch = x[i:i + batch_size].to(device)
            out = model(batch)
            preds.append(out.argmax(1).cpu())
    return torch.cat(preds).numpy()

def fit_gpu(x, y, classes, epochs, device, dev=None):
    seed()
    model = CharacterCNN(classes).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=0.0001)
    dataset = torch.utils.data.TensorDataset(x, y)
    loader = torch.utils.data.DataLoader(dataset, batch_size=32, shuffle=True, pin_memory=(device.type == 'cuda'))

    logs = []
    for epoch in range(1, epochs + 1):
        epoch_start = time.perf_counter()
        model.train()
        loss_sum = 0.0

        for images, labels in loader:
            images = images.to(device, non_blocking=True)
            labels = labels.to(device, non_blocking=True)
            optimizer.zero_grad()
            out = model(images)
            loss = nn.functional.cross_entropy(out, labels)
            if not torch.isfinite(loss):
                raise ValueError('Non-finite training loss')
            loss.backward()
            optimizer.step()
            loss_sum += loss.item() * len(labels)

        epoch_time = time.perf_counter() - epoch_start
        row = {
            'epoch': epoch,
            'train_loss': round(loss_sum / len(y), 4),
            'epoch_seconds': round(epoch_time, 3)
        }
        if dev is not None:
            dev_pred = predict_gpu(model, dev[0], device)
            row['dev_correct'] = int((dev_pred == dev[1]).sum())
        logs.append(row)
        if epoch % 5 == 0 or epoch == 1 or epoch == epochs:
            print(json.dumps(row), flush=True)

    return model, logs

def main():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print("=" * 60)
    print(f"Device target: {device}")
    if device.type == 'cuda':
        print(f"GPU Name: {torch.cuda.get_device_name(0)}")
        print(f"VRAM Total: {torch.cuda.get_device_properties(0).total_memory / (1024**2):.1f} MB")
        torch.backends.cudnn.benchmark = True
    print("=" * 60, flush=True)

    start_total = time.perf_counter()
    out = ROOT / 'outputs/cnn_study'
    out.mkdir(exist_ok=True)

    rows = json.loads((ROOT / 'work/hero_pilot/manifest.json').read_text(encoding='utf-8'))
    site = lambda r: re.split(r'\d', r['source_name'], maxsplit=1)[0].strip().lower()
    protocol = json.loads((ROOT / 'outputs/matched_mask_study/summary.json').read_text())

    train = [r for r in rows if r['source_split'] == 'train' and site(r) not in protocol['excluded_validation_sites']]
    val = [r for r in rows if r['source_split'] == 'val']
    devsites = set(protocol['development_sites'])

    classes = sorted({r['label'] for r in train})
    index = {c: i for i, c in enumerate(classes)}

    print(f"Loading {len(train)} training crops and {len(val)} validation crops...", flush=True)
    x = torch.from_numpy(np.stack([pixels(ROOT / 'outputs/full_binarizer' / r['crop_path']) for r in train]))
    y = torch.tensor([index[r['label']] for r in train])

    dev = np.array([site(r) in devsites for r in train])
    assert dev.sum() == 308 and len(train) == 949

    print("Phase 1: Training development model (641 fit, 308 dev) for 30 epochs on GPU...", flush=True)
    t0 = time.perf_counter()
    model, logs = fit_gpu(x[~dev], y[~dev], len(classes), 30, device, (x[dev], y[dev].numpy()))
    phase1_time = time.perf_counter() - t0
    best = max(logs, key=lambda r: r['dev_correct'])
    epochs = best['epoch']
    print(f"Development best correct: {best['dev_correct']}/308 at epoch {epochs} (took {phase1_time:.2f}s)", flush=True)

    print(f"Phase 2: Refitting all {len(train)} training crops on GPU for {epochs} epochs...", flush=True)
    t1 = time.perf_counter()
    model, refit = fit_gpu(x, y, len(classes), epochs, device)
    phase2_time = time.perf_counter() - t1

    v = torch.from_numpy(np.stack([pixels(ROOT / 'outputs/full_binarizer' / r['crop_path']) for r in val]))
    pred = predict_gpu(model, v, device)
    truth = [r['label'] for r in val]
    labels = [classes[i] for i in pred]

    val_correct = sum(a == b for a, b in zip(truth, labels))
    val_acc = val_correct / len(val)

    peak_vram_mb = 0.0
    if device.type == 'cuda':
        peak_vram_mb = torch.cuda.max_memory_allocated() / (1024**2)

    total_time = time.perf_counter() - start_total

    checkpoint = out / 'character_cnn_gpu.pth'
    torch.save({
        'state_dict': model.state_dict(),
        'classes': classes,
        'input': 'predicted_mask_64_letterbox',
        'device': str(device),
        'val_accuracy': val_acc
    }, checkpoint)

    summary = {
        'model': 'CharacterCNN (GPU accelerated)',
        'device': str(device),
        'gpu_name': torch.cuda.get_device_name(0) if device.type == 'cuda' else 'N/A',
        'peak_vram_mb': round(peak_vram_mb, 2),
        'training_n': len(train),
        'classes': len(classes),
        'development_n': int(dev.sum()),
        'development_best_correct': best['dev_correct'],
        'selected_epochs': epochs,
        'validation_correct': val_correct,
        'validation_n': len(val),
        'validation_accuracy': val_acc,
        'phase1_seconds': round(phase1_time, 2),
        'phase2_seconds': round(phase2_time, 2),
        'total_seconds': round(total_time, 2)
    }

    (out / 'summary_gpu.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print("=" * 60)
    print("TRAINING RUN COMPLETE:")
    print(json.dumps(summary, indent=2))
    print("=" * 60, flush=True)

if __name__ == '__main__':
    main()

