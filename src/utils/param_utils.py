# utils/param_utils.py

from utils import config

# --- window list -----------------------------------------------------
def windows() -> list[int]:
    return config.getlist("pipeline", "windows", int)

# --- N helpers -------------------------------------------------------
def _N_cfg_list() -> list[int]:
    return config.getlist("knn", "Ns", int)

def _N_effective(N_cfg: int) -> int:
    return N_cfg

def N_all_effective() -> list[int]:
    return [_N_effective(n) for n in _N_cfg_list()]

# --- theta list ------------------------------------------------------
def thetas() -> list[int]:
    return config.getlist("knn", "thetas", int)

def label_tag() -> str:
    """Return composite tag like  pl30_t0.50  (two decimals fixed)."""
    from utils import config
    pl  = config.get("pipeline", "pl_limit",  int)
    tau = config.get("pipeline", "time_limit", float)
    return f"pl{pl}_t{tau:0.2f}"

