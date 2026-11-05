"""GPU-accelerated and multi-scale inference for the attributed Shilalekhya checkpoint (Jena et al., ICVGIP 2025)."""
from pathlib import Path
import sys, argparse, json, time
import numpy as np
from PIL import Image, ImageOps
import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'work/shilalekhya'))
from Unet.model import AttentionUNet

def load_model(device=None):
    if device is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    device = torch.device(device)
    if device.type == 'cpu':
        torch.set_num_threads(4)
    elif device.type == 'cuda':
        torch.backends.cudnn.benchmark = True
    model = AttentionUNet(3, 1, bilinear=False)
    weights = torch.load(ROOT / 'work/shilalekhya/binarizer.pth', map_location='cpu', weights_only=True)
    model.load_state_dict(weights, strict=True)
    return model.to(device).eval()

def enhance(image, model):
    device = next(model.parameters()).device
    image = ImageOps.exif_transpose(image).convert('RGB')
    a = np.array(image)
    h, w = a.shape[:2]
    padded = np.pad(a, ((0, max(0, 512 - h)), (0, max(0, 512 - w)), (0, 0)), mode='edge')
    ph, pw = padded.shape[:2]
    def positions(n):
        return sorted(set(list(range(0, n - 512 + 1, 448)) + [n - 512]))
    total = np.zeros((ph, pw), np.float32)
    count = np.zeros((ph, pw), np.uint16)
    for y in positions(ph):
        for x in positions(pw):
            t = torch.from_numpy(padded[y:y + 512, x:x + 512].copy()).permute(2, 0, 1).float().unsqueeze(0) / 255.0
            with torch.inference_mode():
                p = torch.sigmoid(model(t.to(device)))[0, 0].cpu().numpy()
            if not np.isfinite(p).all():
                raise ValueError('Non-finite model output')
            total[y:y + 512, x:x + 512] += p
            count[y:y + 512, x:x + 512] += 1
    assert count.min() > 0
    return Image.fromarray(((total / count)[:h, :w] > 0.5).astype('uint8') * 255)

def enhance_multiscale(image, model, scales=(256, 384, 512)):
    """Multi-scale sliding window prediction with max-probability fusion (Paper 5, Algorithm 1)."""
    device = next(model.parameters()).device
    image = ImageOps.exif_transpose(image).convert('RGB')
    a = np.array(image)
    h, w = a.shape[:2]
    max_probs = np.zeros((h, w), dtype=np.float32)

    for s in scales:
        stride = max(64, int(s * 0.8))
        padded = np.pad(a, ((0, max(0, s - h)), (0, max(0, s - w)), (0, 0)), mode='edge')
        ph, pw = padded.shape[:2]

        def positions(n, sz, st):
            if n <= sz:
                return [0]
            return sorted(set(list(range(0, n - sz + 1, st)) + [n - sz]))

        prob_scale = np.zeros((ph, pw), dtype=np.float32)
        count_scale = np.zeros((ph, pw), dtype=np.uint16)

        for y in positions(ph, s, stride):
            for x in positions(pw, s, stride):
                crop = padded[y:y + s, x:x + s]
                crop_pil = Image.fromarray(crop).resize((512, 512), Image.Resampling.BILINEAR)
                t = torch.from_numpy(np.array(crop_pil)).permute(2, 0, 1).float().unsqueeze(0) / 255.0
                with torch.inference_mode():
                    p = torch.sigmoid(model(t.to(device)))[0, 0].cpu().numpy()
                p_resized = np.array(Image.fromarray(p).resize((s, s), Image.Resampling.BILINEAR))
                prob_scale[y:y + s, x:x + s] += p_resized
                count_scale[y:y + s, x:x + s] += 1

        merged = (prob_scale / np.maximum(count_scale, 1))[:h, :w]
        max_probs = np.maximum(max_probs, merged)

    return Image.fromarray((max_probs > 0.5).astype('uint8') * 255)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--device', type=str, default=None)
    parser.add_argument('--multiscale', action='store_true', help='Use multi-scale sliding window (Paper 5)')
    args = parser.parse_args()

    model = load_model(args.device)
    start = time.perf_counter()
    with Image.open(args.input) as im:
        if args.multiscale:
            result = enhance_multiscale(im, model)
            method = 'multiscale_context_aware_binarization_paper5'
        else:
            result = enhance(im, model)
            method = 'single_scale_pretrained_binarization'
    elapsed = time.perf_counter() - start

    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.save(args.output)
    device_str = str(next(model.parameters()).device)
    print(json.dumps({
        'seconds': round(elapsed, 4),
        'size': result.size,
        'method': method,
        'device': device_str
    }))
