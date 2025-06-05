#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# NEW MODULE: src/viz/grid_heat.py  (heat‑map of grid‑search metrics)
# -----------------------------------------------------------------------------
# This module scans data/knn/grids/<PAIR>/window_<W>/week_<DATE>.npy and shows a
# Plotly heat‑map for any (week, window, side, metric).
# -----------------------------------------------------------------------------

import re
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# Root folder where knn_gridsearch saves its metric cubes
ROOT = Path("data/knn/grids")
PAIR = "USDJPY"  # could expose as selector if you trade multiple pairs

# -----------------------------------------------------------------------------
# Discover grid files:   window_* / week_*.npy  two levels deep
# -----------------------------------------------------------------------------
grid_files = sorted((ROOT / PAIR).rglob("week_*.npy"))
if not grid_files:
    st.error("No grid .npy files found. Run knn_gridsearch first.")
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

# Axis labels – pull from config so they stay consistent
from utils import config
NS_WEEK = config.getlist("knn", "Ns_week", int)
THETAS = config.getlist("knn", "thetas", int)

# -----------------------------------------------------------------------------
# Build heat‑map  – wide aspect + fixed colour scale (−15 … +15)
# -----------------------------------------------------------------------------
fig = px.imshow(
    Z,
    x=THETAS,
    y=NS_WEEK,
    color_continuous_scale="RdBu",
    origin="lower",
    aspect="auto",
    zmin=-15, zmax=15,        # fixed scale across weeks/windows
)

# Make the figure wider (≈ 5× as wide as tall)
rows = len(NS_WEEK)
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

