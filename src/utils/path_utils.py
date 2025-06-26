"""
Canonical path helpers for the FX pipeline.
Change ONE place – everything else follows.
"""

from pathlib import Path
from datetime import date
from utils import tag_ctx

DATA_ROOT = Path("data")           # git‑ignored
PROJECT_ROOT = Path("")           # git‑ignored
ALG_TAGS   = {
    "quadratic_v1": "quad_v1",
    "knn_v1": "knn_v1",
}

def data_root() -> Path:
    return DATA_ROOT

def dukascopy_raw_root() -> Path:
    return data_root() / "raw" / "dukascopy"

def bin_dir() -> Path:
    return PROJECT_ROOT / "build" / "bin"

def raw_tick(pair: str, d: date, hour: int) -> Path:
    return (
        dukascopy_raw_root() / pair
        / d.strftime("%Y-%m-%d")
        / f"{hour:02d}h_ticks.csv"
    )

def weekly_dir(pair: str) -> Path:
    return data_root() / "weekly" / pair

def weekly_file(pair: str, monday_date: str) -> Path:
    return weekly_dir(pair) / f"week_{monday_date}.csv"

def label_dir(pair: str,window: int) -> Path:
    return (data_root() / "labels" / tag_ctx.label_tag() / pair /
            f"window_{window}")

def label_file(pair: str, monday: str,window:int) -> Path:
    return label_dir(pair, window) / f"week_{monday}.csv"

def features_dir(pair: str, window: int) -> Path:
    return (data_root() / "features" / tag_ctx.label_tag() /
            tag_ctx.feat_tag() / pair / f"window_{window}")

def features_file(pair: str, monday_date: str, window: int) -> Path:
    return features_dir(pair, window) / f"week_{monday_date}.csv"

def digest_dir(pair: str, window: int) -> Path:
    return (data_root() / "digest" / tag_ctx.label_tag() /
            tag_ctx.feat_tag() / pair / f"window_{window}")

def digest_file(pair: str, monday_date: str, window: int) -> Path:
    return digest_dir(pair, window) / f"week_{monday_date}.csv"

def grid_dir(pair: str, window: int) -> Path:
    return (data_root() / "knn" / "grids" / tag_ctx.label_tag() /
            tag_ctx.feat_tag() / tag_ctx.knn_tag() /
            pair / f"window_{window}")

def grid_file(pair: str, monday_date: str, window: int) -> Path:
    return grid_dir(pair, window) / f"week_{monday_date}.npy"

def trade_dir(pair: str, monday_date: str, window: int) -> Path:
    return (data_root() / "knn" / "trades" / tag_ctx.label_tag() /
            tag_ctx.feat_tag() / tag_ctx.knn_tag() /
            pair / f"window_{window}" / f"week_{monday_date}")

def trade_file(pair: str, monday_date: str, window: int, side: str, N: int, theta: int) -> Path:
    return trade_dir(pair, monday_date, window) / f"{side}_N{N}_theta{theta}.parquet"

def vis_dir(pair: str, monday_date: str, window: int) -> Path:
    return (data_root() / "knn" / "viz" / tag_ctx.label_tag() /
            tag_ctx.feat_tag() / tag_ctx.knn_tag() / pair /
            f"window_{window}" / f"week_{monday_date}")

def vis_file(pair: str, monday_date: str, window: int, side: str, N: int, theta: float) -> Path:
    return vis_dir(pair, monday_date, window) / f"{side}_N{N}_theta{theta}.parquet"

def params_dir(pair: str) -> Path:
    return (data_root() / "knn" / "params" / tag_ctx.label_tag() /
            tag_ctx.feat_tag() / tag_ctx.knn_tag() / pair)

def params_file(pair: str, monday_date: str) -> Path:
    return params_dir(pair) / f"week_{monday_date}.json"

def quadratic_tag() -> str:
    return config.get("pipeline", "quadratic_alg_tag")

