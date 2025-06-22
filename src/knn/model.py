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
    def _edge_side(self, pl: np.ndarray) -> float:
        """Compute normalised vote margin for ONE side."""
        L = self.pl_lim
        if L == 0:                              # legacy: any positive counts
            y = np.where(pl > 0,  1,
                np.where(pl < 0, -1, 0))
        else:                                   # three-way win / draw / loss
            y = np.where(pl >  L,  1,
                np.where(pl < -L, -1, 0))
        return ( (y == 1).sum() - (y == -1).sum() ) / self.k

    # ------------------------------------------ scores --
    def scores(self, query) -> dict[str, float] | None:
        if self._tree is None:
            raise RuntimeError("Model not fitted")

        dist, idx = self._tree.query([query], k=self.k)
        dist = dist[0]

        # CV gap guard
        cv = dist.std(ddof=0) / dist.mean()
        if self.gamma != 0 and cv > self.gamma:
            return None

        rows = self._labels[idx[0]]
        edge_buy  = self._edge_side(rows[:, 0])   # use buyPL only
        edge_sell = self._edge_side(rows[:, 1])   # use sellPL only

        return {"buy": edge_buy, "sell": edge_sell}
