###############################################################################
# R² threshold search with side‑specific spacing
###############################################################################

from __future__ import annotations

import pandas as pd

###############################################################################
# R² threshold search with side-specific spacing
###############################################################################
def binary_search_r2(
    df: pd.DataFrame,
    N_target: int,
    spacing_ms: int,
    side: str,
    *,
    iters: int = 25,
) -> tuple[float, list[int]]:
    """
    Return (tau, kept_idx) where tau is the *largest* R² threshold such
    that spacing-filtered rows ≥ N_target, and kept_idx is the list of
    row indices that satisfy that tau (for this *side*).

    `side` ∈ {"buy", "sell"} determines which exit column to use.
    """
    exit_col = f"{side}Exit"

    def count_with_tau(tau: float) -> int:
        last_exit = -1_000_000_000  # far past
        kept = 0
        for r in df.itertuples():
            if r.r2 < tau:
                continue
            if r.time_ms >= last_exit + spacing_ms:
                kept += 1
                last_exit = getattr(r, exit_col)
                if kept >= N_target:          # early-exit
                    break
        return kept

    # ---------- 1. establish bounds -----------------------------------------
    tau_lo = 0.0
    tau_hi = float(df.r2.max())

    if count_with_tau(tau_lo) < N_target:
        # impossible: even tau=0 keeps too few rows
        return 0.0, []

    # ---------- 2. binary search (counts only) ------------------------------
    for _ in range(iters):
        tau_mid = 0.5 * (tau_lo + tau_hi)
        if count_with_tau(tau_mid) >= N_target:
            tau_lo = tau_mid          # still enough rows → tighten
        else:
            tau_hi = tau_mid          # too strict → loosen

    tau_star = tau_lo

    # ---------- 3. final pass to collect indices ----------------------------
    kept_idx: list[int] = []
    last_exit = -1_000_000_000
    for i, r in enumerate(df.itertuples()):
        if r.r2 < tau_star:
            continue
        if r.time_ms >= last_exit + spacing_ms:
            kept_idx.append(i)
            last_exit = getattr(r, exit_col)
            if len(kept_idx) == N_target:
                break

    return tau_star, kept_idx
