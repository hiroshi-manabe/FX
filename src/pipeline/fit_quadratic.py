#!/usr/bin/env python3
"""
fit_quadratic.py – run quadratic fitting per window, one file per call.

Reads  : data/labels/<PL_TAG>/<PAIR>/week_YYYY-MM-DD.csv
Writes : data/features/<ALG_TAG>/<PAIR>/window_<W>/week_YYYY-MM-DD.csv
Call   : build/bin/fit_quadratic <window>  (stdin = label CSV, stdout = feature CSV)
"""

import argparse, subprocess, zoneinfo, datetime as dt
from pathlib import Path
from utils import path_utils, config

BIN      = Path("build/bin/fit_quadratic")
WINDOWS  = config.getlist("pipeline", "windows", int)
ALG_TAG  = config.get("pipeline", "quadratic_alg_tag")
PL_TAG   = config.get("pipeline", "pl_tag")
TOKYO    = zoneinfo.ZoneInfo("Asia/Tokyo")

# ---------------------------------------------------------------------------

def monday_dates(pair: str, limit: int | None):
    all_weeks = sorted(path_utils.label_pl_dir(pair, PL_TAG).glob("week_*.csv"))
    if limit:
        all_weeks = all_weeks[-limit:]
    return [w.stem.split("_")[1] for w in all_weeks]

def process(pair: str, monday: str, window: int) -> str:
    src = path_utils.label_pl_file(pair, monday, PL_TAG)
    if not src.exists():
        return "skip"
    dst = path_utils.features_file(pair, monday, window, ALG_TAG)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return "skip"
    with src.open("rb") as fin, dst.open("wb") as fout:
        subprocess.check_call([BIN, str(window)], stdin=fin, stdout=fout)
    return "ok"

# ---------------------------------------------------------------------------

def main(pair: str, limit: int | None):
    for w in WINDOWS:
        stats = {"ok": 0, "skip": 0, "err": 0}
        for monday in monday_dates(pair, limit):
            try:
                stats[process(pair, monday, w)] += 1
            except subprocess.CalledProcessError:
                stats["err"] += 1
        print(f"window {w}: ok={stats['ok']} skip={stats['skip']} err={stats['err']}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair",  default="USDJPY")
    ap.add_argument("--weeks", type=int, default=None)
    args = ap.parse_args()
    weeks_limit = args.weeks or config.get("pipeline", "weeks_default", int)
    main(args.pair.upper(), weeks_limit)
