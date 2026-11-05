"""Data-driven rule-based draft engine for formulaic Halegannada hero-stone inscriptions."""
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

ROOT = Path(__file__).resolve().parent.parent
RULES_PATH = ROOT / "outputs/translation_rules.json"

def load_translation_rules() -> Dict[str, Any]:
    if not RULES_PATH.exists():
        raise FileNotFoundError(f"Translation rules file missing: {RULES_PATH}")
    return json.loads(RULES_PATH.read_text(encoding="utf-8"))

RULES_DATA = load_translation_rules()

def normalize_spelling(s: str) -> str:
    """Normalize orthographic short/long vowels, anusvara, and spacing for invariant formula matching."""
    t = s.lower().strip(" ,.-:;")
    t = t.replace("ĕ", "e").replace("ŏ", "o")
    t = t.replace("ā", "a").replace("ī", "i").replace("ū", "u").replace("ē", "e").replace("ō", "o")
    t = t.replace("aṃ", "am").replace("ṃ", "m")
    t = re.sub(r"[\s\-_]+", " ", t)
    return t

def modernize_single_token(cleaned_token: str) -> Dict[str, Any]:
    """Modernize a single standalone token. Does not alter morphemes if unmatched."""
    norm_cleaned = normalize_spelling(cleaned_token)

    # 1. Single-token formula in lexicon
    for entry in RULES_DATA.get("formulaic_lexicon", []):
        keys = [entry["key"]] + entry.get("variants", [])
        for k in keys:
            if cleaned_token == k or norm_cleaned == normalize_spelling(k):
                prov = f"Formula entry '{entry['key']}'"
                if entry.get("provenance_status") == "confirmed from a repo file":
                    prov += f" ({entry['source']})"
                return {
                    "modern": entry["modern_kannada"],
                    "english": entry["english_translation"],
                    "category": entry["category"],
                    "rule_id": entry["id"],
                    "rule_provenance": prov,
                    "status": "matched"
                }

    # 2. Strict allowlist for initial p- to h- shift
    p_rule = next((r for r in RULES_DATA.get("phonological_rules", []) if r["id"] == "PHONO_P_TO_H_ALLOWLIST"), None)
    if p_rule and cleaned_token in p_rule.get("allowlist", {}):
        modern = p_rule["allowlist"][cleaned_token]
        return {
            "modern": modern,
            "rule_id": p_rule["id"],
            "rule_provenance": f"{p_rule['name']} (Native root allowlist)",
            "status": "matched"
        }

    # 3. Case endings with strict exceptions
    modern = cleaned_token
    for c_rule in RULES_DATA.get("case_markers", []):
        pat = c_rule["halegannada_pattern"]
        repl = c_rule["modern_replacement"]
        exceptions = [normalize_spelling(e) for e in c_rule.get("exceptions", [])]
        if norm_cleaned in exceptions:
            continue
        if re.search(pat, modern):
            modern = re.sub(pat, repl, modern)
            return {
                "modern": modern,
                "rule_id": c_rule["id"],
                "rule_provenance": f"{c_rule['case_name']} (Pattern match)",
                "status": "matched"
            }

    # 4. Verb endings with strict exceptions
    for v_rule in RULES_DATA.get("verb_markers", []):
        pat = v_rule["halegannada_pattern"]
        repl = v_rule["modern_replacement"]
        exceptions = [normalize_spelling(e) for e in v_rule.get("exceptions", [])]
        if norm_cleaned in exceptions:
            continue
        if re.search(pat, modern):
            modern = re.sub(pat, repl, modern)
            return {
                "modern": modern,
                "rule_id": v_rule["id"],
                "rule_provenance": f"{v_rule['category']} (Pattern match)",
                "status": "matched"
            }

    # 5. Archaic retroflex mergers (only if already part of an identified root or loanword)
    # Passed through unchanged if not matched by any grammatical or lexical rule
    return {
        "modern": cleaned_token,
        "rule_id": None,
        "rule_provenance": "Unmatched; passed through verbatim",
        "status": "untranslated"
    }

