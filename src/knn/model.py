###############################################################################
# KD‑tree wrapper for (a,b) neighbours
###############################################################################

from sklearn.neighbors import KDTree
import numpy as np
import pandas as pd

class KNNModel:
    """KD‑tree on (a,b) with helper to return buy/sell tallies."""

    def __init__(self, k: int = 25, gamma: float = 0.35,
                 pl_limit: float | None = None):
        self.k      = k
        self.gamma  = gamma
        self.pl_lim = pl_limit
        self._tree:   KDTree | None = None
        self._labels: np.ndarray | None = None   # buyPL , sellPL

    def fit(self, df: pd.DataFrame):
        X = df[["a", "b"]].values.astype(float)
        self._tree = KDTree(X, metric="minkowski", p=2)
        self._labels = df[["buyPL", "sellPL"]].values.astype(float)

    # -------------------------------------- score helper -
    def _tally_side(self, pl: np.ndarray) -> tuple[int,int,int,float]:
        """Return (wins, draws, losses, edge) for one side."""
        L = self.pl_lim if self.pl_lim is not None else 0.0
        win  = pl >  L
        loss = pl < -L
        draw = ~(win | loss)
        w = int(win.sum())
        l = int(loss.sum())
        d = self.k - w - l
        edge = (w - l) / self.k          # ∈ [-1, +1]
        return w, d, l, edge

    # ------------------------------------------ scores --
    def scores(self, query) -> dict[str, float] | None:
        if self._tree is None:
            raise RuntimeError("Model not fitted")

        dist, idx = self._tree.query([query], k=self.k)
        dist = dist[0]

        cv = dist.std(ddof=0) / dist.mean()
        rows = self._labels[idx[0]]

        w_b, d_b, l_b, edge_b = self._tally_side(rows[:, 0])
        w_s, d_s, l_s, edge_s = self._tally_side(rows[:, 1])

        return {
            "cv":  cv,
            "buy": dict(w=w_b, d=d_b, l=l_b, edge=edge_b),
            "sell":dict(w=w_s, d=d_s, l=l_s, edge=edge_s),
        }        
