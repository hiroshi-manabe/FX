#!/usr/bin/env python3
# src/viz/knn_scatter.py  –  window-aware scatter with no-hit + reject layers
#
# Shows (a, b) points coloured by trade outcome for a single (week, window,
# side, N, θ) parquet produced by knn_gridsearch.  Enhancements:
#   • Grey points  = trade executed but |PL| < PL-limit (time-out exit)
#   • Optional faint-grey dots = DEV candidates that failed θ (“rejects”)
# Everything else (dynamic window discovery, tag selectors) remains as before.
# -----------------------------------------------------------------------------

from pathlib import Path
import re, os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from utils import tag_ctx

# -----------------------------------------------------------------------------
# Sidebar – choose run context (defaults come from last pipeline run)
# -----------------------------------------------------------------------------
with st.sidebar:
    label_tag   = st.text_input("Label tag",  value=tag_ctx.label_tag())
    feat_tag    = st.text_input("Feature tag", value=tag_ctx.feat_tag())
    knn_tag     = st.text_input("KNN tag",     value=tag_ctx.knn_tag())
    show_rejects = st.checkbox("Show DEV rejects (score < θ)", value=False)

# -----------------------------------------------------------------------------
# Locate all parquet files under the chosen context
# -----------------------------------------------------------------------------
ROOT = Path("data/knn/viz") / label_tag / feat_tag / knn_tag
PARQUETS = sorted(ROOT.rglob("*.parquet"))
if not PARQUETS:
    st.error(f"No parquets found under {ROOT}")
    st.stop()

# Build a catalogue for Streamlit selectors
meta_rows = []
for p in PARQUETS:
    stem = p.stem                         # e.g. buy_N30_theta15
    mN   = re.search(r"_N(\d+)",     stem)
    mT   = re.search(r"_theta(\d+)", stem)
    meta_rows.append({
        "path":   p,
        "week":   p.parts[-3].split("_", 1)[1],        # week_YYYY-MM-DD
        "window": p.parts[-2].split("_", 1)[1],        # window_W
        "side":   stem.split("_", 1)[0],               # buy / sell
        "N":      mN.group(1)  if mN  else "?",
        "theta":  mT.group(1) if mT else "?",
    })
meta = pd.DataFrame(meta_rows)

# -----------------------------------------------------------------------------
# Streamlit selectors (week → window → side → N → θ)
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
# Derive outcome classes and marker appearance
# -----------------------------------------------------------------------------
# 1) parse PL-limit from label tag, e.g. pl30_t0.50  →  30
pl_limit = int(re.search(r"pl(\d+)", label_tag).group(1))

# 2) boolean masks
is_dev     = df["set"] == "DEV"
no_hit_col = "no_hit" in df.columns
no_hit = df.get("no_hit", False).astype(bool)

# DEV rejects = did not pass θ
reject = (df.get("passed", True) == False) & (is_dev)

# 3) outcome class for colour mapping
df["class"] = np.where(
    no_hit,                     "no_hit",
    np.where(df["pl"] > 0,      "win",      "loss")
)

# 4) size: 1 px for TRAIN, 4 px for DEV trades (rejects get special size)
df["msize"] = np.where(is_dev, 4, 1)

colour_map = {
    "win":     "royalblue",
    "loss":    "firebrick",
    "no_hit":  "rgba(127,127,127,0.5)",
}

# -----------------------------------------------------------------------------
# Main scatter (decisive + no-hit points)
# -----------------------------------------------------------------------------
fig = px.scatter(
    df,
    x="a", y="b",
    color="class",
    color_discrete_map=colour_map,
    hover_data=["time_ms", "pl", "set", "r2", "tau", "w", "l", "d", "cv"],
    size="msize",
    size_max=4,
)

fig.update_layout(
    title=f"{side.upper()}  N={N}  θ={theta}  week {week}  window {window}",
    xaxis_title="quadratic a",
    yaxis_title="quadratic b",
    legend_title="Outcome",
    legend=dict(orientation="h", yanchor="bottom", y=1.02,
                xanchor="right", x=1),
)

# -----------------------------------------------------------------------------
# Optional DEV-reject overlay
# -----------------------------------------------------------------------------
if show_rejects and reject.any():
    fig.add_trace(
        go.Scatter(
            x=df.loc[reject, "a"], y=df.loc[reject, "b"],
            mode="markers",
            marker=dict(size=2, color="rgba(170,170,170,0.2)"),
            name="DEV reject", hoverinfo="skip",
        )
    )

st.plotly_chart(fig, use_container_width=True)
