#!/usr/bin/env python3
"""
weekify.py – merge seven days of hourly tick CSVs into one weekly file.

Enhancement
-----------
• **NY-close awareness** – If the current moment is *after* the New-York
  FX close (Friday 17:00 America/New_York) we treat the finishing week as
  complete and include it in processing; otherwise we start counting
  from the previous Monday (original behaviour).
"""
import argparse
import csv
import datetime as dt
import zoneinfo
from utils import path_utils

TOKYO = zoneinfo.ZoneInfo("Asia/Tokyo")
NY    = zoneinfo.ZoneInfo("America/New_York")


# ---------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------

def monday_date(ts: dt.datetime) -> dt.date:
    """Return Monday (Tokyo) of the datetime's week."""
    ts = ts.astimezone(TOKYO)
    return (ts - dt.timedelta(days=ts.weekday())).date()


def ny_week_has_closed(now_tokyo: dt.datetime) -> bool:
    """True if NY-close (Fri 17:00 NY) for the current week has passed."""
    ny = now_tokyo.astimezone(NY)
    # weekday: Mon=0 … Sun=6
    return (ny.weekday() > 4) or (ny.weekday() == 4 and ny.hour >= 17)


def process_week(pair: str, monday: dt.date, force: bool) -> str:
    out_file = path_utils.weekly_file(pair, monday.isoformat())
    if out_file.exists() and not force:
        return "skip"

    out_file.parent.mkdir(parents=True, exist_ok=True)
    week_ms0 = int(
        dt.datetime.combine(monday, dt.time(0), tzinfo=TOKYO).timestamp() * 1000
    )

    with out_file.open("w", newline="") as fout:
        writer = csv.writer(fout)
        start = dt.datetime.combine(monday, dt.time(0), tzinfo=TOKYO)
        for day in range(7):
            for hour in range(24):
                t = start + dt.timedelta(days=day, hours=hour)
                src = path_utils.raw_tick(pair, t.date(), t.hour).with_suffix(".csv")
                if not src.exists():
                    continue
                hour_ms0 = int(t.timestamp() * 1000) - week_ms0
                with src.open() as fin:
                    for row in csv.reader(fin):
                        if not row:
                            continue
                        row[0] = str(hour_ms0 + int(row[0]))
                        writer.writerow(row)
    return "ok"


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------

def main(pair: str, weeks: int, force: bool):
    now_tokyo = dt.datetime.now(TOKYO)
    include_current = ny_week_has_closed(now_tokyo)

    base_monday = monday_date(now_tokyo)
    # if week still open, start from the *previous* Monday offset by one
    start_offset = 0 if include_current else 1

    stats = {"ok": 0, "skip": 0}
    for w in range(start_offset, weeks + start_offset):
        monday = base_monday - dt.timedelta(weeks=w)
        res = process_week(pair, monday, force)
        stats[res] += 1
        print(f"{res}: {monday}")

    print("weekify", *(f"{k}={v}" for k, v in stats.items()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair", default="USDJPY")
    parser.add_argument("--weeks", type=int, default=8)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    main(args.pair.upper(), args.weeks, args.force)
