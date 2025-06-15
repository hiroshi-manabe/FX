#!/usr/bin/env python3
"""
bin_to_csv.py  –  Decompress .bi5 → .bin and convert to .csv, idempotently.

Requires:
  * build/bin/bin_to_csv   (compiled by Makefile)
  * external `lzma` or `xz` on PATH, OR Python's built‑in lzma module.

Usage:
  python -m pipeline.bin_to_csv --pair USDJPY
"""
import argparse, subprocess, sys, os
from pathlib import Path
from multiprocessing.pool import ThreadPool
from utils import path_utils

BIN2CSV = path_utils.bin_dir() / "bin_to_csv"
RAWROOT = path_utils.dukascopy_raw_root()
CONCURRENCY = 8

def lzma_decompress(src: Path, dst: Path):
    """Return True on success, False if we touched an empty input."""
    if src.stat().st_size == 0:
        dst.touch()
        return False
    # prefer Python's lzma (no forking)
    import lzma
    data = lzma.decompress(src.read_bytes())
    dst.write_bytes(data)
    return True

def process(bi5: Path, force: bool):
    bin_ = bi5.with_suffix(".bin")
    csv  = bi5.with_suffix(".csv")
    # Step 1: ensure .bin
    if not bin_.exists():
        ok = lzma_decompress(bi5, bin_)
        if not ok:
            return "skip_empty"
    # Step 2: ensure .csv
    if force or not csv.exists():
        try:
            subprocess.check_call([BIN2CSV, str(bin_)], stdout=csv.open("wb"))
            return "ok"
        except subprocess.CalledProcessError as e:
            return f"err:{e.returncode}"
    return "skip"

def main(pair: str, force: bool):
    targets = list((RAWROOT / pair).rglob("*.bi5"))
    if not targets:
        sys.exit(f"No .bi5 files found under {RAWROOT/pair}")
    results = ThreadPool(CONCURRENCY).starmap(process, [(f, force) for f in targets])
    print("bin→csv",
          f"ok={results.count('ok')}",
          f"skip={results.count('skip') + results.count('skip_empty')}",
          f"err={sum(r.startswith('err') for r in results)}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", default="USDJPY")
    ap.add_argument("--weeks")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    main(args.pair.upper(), args.force)
