# FX

This is a personal research project exploring micro-patterns in high-frequency FX (foreign exchange) data—specifically USD/JPY—using simple, interpretable methods rather than machine learning.

The core idea is to fit quadratic curves to short windows of tick data and use the fitted parameters (a, b) as 2D features for a k-NN classifier. Entry points are selected based on consistency with past profitable patterns, filtered by R² goodness of fit and Sharpe-style metrics.

The pipeline supports:
- Windowed fitting and feature extraction
- Binary-search tuning of R² thresholds (τ)
- Grid search over k-NN thresholds (θ)
- Causal DEV/TEST evaluation
- Optional visualisation using saved train/test distributions

**Note**: This repository is not intended as a trading system or public package. It's a private sandbox for studying statistical edge in market microstructure.

Branch: [`rolling-knn`](https://github.com/hiroshi-manabe/FX/tree/rolling-knn)
