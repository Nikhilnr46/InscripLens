"""GPU-accelerated training of Historical Kannada Language Model (KittelLM) on Ferdinand Kittel's Dictionary (1894)."""
import json
import time
import math
import random
from pathlib import Path
import numpy as np
import torch
from torch import nn

ROOT = Path(__file__).resolve().parent.parent

class KittelLM(nn.Module):
    def __init__(self, vocab_size, embed_dim=128, hidden_dim=256, num_layers=2, dropout=0.2):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.lstm = nn.LSTM(
            embed_dim, hidden_dim, num_layers=num_layers,
            dropout=dropout, batch_first=True
        )
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim, vocab_size)

    def forward(self, x, hidden=None):
        embeds = self.dropout(self.embedding(x))
        out, hidden = self.lstm(embeds, hidden)
        out = self.dropout(out)
        logits = self.fc(out)
        return logits, hidden

def build_dataset(text, char_to_idx, seq_length=64, step=32):
    encoded = np.array([char_to_idx[c] for c in text if c in char_to_idx], dtype=np.int64)
    num_sequences = (len(encoded) - seq_length - 1) // step
    inputs = np.zeros((num_sequences, seq_length), dtype=np.int64)
    targets = np.zeros((num_sequences, seq_length), dtype=np.int64)

    for i in range(num_sequences):
        start = i * step
        inputs[i] = encoded[start:start + seq_length]
        targets[i] = encoded[start + 1:start + seq_length + 1]

    return inputs, targets

def evaluate_lm(model, data_loader, criterion, device):
    model.eval()
    total_loss = 0.0
    total_tokens = 0
    correct = 0

    with torch.inference_mode():
        for bx, by in data_loader:
            bx = bx.to(device)
            by = by.to(device)
            logits, _ = model(bx)
            loss = criterion(logits.view(-1, logits.size(-1)), by.view(-1))
            total_loss += loss.item() * by.numel()
            total_tokens += by.numel()
            preds = logits.argmax(dim=-1)
            correct += (preds == by).sum().item()

    avg_loss = total_loss / max(1, total_tokens)
    ppl = math.exp(min(15.0, avg_loss))
    acc = correct / max(1, total_tokens)
    return avg_loss, ppl, acc

def generate_sample(model, prompt, char_to_idx, idx_to_char, device, max_chars=40):
    model.eval()
    encoded = [char_to_idx[c] for c in prompt if c in char_to_idx]
    if not encoded:
        encoded = [0]
    input_seq = torch.tensor([encoded], dtype=torch.long, device=device)

    generated = list(prompt)
    with torch.inference_mode():
        logits, hidden = model(input_seq)
        last_token = logits[:, -1, :].argmax(dim=-1).item()
        generated.append(idx_to_char.get(last_token, ''))

        curr_token = torch.tensor([[last_token]], dtype=torch.long, device=device)
        for _ in range(max_chars - 1):
            logits, hidden = model(curr_token, hidden)
            probs = torch.softmax(logits[:, -1, :], dim=-1)
            # Greedy argmax
            next_char_idx = probs.argmax(dim=-1).item()
            char = idx_to_char.get(next_char_idx, '')
            generated.append(char)
            curr_token = torch.tensor([[next_char_idx]], dtype=torch.long, device=device)
            if char in ('\n', '.'):
                break

    return "".join(generated)

