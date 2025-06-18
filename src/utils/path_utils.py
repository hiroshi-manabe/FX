"""
Canonical path helpers for the FX pipeline.
Change ONE place – everything else follows.
"""

from pathlib import Path
from datetime import date
from utils import config

DATA_ROOT = Path("data")           # git‑ignored
PROJECT_ROOT = Path("")           # git‑ignored
ALG_TAGS   = {
    "quadratic_v1": "quad_v1",
    "knn_v1": "knn_v1",
}

def data_root() -> Path:
    return DATA_ROOT

def dukascopy_raw_root() -> Path:
    return DATA_ROOT / "raw" / "dukascopy"

def bin_dir() -> Path:
    return PROJECT_ROOT / "build" / "bin"

def raw_tick(pair: str, d: date, hour: int) -> Path:
    return (
        dukascopy_raw_root() / pair
        / d.strftime("%Y-%m-%d")
        / f"{hour:02d}h_ticks.csv"
    )

def weekly_dir(pair: str) -> Path:
    return DATA_ROOT / "weekly" / pair

def weekly_file(pair: str, monday_date: str) -> Path:
    return weekly_dir(pair) / f"week_{monday_date}.csv"

def label_pl_dir(pair: str, pl_tag: str = "pl30") -> Path:
    return DATA_ROOT / "labels" / pl_tag / pair

def label_pl_file(pair: str, monday_date: str, pl_tag: str = "pl30") -> Path:
    return label_pl_dir(pair, pl_tag) / f"week_{monday_date}.csv"

def features_dir(pair: str, window: int, alg: str | None = None) -> Path:
    tag = alg or quadratic_tag()
    return DATA_ROOT / "features" / tag / pair / f"window_{window}"

def features_file(pair: str, monday_date: str, window: int, alg: str | None = None) -> Path:
    return features_dir(pair, window, alg) / f"week_{monday_date}.csv"

def digest_dir(pair: str, window: int) -> Path:
    return DATA_ROOT / "digest" / pair / f"window_{window}"

def digest_file(pair: str, monday_date: str, window: int) -> Path:
    return digest_dir(pair, window) / f"week_{monday_date}.csv"

def grid_dir(pair: str, window: int) -> Path:
    return DATA_ROOT / "knn" / "grids" / pair / f"window_{window}"

def grid_file(pair: str, monday_date: str, window: int) -> Path:
    return grid_dir(pair, window) / f"week_{monday_date}.npy"

def trade_dir(pair: str, monday_date: str, window: int) -> Path:
    return DATA_ROOT / "knn" / "trades" / pair / f"window_{window}" / f"week_{monday_date}"

def trade_file(pair: str, monday_date: str, window: int, side: str, N: int, theta: float) -> Path:
    return trade_dir(pair, monday_date, window) / f"{side}_N{N}_theta{theta}.parquet"

def vis_dir(pair: str, monday_date: str, window: int) -> Path:
    return DATA_ROOT / "knn" / "viz" / pair / f"window_{window}" / f"week_{monday_date}"

def vis_file(pair: str, monday_date: str, window: int, side: str, N: int, theta: float) -> Path:
    return vis_dir(pair, monday_date, window) / f"{side}_N{N}_theta{theta*100}.parquet"

def params_dir(pair: str) -> Path:
    return DATA_ROOT / "knn" / "params" / pair

def params_file(pair: str, monday_date: str) -> Path:
    return params_dir(pair) / f"week_{monday_date}.json"

def opps_file(pair: str, monday_date: str) -> Path:
    return DATA_ROOT / "knn" / "opps" / pair / f"week_{monday_date}.csv"

def quadratic_tag() -> str:
    return config.get("pipeline", "quadratic_alg_tag")

def knn_model(pair: str, monday_date: str, window: int, r2: float, alg="knn_v1"):
    tag = ALG_TAGS[alg]
    return (
        DATA_ROOT
        / "models" / tag / pair
        / f"window_{window}" / f"R2_{r2:.4f}" / f"week_{monday_date}.pkl"
    )

def report(pair: str, monday_date: str) -> Path:
    return DATA_ROOT / "reports" / pair / monday_date / "summary.csv"

# Utilities
def ensure_parent(p: Path) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    return p
