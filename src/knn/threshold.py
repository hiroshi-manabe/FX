###############################################################################
# R² threshold search with side‑specific spacing
###############################################################################

from __future__ import annotations

import pandas as pd

def _count_with_tau(df: pd.DataFrame, tau: float, N_target: int,
                    spacing_ms: int, side: str) -> int:
    """Return number of kept rows using the given τ and spacing.
    side = 'buy' or 'sell'."""
    last_exit = -1_000_000_000
    kept = 0
    pl_col   = f"{side}PL"
    exit_col = f"{side}Exit"

    for row in df.itertuples(index=False):
        if row.r2 < tau:
            continue
        if row.time_ms < last_exit + spacing_ms:
            continue
        kept += 1
        last_exit = getattr(row, exit_col)
        if kept >= N_target:
            break
    return kept


def binary_search_r2(df: pd.DataFrame, N_target: int, spacing_ms: int,
                     side: str, tol: float = 1e-4) -> Tuple[float, int]:
    """Find minimal τ so that *at least* N_target rows survive spacing.

    Returns (tau, kept_rows).
    If not reachable, returns (0.0, kept_rows) where kept_rows < N_target.
    """
    # Quick bounds
    tau_lo, tau_hi = 0.0, 1.0
    if _count_with_tau(df, tau_hi, N_target, spacing_ms, side) < N_target:
        return 0.0, _count_with_tau(df, 0.0, N_target, spacing_ms, side)

    while tau_hi - tau_lo > tol:
        mid = (tau_lo + tau_hi) / 2.0
        kept = _count_with_tau(df, mid, N_target, spacing_ms, side)
        if kept >= N_target:
            tau_hi = mid
        else:
            tau_lo = mid
    kept_final = _count_with_tau(df, tau_hi, N_target, spacing_ms, side)
    return tau_hi, kept_final
