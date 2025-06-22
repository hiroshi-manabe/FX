# utils/param_utils.py

from utils import config

# --- window list -----------------------------------------------------
def windows() -> list[int]:
    return config.getlist("pipeline", "windows", int)

# --- N helpers -------------------------------------------------------
_USE_SCALE = config.get('knn', 'use_week_scaling', bool)
_TRAIN_WEEKS = config.get('knn', 'train_weeks', int)

def _N_cfg_list() -> list[int]:
    return config.getlist("knn", "Ns_week", int)

def _N_effective(N_cfg: int) -> int:
    return N_cfg * _TRAIN_WEEKS if _USE_SCALE else N_cfg

def N_all_effective() -> list[int]:
    return [_N_effective(n) for n in _N_cfg_list()]

# --- theta list ------------------------------------------------------
def thetas() -> list[float]:
    return config.getlist("knn", "thetas", float)

def label_tag() -> str:
    """Return composite tag like  pl30_t0.50  (two decimals fixed)."""
    from utils import config
    pl  = config.get("pipeline", "pl_limit",  int)
    tau = config.get("pipeline", "time_limit", float)
    return f"pl{pl}_t{tau:0.2f}"

