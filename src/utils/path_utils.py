# src/utils/path_utils.py
"""
Canonical path helpers for the FX pipeline.
Change ONE place – everything else follows.
"""

from pathlib import Path
from datetime import date

DATA_ROOT = Path("data")           # git‑ignored
PROJECT_ROOT = Path("")           # git‑ignored
ALG_TAGS   = {
    "quadratic_v1": "quad_v1",
    "knn_v1": "knn_v1",
}

def raw_tick(pair: str, d: date, hour: int) -> Path:
    """Mirror Dukascopy: data/raw/dukascopy/USDJPY/2025‑03‑25/09h_ticks.csv"""
    return (
        DATA_ROOT
        / "raw" / "dukascopy" / pair
        / d.strftime("%Y-%m-%d")
        / f"{hour:02d}h_ticks.csv"
    )

def weekly(pair: str, iso_week: str) -> Path:
    """data/weekly/USDJPY/week_2025-13.csv"""
    return DATA_ROOT / "weekly" / pair / f"week_{iso_week}.csv"

def dukascopy_raw_root() -> Path:
    return DATA_ROOT / "raw" / "dukascopy"

def label_pl(pair: str, iso_week: str, pl_tag: str = "pl30") -> Path:
    """data/labels/pl30/USDJPY/week_2025-13.csv"""
    return (
        DATA_ROOT / "labels" / pl_tag / pair / f"week_{iso_week}.csv"
    )

def features(pair: str, iso_week: str, window: int, alg="quadratic_v1") -> Path:
    tag = ALG_TAGS[alg]
    return (
        DATA_ROOT
        / "features" / tag / pair
        / f"window_{window}" / f"week_{iso_week}.csv"
    )

def knn_model(pair: str, iso_week: str, window: int, r2: float, alg="knn_v1"):
    tag = ALG_TAGS[alg]
    return (
        DATA_ROOT
        / "models" / tag / pair
        / f"window_{window}" / f"R2_{r2:.4f}" / f"week_{iso_week}.pkl"
    )

def report(pair: str, iso_week: str) -> Path:
    return DATA_ROOT / "reports" / pair / iso_week / "summary.csv"

# Utilities
def ensure_parent(p: Path) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    return p
