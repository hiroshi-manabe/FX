#!/usr/bin/env python3
#!/usr/bin/env python3
"""
filter_digest.py – apply quality + density filters and enforce
"one‑trade‑at‑a‑time" spacing.

Reads  : data/features/<ALG_TAG>/<PAIR>/window_<W>/week_<YYYY-MM-DD>.csv
Writes : data/digest/<ALG_TAG>/<PAIR>/window_<W>/week_<YYYY-MM-DD>.csv

Filtering steps per row:
1.  R² ≥ r2_threshold and |a|,|b| within bounds.
2.  Density check:   past_width / ticks_in_window ≤ max_ms_per_tick  (reject sparse).
3.  Spacing rule: current_time ≥ last_exit_ms  (where last_exit_ms = max(buyExit, sellExit) of last **kept** row).
"""
from __future__ import annotations

import argparse
import csv
import collections
from pathlib import Path

from utils import path_utils, config

# --- config --------------------------------------------------------
WINDOWS              = config.getlist("pipeline", "windows", int)
ALG_TAG              = config.get("pipeline", "quadratic_alg_tag")
PL_TAG               = config.get("pipeline", "pl_tag")

R2_THR               = config.get("digest", "r2_threshold", float)
A_MIN                = config.get("digest", "min_abs_a", float)
A_MAX                = config.get("digest", "max_abs_a", float)
B_MIN                = config.get("digest", "min_abs_b", float)
B_MAX                = config.get("digest", "max_abs_b", float)
MAX_MS_PER_TICK      = config.get("digest", "max_ms_per_tick", float)  # density gate

# ------------------------------------------------------------------

def weekly_dates(pair: str, window: int, limit: int | None):
    feats = sorted(path_utils.features_dir(pair, window, ALG_TAG).glob("week_*.csv"))
    if limit:
        feats = feats[-limit:]
    return [p.stem.split("_")[1] for p in feats]


def row_passes(r2: float, a: float, b: float) -> bool:
    return (
        r2 >= R2_THR
        and A_MIN <= abs(a) <= A_MAX
        and B_MIN <= abs(b) <= B_MAX
    )


def process(pair: str, monday: str, window: int, force: bool) -> str:
    src = path_utils.features_file(pair, monday, window, ALG_TAG)
    if not src.exists():
        return "skip"

    dst = path_utils.digest_file(pair, monday, window, ALG_TAG)
    if dst.exists() and not force:
        return "skip"

    kept_rows: list[str] = []
    last_exit_ms = -1  # spacing rule
    recent_ticks: collections.deque[int] = collections.deque()

    with src.open() as fin:
        for raw in fin:
            row = raw.rstrip().split(",")
            if len(row) < 7:
                continue

            # basic fields
            try:
                t_ms = int(row[0])
            except ValueError:
                continue

            # ---- update density deque ----
            recent_ticks.append(t_ms)
            window_ms = window  # equal to past_width for this file
            while recent_ticks and recent_ticks[0] < t_ms - window_ms:
                recent_ticks.popleft()
            if window_ms / len(recent_ticks) > MAX_MS_PER_TICK:
                continue  # too sparse, skip

            # ---- parse coefficient block ----
            coeff_parts = row[6].split(":")
            if len(coeff_parts) < 5:
                continue
            try:
                a = float(coeff_parts[1])
                b = float(coeff_parts[2])
                r2 = float(coeff_parts[4])
            except ValueError:
                continue
            if not row_passes(r2, a, b):
                continue

            # ---- parse buy/sell block ----
            future_parts = row[5].split(":")
            if len(future_parts) < 4:
                continue
            try:
                buy_exit = int(future_parts[1])  # index 1 is buyExitTs
                sell_exit = int(future_parts[3]) # index 3 is sellExitTs
            except ValueError:
                continue
            exit_ts = max(buy_exit, sell_exit)

            # spacing rule: no overlap with previous kept trade
            if last_exit_ms >= 0 and t_ms < last_exit_ms:
                continue

            # keep row
            kept_rows.append(raw.rstrip())
            last_exit_ms = exit_ts

    if kept_rows:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text("\n".join(kept_rows) + "\n")
        return "ok"
    return "skip_empty"


# --------------------- CLI ----------------------------------------

def main(pair: str, limit: int | None, force: bool):
    for w in WINDOWS:
        stats = {"ok": 0, "skip": 0, "skip_empty": 0}
        for monday in weekly_dates(pair, w, limit):
            res = process(pair, monday, w, force)
            stats[res] += 1
        print(f"digest window {w}: ", *(f"{k}={v}" for k, v in stats.items()))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", default="USDJPY")
    ap.add_argument("--weeks", type=int, default=None)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    week_limit = args.weeks or config.get("pipeline", "weeks_default", int)
    main(args.pair.upper(), week_limit, args.force)
