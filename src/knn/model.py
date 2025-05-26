###############################################################################
# KD‑tree wrapper for (a,b) neighbours
###############################################################################

from sklearn.neighbors import KDTree
import numpy as np

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

    def scores(self, x_query: tuple[float, float], pl_cut: float = 30.0,
               weighted: bool = True) -> dict[str, tuple[int, int, float]]:
        """Return wins, losses, meanPL for buy and sell around *x_query*."""
        if self._tree is None:
            raise RuntimeError("Model not fitted")
        dist, idx = self._tree.query([x_query], k=self.k)
        idx = idx[0]
        d_inv = 1.0 / (dist[0] + 1e-9) if weighted else np.ones_like(dist[0])

        wins_b = losses_b = wins_s = losses_s = 0
        pl_sum_b = pl_sum_s = 0.0
        w_sum_b = w_sum_s = 0.0

        for w, i in zip(d_inv, idx):
            buy_pl, sell_pl = self._labels[i]
            # BUY side
            if buy_pl >= +pl_cut:
                wins_b += 1; pl_sum_b += w * buy_pl; w_sum_b += w
            elif buy_pl <= -pl_cut:
                losses_b += 1; pl_sum_b += w * buy_pl; w_sum_b += w
            # SELL side
            if sell_pl >= +pl_cut:
                wins_s += 1; pl_sum_s += w * sell_pl; w_sum_s += w
            elif sell_pl <= -pl_cut:
                losses_s += 1; pl_sum_s += w * sell_pl; w_sum_s += w

        mean_b = 0.0 if w_sum_b == 0 else pl_sum_b / w_sum_b
        mean_s = 0.0 if w_sum_s == 0 else pl_sum_s / w_sum_s
        return {
            "buy":  (wins_b, losses_b, mean_b),
            "sell": (wins_s, losses_s, mean_s),
        }
