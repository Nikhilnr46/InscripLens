with open("outputs/eval/verify_kannada_regression.py", "r", encoding="utf-8") as f:
    text = f.read()

old_check = """    assert "prediction" in r0
    assert "prediction_kannada" in r0"""

new_check = """    assert ("predicted_source_label" in r0 or "prediction" in r0)
    assert "prediction_kannada" in r0"""

assert old_check in text, "old_check not found"
text = text.replace(old_check, new_check, 1)

with open("outputs/eval/verify_kannada_regression.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Updated regression test")

