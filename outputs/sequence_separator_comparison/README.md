# Separator comparison

Both runs used 124 screened training lines, the same mask crops, initialization, alphabet, minibatch order and ten epochs. Seven development lines from five other images contain 125 Roman reference codepoints after removing the inserted separators. Run `outputs/train_screened_sequences.py` first to generate baseline predictions, then run it with `--omit-separators` in the PyTorch environment.

Beam decoding yielded 125 edits with separator supervision and 116 with separators omitted. Six of seven candidate predictions were `a`, and the seventh was `aaaa`. Always returning one `a` costs 119 edits. The same-size zero-image control cost 125 edits. The output responds to image content, but offers little beyond the most frequent training letter. Both models recovered zero complete development lines. The experiment tests ten epochs and a small reused development set. No sequence model was deployed.

Next diagnostic: use the existing character boxes and labels to supervise the visual encoder on training images before sequence training. Evaluate on the same separated development sources and compare against a frequency-only baseline. This keeps the inscription corpus intact and tests whether the model can distinguish glyphs before learning line alignment.
