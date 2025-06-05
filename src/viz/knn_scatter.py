#!/usr/bin/env python3
# src/viz/knn_scatter.py – revised
"""
Interactive scatter of (a, b) with original encoding:
    • TRAIN  (+PL / −PL)  → 1‑pixel markers (blue / red)
    • DEV    (+PL / −PL)  4‑pixel markers (blue / red)

We use Streamlit + Plotly.  Point counts can be large, so the marker sizes are
kept tiny (`sizemode="pixels"`, available since Plotly 5.17).
"""
from pathlib import Path
import re
import pandas as pd
import plotly.express as px
import streamlit as st

# -----------------------------------------------------------------------------
# Locate parquet artefacts
# -----------------------------------------------------------------------------
ROOT = Path("data/knn/viz")
PARQUETS = sorted(ROOT.rglob("*.parquet"))
if not PARQUETS:
    st.error("No parquet files found under data/knn/viz/")
    st.stop()

# Build a metadata table -------------------------------------------------------
meta_rows = []
for p in PARQUETS:
    stem = p.stem                 # e.g.  buy_N30_theta15
    mN    = re.search(r"_N(\d+)", stem)
    mTh   = re.search(r"_theta(\d+)", stem)
    meta_rows.append({
        "path"  : p,
        "week"  : p.parts[-3].split("_", 1)[1],       # week_YYYY‑MM‑DD
        "window": p.parts[-2].split("_", 1)[1],       # window_W
        "side"  : stem.split("_", 1)[0],              # buy / sell
        "N"     : mN.group(1)  if mN  else "?",
        "theta" : mTh.group(1) if mTh else "?",
    })

meta = pd.DataFrame(meta_rows)

# -----------------------------------------------------------------------------
# Streamlit selectors
# -----------------------------------------------------------------------------
week   = st.selectbox("Week",   sorted(meta["week"].unique()))
window = st.selectbox("Window", sorted(meta.query("week==@week")["window"].unique()))
side   = st.selectbox("Side",   sorted(meta.query("week==@week and window==@window")["side"].unique()))
N      = st.selectbox("N",      sorted(meta.query("week==@week and window==@window and side==@side")["N"].unique()))
theta  = st.selectbox("θ",      sorted(meta.query("week==@week and window==@window and side==@side and N==@N")["theta"].unique()))

file_path = meta.query(
    "week==@week and window==@window and side==@side and N==@N and theta==@theta"
)["path"].iloc[0]

df = pd.read_parquet(file_path)

# -----------------------------------------------------------------------------
# Encode colour (+ / −)  and marker size (TRAIN 1 px, DEV 4 px)
# -----------------------------------------------------------------------------
df["sign"] = df["pl"].apply(lambda x: "+" if x > 0 else "−")
size_map   = {"TRAIN": 1, "DEV": 4}
df["msize"] = df["set"].map(size_map)

# -----------------------------------------------------------------------------
# Build scatter
# -----------------------------------------------------------------------------
fig = px.scatter(
    df,
    x="a", y="b",
    color="sign",
    color_discrete_map={"+": "blue", "−": "red"},
    hover_data=["time_ms", "pl", "set", "r2", "tau"],
    size="msize",            # absolute because max == provided max
    size_max=4,               # ensures DEV=3px, TRAIN≈1px
)
# No explicit sizemode – default ('diameter') keeps pixel interpretation.

fig.update_layout(
    title=f"{side.upper()}  N={N}  θ={theta}  week {week}  window {window}",
    xaxis_title="quadratic a",
    yaxis_title="quadratic b",
    legend_title="P/L sign",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)

st.plotly_chart(fig, use_container_width=True)
