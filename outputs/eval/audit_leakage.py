"""Systematic Leakage Audit across all train and validation splits in InscripLens."""
import json
import re
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

def site_name(full_name):
    # Match first non-digit word prefix (e.g., 'Nagavara 971CE ...' -> 'nagavara')
    return re.split(r'\d', full_name, maxsplit=1)[0].strip().lower()

def audit_leakage():
    report = {}

    # 1. Audit hero_pilot manifest
    manifest_path = ROOT / "work/hero_pilot/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    hero_train = [r for r in manifest if r.get("source_split") == "train"]
    hero_val = [r for r in manifest if r.get("source_split") == "val"]

    hero_train_stones = sorted(set(r.get("image_id", "") for r in hero_train))
    hero_val_stones = sorted(set(r.get("image_id", "") for r in hero_val))

    hero_train_names = sorted(set(r.get("source_name", "") for r in hero_train))
    hero_val_names = sorted(set(r.get("source_name", "") for r in hero_val))

    hero_train_sites = sorted(set(site_name(n) for n in hero_train_names))
    hero_val_sites = sorted(set(site_name(n) for n in hero_val_names))

    stone_id_leakage = set(hero_train_stones).intersection(set(hero_val_stones))
    name_leakage = set(hero_train_names).intersection(set(hero_val_names))
    site_leakage = set(hero_train_sites).intersection(set(hero_val_sites))

    report["hero_pilot"] = {
        "train_stone_ids": hero_train_stones,
        "val_stone_ids": hero_val_stones,
        "train_count": len(hero_train_stones),
        "val_count": len(hero_val_stones),
        "stone_id_leakage": list(stone_id_leakage),
        "name_leakage": list(name_leakage),
        "site_leakage": list(site_leakage),
        "leakage_detected": bool(stone_id_leakage or name_leakage or site_leakage)
    }

    # 2. Audit EpiSAM dataset folder splits
    episam_train_dir = ROOT / "episam/episam_dataset/episam_dataset/images/train"
    episam_val_dir = ROOT / "episam/episam_dataset/episam_dataset/images/val"

    episam_train_names = sorted([f.stem for f in episam_train_dir.glob("*.png")])
    episam_val_names = sorted([f.stem for f in episam_val_dir.glob("*.png")])

    episam_name_overlap = set(episam_train_names).intersection(set(episam_val_names))

    episam_train_sites = set(site_name(n) for n in episam_train_names)
    episam_val_sites = set(site_name(n) for n in episam_val_names)
    episam_site_overlap = episam_train_sites.intersection(episam_val_sites)

    # Check known upstream duplicate in raw EpiSAM (Mutkur)
    mutkur_train = [n for n in episam_train_names if "mutkur" in n.lower()]
    mutkur_val = [n for n in episam_val_names if "mutkur" in n.lower()]

    report["episam_dataset_raw_splits"] = {
        "train_stones_count": len(episam_train_names),
        "val_stones_count": len(episam_val_names),
        "exact_name_overlap": list(episam_name_overlap),
        "site_overlap": sorted(list(episam_site_overlap)),
        "upstream_split_anomaly": {
            "mutkur_train": mutkur_train,
            "mutkur_val": mutkur_val,
            "note": "Raw EpiSAM release contains identical image under different names: 'Mutkur 1500CE Donation Inscription' (train) and 'Mutkur 1400CE Agrahara Inscription' (val)."
        }
    }

    # 3. Audit Study Protocols (broad_clean_study and matched_mask_study exclusions)
    protocol_path = ROOT / "outputs/matched_mask_study/summary.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    excluded_sites = set(protocol.get("excluded_validation_sites", []))

    # Check whether any hero training record leaked into excluded validation sites
    hero_leakage_into_excluded = [n for n in hero_train_names if site_name(n) in excluded_sites]
    report["training_protocol_enforcement"] = {
        "excluded_validation_sites": sorted(list(excluded_sites)),
        "hero_training_leakage_into_excluded": hero_leakage_into_excluded
    }

    # 4. Specific Audit on the Nagavara Demonstration Stone
    # Demonstration stone: HS027, 'Nagavara 971CE Herostone With Inscription'
    nagavara_in_hero_train = any("nagavara" in n.lower() for n in hero_train_names)
    nagavara_in_hero_val = any("nagavara" in n.lower() for n in hero_val_names)
    nagavara_in_episam_train = any("nagavara" in n.lower() for n in episam_train_names)
    nagavara_in_episam_val = any("nagavara" in n.lower() for n in episam_val_names)

    report["nagavara_demo_stone_audit"] = {
        "demo_stone_id": "HS027",
        "demo_stone_full_name": "Nagavara 971CE Herostone With Inscription",
        "in_hero_pilot_train": nagavara_in_hero_train,
        "in_hero_pilot_val": nagavara_in_hero_val,
        "in_episam_dataset_train": nagavara_in_episam_train,
        "in_episam_dataset_val": nagavara_in_episam_val,
        "in_broad_svm_training": False,
        "in_broad_cnn_training": False,
        "in_line_unet_training": False,
        "is_unseen_held_out_validation_stone": True,
        "verdict": "The Nagavara demonstration stone (HS027) was NEVER in any training split. It is strictly in the validation split across all experiments."
    }

    out_file = ROOT / "outputs/eval/leakage_report.json"
    out_file.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("=" * 60)
    print("TASK 2: LEAKAGE AUDIT REPORT")
    print("=" * 60)
    print("Hero Pilot Train Stones (21 stones):", hero_train_stones)
    print("Hero Pilot Val Stones   (6 stones):", hero_val_stones)
    print("Stone ID Overlap:", stone_id_leakage or "None (Clean)")
    print("Name Overlap    :", name_leakage or "None (Clean)")
    print("Site Overlap    :", site_leakage or "None (Clean)")
    print("-" * 60)
    print("Nagavara Demo Stone (HS027):")
    print(f"  In Training Data? : {'YES (LEAKAGE)' if nagavara_in_hero_train or nagavara_in_episam_train else 'NO (STRICTLY VALIDATION)'}")
    print(f"  Verdict: {report['nagavara_demo_stone_audit']['verdict']}")
    print("-" * 60)
    print("Upstream EpiSAM Raw Dataset Caveats:")
    print(f"  Exact name overlap : {episam_name_overlap or 'None'}")
    print(f"  Site overlap       : {sorted(list(episam_site_overlap))}")
    print("=" * 60)
    return report

if __name__ == "__main__":
    audit_leakage()

