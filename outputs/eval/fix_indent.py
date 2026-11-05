from pathlib import Path

p = Path("api/server.py")
lines = p.read_text(encoding="utf-8").splitlines()

fixed_lines = []
for i, line in enumerate(lines):
    if line == '        for reg in batch:':
        fixed_lines.append('    for reg in batch:')
    elif line == '        if isinstance(reg, dict) and "prediction" in reg:':
        fixed_lines.append('        if isinstance(reg, dict) and "prediction" in reg:')
    elif line == '            reg["prediction_kannada"] = to_kannada(reg["prediction"])':
        fixed_lines.append('            reg["prediction_kannada"] = to_kannada(reg["prediction"])')
    else:
        fixed_lines.append(line)

p.write_text("\n".join(fixed_lines), encoding="utf-8")
print("Fixed lines")

