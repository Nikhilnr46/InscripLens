with open("outputs/eval/verify_kannada_regression.py", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace(
    'assert exp_latest["suggested_label_kannada"] == "\\u0c95\\u0cca"  # \u0c95\u0cca',
    'assert exp_latest["suggested_label_kannada"] == "\\u0c95\\u0ccb"  # \u0c95\u0ccb (ko is long o)'
)
text = text.replace(
    'assert hist_rev["suggested_label_kannada"] == "\\u0c95\\u0cca"',
    'assert hist_rev["suggested_label_kannada"] == "\\u0c95\\u0ccb"  # \u0c95\u0ccb (ko is long o)'
)

with open("outputs/eval/verify_kannada_regression.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Updated test expectations")