def main():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print("=" * 60)
    print("TRAINING KITTEL HISTORICAL KANNADA LANGUAGE MODEL (GPU)")
    print(f"Device target: {device}")
    if device.type == 'cuda':
        print(f"GPU Name: {torch.cuda.get_device_name(0)}")
        print(f"VRAM Total: {torch.cuda.get_device_properties(0).total_memory / (1024**2):.1f} MB")
        torch.backends.cudnn.benchmark = True
    print("=" * 60, flush=True)

    start_total = time.perf_counter()
    corpus_path = ROOT / 'scratch/kittel_corpus_sample.txt'
    out = ROOT / 'outputs/dictionary_study'
    out.mkdir(exist_ok=True)

    raw_text = corpus_path.read_text(encoding='utf-8')
    print(f"Loaded Kittel dictionary corpus: {len(raw_text):,} characters", flush=True)

    # Build character vocabulary
    chars = sorted(set(raw_text))
    vocab_size = len(chars)
    char_to_idx = {c: i for i, c in enumerate(chars)}
    idx_to_char = {i: c for i, c in enumerate(chars)}
    print(f"Unique vocabulary characters: {vocab_size}", flush=True)

    # 90% train, 10% validation
    split_point = int(len(raw_text) * 0.9)
    train_text = raw_text[:split_point]
    val_text = raw_text[split_point:]

    seq_length = 64
    step = 32
    print(f"Building sequence datasets (length {seq_length}, step {step})...", flush=True)
    x_train, y_train = build_dataset(train_text, char_to_idx, seq_length, step)
    x_val, y_val = build_dataset(val_text, char_to_idx, seq_length, step * 2)
    print(f"Train sequences: {len(x_train):,}, Val sequences: {len(x_val):,}", flush=True)

    train_dataset = torch.utils.data.TensorDataset(
        torch.from_numpy(x_train), torch.from_numpy(y_train)
    )
    val_dataset = torch.utils.data.TensorDataset(
        torch.from_numpy(x_val), torch.from_numpy(y_val)
    )

    batch_size = 128
    train_loader = torch.utils.data.DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True, pin_memory=(device.type == 'cuda'), drop_last=True
    )
    val_loader = torch.utils.data.DataLoader(
        val_dataset, batch_size=batch_size, shuffle=False, pin_memory=(device.type == 'cuda')
    )

    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    if device.type == 'cuda':
        torch.cuda.manual_seed_all(42)

    model = KittelLM(vocab_size=vocab_size, embed_dim=128, hidden_dim=256, num_layers=2, dropout=0.2).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.002, weight_decay=1e-4)
    criterion = nn.CrossEntropyLoss()
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=15)

    epochs = 15
    print(f"Training KittelLM for {epochs} epochs on GPU...", flush=True)
    logs = []
    best_val_loss = float('inf')

    for epoch in range(1, epochs + 1):
        ep_start = time.perf_counter()
        model.train()
        train_loss = 0.0
        train_tokens = 0

        for bx, by in train_loader:
            bx = bx.to(device, non_blocking=True)
            by = by.to(device, non_blocking=True)
            optimizer.zero_grad()
            logits, _ = model(bx)
            loss = criterion(logits.view(-1, vocab_size), by.view(-1))
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=2.0)
            optimizer.step()
            train_loss += loss.item() * by.numel()
            train_tokens += by.numel()

        scheduler.step()
        train_loss /= train_tokens
        ep_seconds = time.perf_counter() - ep_start

        # Evaluate validation set
        val_loss, val_ppl, val_acc = evaluate_lm(model, val_loader, criterion, device)
        row = {
            'epoch': epoch,
            'train_loss': round(train_loss, 4),
            'val_loss': round(val_loss, 4),
            'val_perplexity': round(val_ppl, 2),
            'val_char_accuracy': round(val_acc, 4),
            'epoch_seconds': round(ep_seconds, 2)
        }
        logs.append(row)
        print(f"Epoch {epoch:2d}/{epochs} - Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Val PPL: {val_ppl:.2f} | Val Acc: {val_acc*100:.1f}% | Time: {ep_seconds:.2f}s", flush=True)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save({
                'state_dict': model.state_dict(),
                'vocab_size': vocab_size,
                'char_to_idx': char_to_idx,
                'idx_to_char': idx_to_char,
                'embed_dim': 128,
                'hidden_dim': 256,
                'num_layers': 2,
                'val_loss': val_loss,
                'val_perplexity': val_ppl,
                'val_char_accuracy': val_acc
            }, out / 'kittel_lm_gpu.pth')

    # Test sample generation
    sample_prompt = "svasti sri"
    sample_gen = generate_sample(model, sample_prompt, char_to_idx, idx_to_char, device)
    print("\n--- SAMPLE NEURAL CONTINUATION ---")
    print(f"Prompt: '{sample_prompt}' -> Generated: '{sample_gen}'")

    peak_vram_mb = 0.0
    if device.type == 'cuda':
        peak_vram_mb = torch.cuda.max_memory_allocated() / (1024**2)

    total_time = time.perf_counter() - start_total
    summary = {
        'model': 'Historical Kannada KittelLM (GPU accelerated)',
        'source_text': "Rev. F. Kittel's A Kannada-English Dictionary (1894)",
        'corpus_characters': len(raw_text),
        'vocab_size': vocab_size,
        'train_sequences': len(x_train),
        'val_sequences': len(x_val),
        'sequence_length': seq_length,
        'device': str(device),
        'gpu_name': torch.cuda.get_device_name(0) if device.type == 'cuda' else 'CPU',
        'peak_vram_mb': round(peak_vram_mb, 2),
        'best_val_loss': round(best_val_loss, 4),
        'best_val_perplexity': round(logs[np.argmin([r['val_loss'] for r in logs])]['val_perplexity'], 2),
        'best_val_char_accuracy': round(logs[np.argmin([r['val_loss'] for r in logs])]['val_char_accuracy'], 4),
        'epochs': epochs,
        'total_training_seconds': round(total_time, 2),
        'checkpoint_path': str(out / 'kittel_lm_gpu.pth')
    }

    (out / 'summary_dictionary_gpu.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print("=" * 60)
    print("KITTEL DICTIONARY LANGUAGE MODEL TRAINING COMPLETE:")
    print(json.dumps(summary, indent=2))
    print("=" * 60, flush=True)

if __name__ == '__main__':
    main()

