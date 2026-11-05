from pathlib import Path

server_path = Path("api/server.py")
text = server_path.read_text(encoding="utf-8")

# 1. Add import
imp_target = "from translation_core import analyze_inscription_text"
imp_addition = "\nfrom kannada_converter import to_kannada"
if imp_addition not in text:
    assert imp_target in text, "imp_target not found"
    text = text.replace(imp_target, imp_target + imp_addition, 1)

# 2. Update run_recognize_all to add prediction_kannada to regions
rec_target = 'json_path.write_text(json.dumps(save_payload, ensure_ascii=False, indent=2), encoding="utf-8")'
rec_addition = """    for reg in batch:
        if isinstance(reg, dict) and "prediction" in reg:
            reg["prediction_kannada"] = to_kannada(reg["prediction"])
    """
if "prediction_kannada" not in text[:text.find(rec_target)]:
    assert rec_target in text, "rec_target not found"
    text = text.replace(rec_target, rec_addition + rec_target, 1)

# 3. Update run_predict_crop to add prediction_kannada
pred_target = '"prediction": pred,'
pred_replacement = '"prediction": pred,\n        "prediction_kannada": to_kannada(pred) if pred else None,'
if '"prediction_kannada": to_kannada(pred)' not in text:
    assert pred_target in text, "pred_target not found"
    text = text.replace(pred_target, pred_replacement, 1)

# 4. Update get_analysis_history to attach reviews and review_count
hist_target = """            if details.get("fallback_note"):
                item["fallback_note"] = details["fallback_note"]
            sanitized.append(item)"""

hist_replacement = """            if details.get("fallback_note"):
                item["fallback_note"] = details["fallback_note"]

            try:
                with sqlite3.connect(DATA_DIR / "history.sqlite3") as con:
                    cur = con.cursor()
                    cur.execute("SELECT prediction, suggested_label, reviewer, created FROM character_reviews WHERE run_id = ? ORDER BY created", (r["id"],))
                    rev_rows = cur.fetchall()
                run_reviews = []
                for p_rom, s_rom, rev, ts in rev_rows:
                    run_reviews.append({
                        "prediction": p_rom,
                        "prediction_kannada": to_kannada(p_rom) if p_rom else None,
                        "suggested_label": s_rom,
                        "suggested_label_kannada": to_kannada(s_rom) if s_rom else None,
                        "reviewer": rev,
                        "created": ts
                    })
                item["reviews"] = run_reviews
                item["review_count"] = len(run_reviews)
            except Exception:
                item["reviews"] = []
                item["review_count"] = 0

            sanitized.append(item)"""

if "run_reviews" not in text:
    assert hist_target in text, "hist_target not found"
    text = text.replace(hist_target, hist_replacement, 1)

# 5. Update get_run_export to add prediction_kannada and suggested_label_kannada
exp_target = """        return data
    except ValueError:"""

exp_replacement = """        if "reviews" in data and isinstance(data["reviews"], list):
            for rev in data["reviews"]:
                if isinstance(rev, dict):
                    p_rom = rev.get("prediction")
                    s_rom = rev.get("suggested_label")
                    rev["prediction_kannada"] = to_kannada(p_rom) if p_rom else None
                    rev["suggested_label_kannada"] = to_kannada(s_rom) if s_rom else None
        return data
    except ValueError:"""

if 'rev["prediction_kannada"] = to_kannada(p_rom)' not in text:
    assert exp_target in text, "exp_target not found"
    text = text.replace(exp_target, exp_replacement, 1)

server_path.write_text(text, encoding="utf-8")
print("Updated api/server.py successfully")

