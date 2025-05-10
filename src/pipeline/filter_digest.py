#!/usr/bin/env python3
"""
filter_digest.py – select rows that meet R² and |a|,|b| thresholds.

Reads  : data/features/<ALG_TAG>/<PAIR>/window_<W>/week_YYYY-MM-DD.csv
Writes : data/digest/<ALG_TAG>/<PAIR>/window_<W>/week_YYYY-MM-DD.csv
"""
import argparse, csv
from utils import path_utils, config
from pathlib import Path

WINDOWS  = config.getlist("pipeline", "windows", int)
ALG_TAG  = config.get("pipeline", "quadratic_alg_tag")
PL_TAG   = config.get("pipeline", "pl_tag")

# Thresholds
R2_THR   = config.get("digest", "r2_threshold", float)
A_MIN    = config.get("digest", "min_abs_a", float)
A_MAX    = config.get("digest", "max_abs_a", float)
B_MIN    = config.get("digest", "min_abs_b", float)
B_MAX    = config.get("digest", "max_abs_b", float)


def weekly_dates(pair: str, window: int, limit: int | None):
    feats = sorted(path_utils.features_dir(pair, window, ALG_TAG).glob("week_*.csv"))
    if limit:
        feats = feats[-limit:]
    return [p.stem.split("_")[1] for p in feats]


def row_ok(r2: float, a: float, b: float) -> bool:
    return (
        r2 >= R2_THR and
        A_MIN <= abs(a) <= A_MAX and
        B_MIN <= abs(b) <= B_MAX
    )


def process(pair: str, monday: str, window: int) -> str:
    src = path_utils.features_file(pair, monday, window, ALG_TAG)
    if not src.exists():
        return "skip"
    dst = path_utils.digest_file(pair, monday, window, ALG_TAG)
    if dst.exists():
        return "skip"
    kept = []
    with src.open() as fin:
        reader = csv.reader(fin)
        for row in reader:
            try:
                r2 = float(row[2])
                a  = float(row[3])
                b  = float(row[4])
            except (IndexError, ValueError):
                continue  # malformed line
            if row_ok(r2, a, b):
                kept.append(",".join(row))
    if kept:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text("\n".join(kept) + "\n")
        return "ok"
    return "skip_empty"


def main(pair: str, limit: int | None):
    for w in WINDOWS:
        stats = {"ok": 0, "skip": 0, "skip_empty": 0}
        for monday in weekly_dates(pair, w, limit):
            res = process(pair, monday, w)
            stats[res] += 1
        print(f"digest window {w}: ", *(f"{k}={v}" for k, v in stats.items()))

if __name__ == "__main__":
    import sys, argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", default="USDJPY")
    ap.add_argument("--weeks", type=int, default=None)
    args = ap.parse_args()
    weeks = args.weeks or config.get("pipeline", "weeks_default", int)
    main(args.pair.upper(), weeks)