def analyze_inscription_text(text: str, reviewer_verified: bool = True) -> Dict[str, Any]:
    """Execute data-driven translation draft on an inscription passage.
    Tokens consumed by a formula are consistently linked; untranslated tokens are returned verbatim.
    """
    raw_tokens = [t.strip() for t in text.split() if t.strip()]
    if not raw_tokens:
        return {
            "status": "Machine draft, unverified",
            "source_text": text,
            "modern_kannada_transcription": "",
            "english_translation": "",
            "detected_formulas": [],
            "token_analysis": [],
            "rule_provenance": [],
            "limitations": "Rule-based draft for formulaic hero-stone passages; not a general translation."
        }

    cleaned_tokens = [t.lower().strip(" ,.-:;") for t in raw_tokens]
    num_tokens = len(cleaned_tokens)
    token_status = [None] * num_tokens

    # Formula matching with token span consumption
    detected_formulas = []
    rule_provenance = []

    # Sort formulas by token count descending so longer phrases consume tokens first
    sorted_formulas = sorted(
        RULES_DATA.get("formulaic_lexicon", []),
        key=lambda e: -len(e["key"].split())
    )

    for entry in sorted_formulas:
        keys = [entry["key"]] + entry.get("variants", [])
        for k in keys:
            k_tokens = [normalize_spelling(w) for w in k.split() if w.strip()]
            k_len = len(k_tokens)
            if k_len == 0:
                continue

            # Slide window across cleaned_tokens
            for start_idx in range(num_tokens - k_len + 1):
                # Check if all tokens in window are unconsumed
                if any(token_status[i] is not None for i in range(start_idx, start_idx + k_len)):
                    continue

                window_tokens = [normalize_spelling(cleaned_tokens[i]) for i in range(start_idx, start_idx + k_len)]
                if window_tokens == k_tokens:
                    # Match found! Consume tokens
                    prov = f"Formula template '{entry['key']}' matched span '{k}'"
                    if entry.get("provenance_status") == "confirmed from a repo file":
                        prov += f" ({entry['source']})"
                    else:
                        prov += " (Unverified source - pending citation)"

                    detected_formulas.append({
                        "start_token_idx": start_idx,
                        "token_span": [start_idx, start_idx + k_len],
                        "formula_id": entry["id"],
                        "formula_key": entry["key"],
                        "matched_variant": k,
                        "category": entry["category"],
                        "modern_kannada": entry["modern_kannada"],
                        "english": entry["english_translation"],
                        "provenance_status": entry.get("provenance_status", "unverified"),
                        "rule_provenance": prov
                    })
                    rule_provenance.append(prov)

                    # Mark each token in span as consumed by formula
                    for i in range(start_idx, start_idx + k_len):
                        token_status[i] = {
                            "original": raw_tokens[i],
                            "modern": entry["modern_kannada"],
                            "english": entry["english_translation"],
                            "category": entry["category"],
                            "rule_id": entry["id"],
                            "rule_provenance": prov,
                            "consumed_by_formula": entry["key"],
                            "status": "matched"
                        }
                    break

    # Process remaining unconsumed tokens individually
    token_results = []
    for i in range(num_tokens):
        if token_status[i] is not None:
            token_results.append(token_status[i])
        else:
            tok = cleaned_tokens[i]
            res = modernize_single_token(tok)
            rec = {
                "original": raw_tokens[i],
                "modern": res["modern"],
                "rule_id": res.get("rule_id"),
                "rule_provenance": res["rule_provenance"],
                "status": res["status"]
            }
            if "english" in res:
                rec["english"] = res["english"]
            if res["status"] == "matched" and res.get("rule_provenance"):
                rule_provenance.append(f"Token '{raw_tokens[i]}': {res['rule_provenance']}")
            token_results.append(rec)

    # Order detected formulas by start position in inscription
    detected_formulas.sort(key=lambda x: x["start_token_idx"])
    for f in detected_formulas:
        del f["start_token_idx"]

    # Assemble English draft: strictly mapping formula spans and matched tokens
    english_clauses = [f["english"] for f in detected_formulas]
    if english_clauses:
        english_translation = " ".join(english_clauses)
    else:
        # Pass through matched word glosses or untranslated token verbatim
        parts = [t.get("english", t["original"]) for t in token_results]
        english_translation = " ".join(parts)

    modern_sentence = " ".join(t["modern"] for t in token_results)

    return {
        "status": "Machine draft, unverified",
        "source_text": text,
        "reviewer_verified": reviewer_verified,
        "modern_kannada_transcription": modern_sentence,
        "english_translation": english_translation,
        "detected_formulas": detected_formulas,
        "token_analysis": token_results,
        "rule_provenance": rule_provenance,
        "limitations": "Rule-based draft for formulaic hero-stone passages; not a general translation."
    }
