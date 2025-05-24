#!/usr/bin/env python3
"""
download_raw.py – Fetch Dukascopy .bi5 tick files

* After 17:00 Friday (New-York) or any time on Sat/Sun, the **current
  week is considered complete** and will be downloaded.
* Otherwise we skip the still-open week and start with the previous one.

Example:
    python download_raw.py --pair USDJPY --weeks 80
"""
from __future__ import annotations
from pathlib import Path
import argparse, asyncio, aiohttp, datetime as dt, zoneinfo, tqdm, pathlib

BASE = ("https://datafeed.dukascopy.com/datafeed/{pair}/{y}/"
        "{m:02d}/{d:02d}/{h:02d}h_ticks.bi5")
NY = zoneinfo.ZoneInfo("America/New_York")

# ----------------------------------------------------------------------
def last_completed_monday_utc(now_utc: dt.datetime) -> dt.datetime:
    """Return Monday 00:00 UTC of the most recently *finished* trading week."""
    now_ny = now_utc.astimezone(NY)

    # If after Fri 17:00 NY or weekend → this week is finished.
    finished = (
        now_ny.weekday() > 4 or
        (now_ny.weekday() == 4 and now_ny.hour >= 17)
    )

    if not finished:
        # Roll back one week
        now_ny -= dt.timedelta(days=7)

    monday_ny = (now_ny - dt.timedelta(days=now_ny.weekday())
                 ).replace(hour=0, minute=0, second=0, microsecond=0)
    return monday_ny.astimezone(dt.timezone.utc)

# ----------------------------------------------------------------------
async def fetch(session, url: str, dst: Path, force: bool):
    if dst.exists() and not force:
        return "skip"
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        async with session.get(url, timeout=15) as r:
            if r.status != 200:
                return f"err:{r.status}"
            dst.write_bytes(await r.read())
            return "ok"
    except Exception as e:
        return f"err:{e.__class__.__name__}"

async def main(pair: str, weeks: int, out: Path, concurrency: int, force: bool):
    now_utc = dt.datetime.now(dt.timezone.utc).replace(minute=0,
                                                       second=0,
                                                       microsecond=0)
    start_mon = last_completed_monday_utc(now_utc)
    tasks, sem = [], asyncio.Semaphore(concurrency)

    async with aiohttp.ClientSession() as session:
        for w in range(weeks):                           # include start week
            day0 = start_mon - dt.timedelta(weeks=w)
            for h in range(24 * 7):
                t = day0 + dt.timedelta(hours=h)
                url = BASE.format(pair=pair,
                                  y=t.year,
                                  m=t.month - 1,         # Dukascopy 00–11
                                  d=t.day,
                                  h=t.hour)
                dst = (out / pair / t.strftime("%Y-%m-%d")
                             / f"{t.hour:02d}h_ticks.bi5")

                async def bound(u=url, p=dst):
                    async with sem:
                        return await fetch(session, u, p, force)
                tasks.append(bound())

        pbar = tqdm.tqdm(asyncio.as_completed(tasks),
                         total=len(tasks),
                         desc=f"Downloading {pair}")
        results = [await t for t in pbar]

    print(f"done: ok={results.count('ok')} "
          f"skip={results.count('skip')} "
          f"err={sum(r.startswith('err') for r in results)}")

# ----------------------------------------------------------------------
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", default="USDJPY")
    ap.add_argument("--weeks", type=int, default=80)
    ap.add_argument("--out", type=pathlib.Path,
                    default=pathlib.Path("data/raw/dukascopy"))
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    asyncio.run(main(**vars(args)))
