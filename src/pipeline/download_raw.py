#!/usr/bin/env python3
"""
download_raw.py  --  Fetch Dukascopy tick .bi5 files.

Usage:
  python download_raw.py --pair USDJPY --weeks 80 --out data/raw/dukascopy \
         [--concurrency 8] [--force]

The script mirrors Dukascopy's folder hierarchy, month 00‑11.
"""

import argparse, asyncio, aiohttp, datetime as dt, os, sys, pathlib, tqdm

BASE = "https://datafeed.dukascopy.com/datafeed/{pair}/{y}/{m:02d}/{d:02d}/{h:02d}h_ticks.bi5"

async def fetch(session, url, target, force):
    if target.exists() and not force:
        return "skip"
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        async with session.get(url, timeout=15) as r:
            if r.status != 200:
                return f"err:{r.status}"
            data = await r.read()
            target.write_bytes(data)
            return "ok"
    except Exception as e:
        return f"err:{e.__class__.__name__}"

async def main(pair, weeks, out, concurrency, force):
    now = dt.datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    # go back to start‑of‑hour Monday for stability
    start = now - dt.timedelta(days=now.weekday(), hours=now.hour)
    tasks, sem = [], asyncio.Semaphore(concurrency)
    async with aiohttp.ClientSession() as session:
        for w in range(1, weeks + 1):
            day0 = start - dt.timedelta(weeks=w+1)
            for h in range(24 * 7):
                t = day0 + dt.timedelta(hours=h)
                url = BASE.format(pair=pair,
                                  y=t.year,
                                  m=t.month-1,        # Dukascopy month 00‑11
                                  d=t.day,
                                  h=t.hour)
                dst = (out / pair / t.strftime("%Y-%m-%d")
                             / f"{t.hour:02d}h_ticks.bi5")
                async def bound_fetch(u=url, d=dst):
                    async with sem:
                        return await fetch(session, u, d, force)
                tasks.append(bound_fetch())
        pbar = tqdm.tqdm(asyncio.as_completed(tasks), total=len(tasks),
                         desc=f"Downloading {pair}")
        results = [await coro for coro in pbar]
    # quick stats
    print(f"done: ok={results.count('ok')} skip={results.count('skip')}"
          f" err={sum(r.startswith('err') for r in results)}")

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
