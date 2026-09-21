#!/usr/bin/env python3
"""Apply train_crowd.py output to the runtime crowd_model.json.

train_crowd.py deliberately fits only factors supported by the visitor dataset:
weekday, month, and holiday effects. This script copies those fitted values into
the app-facing model without touching hour curves or per-mountain parameters.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIT = ROOT / "data" / "v1" / "crowd_fit.json"
MODEL = ROOT / "data" / "v1" / "crowd_model.json"
RAW = ROOT / "data" / "raw" / "seoraksan_visitors.csv"


def trained_through() -> str | None:
    if not RAW.exists():
        return None
    rows = csv.DictReader(RAW.read_text(encoding="utf-8-sig").splitlines())
    dates = [r.get("일자", "") for r in rows if r.get("일자")]
    return max(dates) if dates else None


def main() -> int:
    fit = json.loads(FIT.read_text(encoding="utf-8"))
    model = json.loads(MODEL.read_text(encoding="utf-8"))

    patch = {
        "dowFactors": fit["dow"],
        "holidayFactor": fit["holidayFactor"],
        "autumnLeaf": fit["month"],
        "trainedThrough": trained_through(),
        "validation": {
            "mape": fit["holdoutMedianAPE"],
            "holdoutParks": ["설악산"],
        },
    }

    changed = False
    if model.get("dowFactors") != patch["dowFactors"]:
        model["dowFactors"] = patch["dowFactors"]
        changed = True
    if model.get("holidayFactor") != patch["holidayFactor"]:
        model["holidayFactor"] = patch["holidayFactor"]
        changed = True
    if model.setdefault("monthProfiles", {}).get("autumnLeaf") != patch["autumnLeaf"]:
        model["monthProfiles"]["autumnLeaf"] = patch["autumnLeaf"]
        changed = True
    if patch["trainedThrough"] and model.get("trainedThrough") != patch["trainedThrough"]:
        model["trainedThrough"] = patch["trainedThrough"]
        changed = True
    if model.get("validation") != patch["validation"]:
        model["validation"] = patch["validation"]
        changed = True

    if not changed:
        print("crowd runtime model: fitted values unchanged")
        return 0

    model["generatedAt"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    MODEL.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "crowd runtime model updated: "
        f"trainedThrough={model.get('trainedThrough')} "
        f"mape={model['validation']['mape']:.1%}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
