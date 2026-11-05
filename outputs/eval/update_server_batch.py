with open("api/server.py", "r", encoding="utf-8") as f:
    text = f.read()

old_b = """    for reg in batch:
        if isinstance(reg, dict) and "prediction" in reg:
            reg["prediction_kannada"] = to_kannada(reg["prediction"])"""

new_b = """    for reg in batch:
        if isinstance(reg, dict):
            p = reg.get("predicted_source_label") or reg.get("prediction")
            if p:
                reg["prediction_kannada"] = to_kannada(p)"""

assert old_b in text, "old_b not found"
text = text.replace(old_b, new_b, 1)

with open("api/server.py", "w", encoding="utf-8", newline="\r\n") as f:
    f.write(text)

print("Updated server.py batch regions handling")

