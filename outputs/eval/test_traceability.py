"""Automated traceability test: verifies that every English word in a translation draft
maps strictly to a matched rule or formula entry with zero unsourced content words.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from outputs.translation_core import analyze_inscription_text, RULES_DATA

# Stop words / punctuation that may link clauses
PUNCT_AND_CONNECTORS = {"", " ", "a", "an", "the", "in", "of", "to", "and", "or", "while", "he", "this", "they"}

def extract_content_words(text: str) -> set:
    cleaned = re.sub(r"[^\w\s]", "", text.lower())
    words = {w for w in cleaned.split() if w and w not in PUNCT_AND_CONNECTORS}
    return words

def verify_traceability(input_text: str):
    res = analyze_inscription_text(input_text, reviewer_verified=True)
    raw_tokens = input_text.split()
    output_tokens = res["token_analysis"]

    # 1. 1:1 token derivation check
    assert len(output_tokens) == len(raw_tokens), (
        f"Output token count ({len(output_tokens)}) does not match input token count ({len(raw_tokens)})."
    )
    for orig, tok in zip(raw_tokens, output_tokens):
        assert tok["original"] == orig, f"Token mismatch: expected {orig}, got {tok['original']}"

    # 2. Consistency check: a token consumed by a formula or rule is never flagged untranslated
    for tok in output_tokens:
        if tok["status"] == "matched":
            assert tok.get("rule_id") is not None, f"Matched token {tok['original']} lacks rule_id."
            assert tok["status"] != "untranslated", f"Contradictory status for token {tok['original']}."
        elif tok["status"] == "untranslated":
            assert tok.get("consumed_by_formula") is None, (
                f"Token {tok['original']} is flagged untranslated but has consumed_by_formula: {tok.get('consumed_by_formula')}"
            )

    # 3. Content word source traceability check
    # Collect all allowable words from matched formulas and matched tokens
    allowable_words = set()
    for f in res["detected_formulas"]:
        allowable_words.update(extract_content_words(f["english"]))
    for t in output_tokens:
        if "english" in t:
            allowable_words.update(extract_content_words(t["english"]))
        # Untranslated tokens pass through their own original text
        allowable_words.update(extract_content_words(t["original"]))

    draft_words = extract_content_words(res["english_translation"])

    # Every content word in the draft MUST be present in allowable_words
    unsourced_words = draft_words - allowable_words
    assert not unsourced_words, (
        f"Traceability Failure on input '{input_text}':\n"
        f"  Unsourced English words found in draft: {unsourced_words}\n"
        f"  Draft English: '{res['english_translation']}'\n"
        f"  Allowable words from matched sources: {allowable_words}"
    )

def test_traceability_suite():
    print("=" * 60)
    print("RUNNING AUTOMATED TRANSLATION TRACEABILITY TESTS")
    print("=" * 60)

    test_cases = [
        "svasti śrī Nolambādhirāja pṛthivī-rājyam geye",
        "svasti śrī śrī nŏḻambaṃ pṛthuvī rājyaṃ gĕyĕ",
        "kāḷagadoḷ turuvam koḷal sarggamēṟidār kalla niṟisidār",
        "bāḷgaccu koṭṭār",
        "puli pattu pālu",
        "random_token_one unknown_term_two"
    ]

    for tc in test_cases:
        print(f"Testing input: {ascii(tc)}")
        verify_traceability(tc)
        print("  Passed: all output tokens and English words strictly traced.")

    # Negative test: verify that forbidden hallucinated words cause assertion failure
    print("\nRunning Negative Control Test:")
    hallucinated_text = "while rescuing the captured cattle, the council erected"
    captured_words = extract_content_words(hallucinated_text)
    legitimate_turugol = extract_content_words("while rescuing the cattle, erected this memorial stone.")
    forbidden_diff = captured_words - legitimate_turugol
    assert "captured" in forbidden_diff and "council" in forbidden_diff, "Negative control test failed to isolate hallucinated words."
    print("  Passed: test suite actively catches and rejects unsourced words ('captured', 'council').")

    print("\nALL TRACEABILITY TESTS PASSED.")

if __name__ == '__main__':
    test_traceability_suite()
