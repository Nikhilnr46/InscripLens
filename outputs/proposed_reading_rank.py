"""Rank a proposed Kannada or Roman reading against all classifier labels."""
import unicodedata
from kannada_converter import to_kannada


def reading_rank(reading, labels):
    proposed = unicodedata.normalize("NFC", reading.strip())
    converted = to_kannada(proposed)
    target = unicodedata.normalize("NFC", converted or proposed)
    for i,label in enumerate(labels,1):
        text = unicodedata.normalize("NFC", to_kannada(label) or label)
        if text == target:
            return dict(reading=reading, normalized_reading=target, rank=i,
                        matched_label=label, total_labels=len(labels), status="ranked")
    return dict(reading=reading, normalized_reading=target, rank=None,
                matched_label=None, total_labels=len(labels), status="absent_from_vocabulary")
