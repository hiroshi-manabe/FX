###############################################################################
# KD‑tree wrapper for (a,b) neighbours
###############################################################################

from sklearn.neighbors import KDTree
import numpy as np
import pandas as pd

class KNNModel:
    """KD‑tree on (a,b) with helper to return buy/sell tallies."""

    def __init__(self, k: int = 25):
        self.k = k
        self._tree: KDTree | None = None
        self._labels = None  # ndarray shape (n_samples, 4) -> buyPL, buyExit, sellPL, sellExit

    def fit(self, df: pd.DataFrame):
        X = df[["a", "b"]].values.astype(float)
        self._tree = KDTree(X, metric="minkowski", p=2)
        self._labels = df[["buyPL", "sellPL"]].values.astype(float)

    def scores(self, x_query: tuple[float, float],
               eps: float = 1e-6) -> dict[str, float]:
        """
        Distance-weighted confidence (‘edge’) for BUY and SELL at *x_query*.

        Returns
        -------
        { "buy":  edge_buy,
          "sell": edge_sell }
        where  edge ∈ [-1 , +1].
        """
        if self._tree is None:
            raise RuntimeError("Model not fitted")

        dist, idx = self._tree.query([x_query], k=self.k)   # (1,k)
        dist = dist[0]
        rows = self._labels[idx[0]]                        # (k, 2) -> buyPL , sellPL

        buy_pl  = rows[:, 0]
        sell_pl = rows[:, 1]

        # neighbour label  y_i  = +1 if BUY wins, else −1
        y_buy = np.where(buy_pl > sell_pl, 1.0, -1.0)

        w = 1.0 / (dist + eps)                            # inverse-distance weights
        edge_buy  = float(np.dot(w, y_buy) / w.sum())     # in [-1 , +1]
        edge_sell = -edge_buy                             # perfect symmetry

        return {"buy": edge_buy, "sell": edge_sell}
