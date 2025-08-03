#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# NEW MODULE: src/viz/grid_heat.py  (heat‑map of grid‑search metrics)
# -----------------------------------------------------------------------------
# This module scans data/knn/grids/<PAIR>/window_<W>/week_<DATE>.npy and shows a
# Plotly heat‑map for any (week, window, side, metric).
# -----------------------------------------------------------------------------

import os, sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))   # add src/ to PYTHONPATH
from utils import path_utils, experiment_config
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# -----------------------------------------------------------------------------
# Choose data source
# -----------------------------------------------------------------------------

MODE = st.sidebar.radio("Source", ["experiment", "legacy"])

if MODE == "experiment":
    exp_root = path_utils.EXPERIMENTS_ROOT
    exps = sorted([p.name for p in exp_root.iterdir() if p.is_dir()])
    exp_name = st.sidebar.selectbox("Experiment", exps)
    cfg = experiment_config.ExperimentConfig.load(exp_root / exp_name)
    PAIR = st.sidebar.selectbox("Pair", sorted(
        [p.name for p in (exp_root/exp_name/"grids").iterdir() if p.is_dir()]
    ))

    root = path_utils.exp_grids_dir(exp_name, PAIR, window=0).parents[1]  # …/grids/<PAIR>
    Ns      = cfg.Ns
    THETAS  = cfg.thetas
else:
    from utils import tag_ctx, param_utils
    label_tag = tag_ctx.label_tag()
    feat_tag  = tag_ctx.feat_tag()
    knn_tag   = tag_ctx.knn_tag()

    pair_root = Path("data/knn/grids") / label_tag / feat_tag / knn_tag
    PAIR = st.sidebar.selectbox("Pair",
                                sorted(p.name for p in pair_root.iterdir() if p.is_dir()))
    root = pair_root / PAIR
    Ns      = param_utils.N_all_effective()
    THETAS  = param_utils.thetas()

grid_files = sorted(root.rglob("week_*.npy"))

if not grid_files:
    st.warning(f"No grid files under {root}")
    st.stop()

meta_rows = []
for p in grid_files:
    week   = p.stem.split("_", 1)[1]          # week_2024-12-09 → 2024-12-09
    window = p.parent.name.split("_", 1)[1]   # window_600 → 600
    meta_rows.append({"path": p, "week": week, "window": window})

df_meta = pd.DataFrame(meta_rows)

# -----------------------------------------------------------------------------
# Streamlit selectors
# -----------------------------------------------------------------------------
week = st.selectbox("Week", sorted(df_meta["week"].unique()))
window = st.selectbox(
    "Window",
    sorted(df_meta.query("week == @week")["window"].unique()),
)
side = st.radio("Side", ["buy", "sell"], horizontal=True)
metric_name = st.selectbox("Metric", ["meanPL", "std", "t-stat"], index=0)
metric_idx = {"meanPL": 1, "std": 2, "t-stat": 3}[metric_name]

# -----------------------------------------------------------------------------
# Load selected .npy file & slice metric cube
# -----------------------------------------------------------------------------
sel_path = df_meta.query("week == @week and window == @window")["path"].iloc[0]
grids = np.load(sel_path, allow_pickle=True).item()

Z = grids[side][:, :, metric_idx].astype(float)
Z[Z == 0] = np.nan  # mark unreachable cells

# -----------------------------------------------------------------------------
# Build heat‑map  – wide aspect + fixed colour scale (−15 … +15)
# -----------------------------------------------------------------------------
fig = px.imshow(
    Z,
    x=THETAS,
    y=Ns,
    color_continuous_scale="RdBu",
    origin="lower",
    aspect="auto",
    zmin=-15, zmax=15,        # fixed scale across weeks/windows
)

# Make the figure wider (≈ 5× as wide as tall)
rows = len(Ns)
cols = len(THETAS)
base_height = 400
fig.update_layout(
    width=base_height * 5,   # 5× width
    height=base_height,
    title=f"{side.upper()} – {metric_name}  week {week}  window {window}",
    xaxis_title="θ (score gap)",
    yaxis_title="N (rows/week)",
)

st.plotly_chart(fig, use_container_width=False)

