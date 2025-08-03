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

──────────────────────────────────────────────────────────────
PURPOSE
A tick‑level research pipeline that discovers simple, mechanically
exploitable patterns in USDJPY by fitting quadratic curves to short
price windows and classifying the (a,b) coefficients with a rolling
k‑nearest‑neighbour model.  No deep learning, no chart watching – just
clean data, small heuristics, and strict train/dev/test discipline.

KEY FEATURES

Works directly on Dukascopy tick data (bid/ask, ~5–6 pips spread).

Three‑way exit logic – take‑profit, stop‑loss, or time‑out.

Sliding TRAIN‑DEV‑TEST windows (any T, D, E) for causal evaluation.

Fast C++ label‑generation and Python KD‑tree grid‑search (multiprocess).

Fully tag‑based directory layout → reproducible & incremental.

Streamlit visualisers: parameter heat‑maps, scatter plots with
decisive / no‑hit / γ‑reject layers.

──────────────────────────────────────────────────────────────
2 · MOTIVATION & PHILOSOPHY

* Data‑First Curiosity Foreign‑exchange ticks are abundant, cheap and
a pure numerical playground.  Dollar‑yen attracts a huge retail crowd;
their behavioural bias leaves exploitable micro‑patterns.

* Simplicity over Opacity Instead of deep nets we use two transparent
building blocks: a quadratic least‑squares fit (three numbers) and a
k‑nearest‑neighbour vote.  Every decision can be plotted and traced.

* Hobby, not HFT No hard SLA, no latency arms‑race.  Objectives:
– learn the market’s texture;
– build a causal, reproducible back‑test;
– graduate to demo trading only if the equity curve survives realistic
slippage & spread.

* Safety Rails Work only on historical data until the demo account is
consistently profitable.  Keep position sizing capped by Kelly edge &
time‑limited exits.

* Iterate Scientifically Each code stage writes immutable artefacts with
a versioned tag.  Change one parameter ➜ rebuild downstream ➜ compare
metrics.  This encourages disciplined experimentation instead of a
parameter bingo.

(End of section 2)
──────────────────────────────────────────────────────────────
3 · HIGH-LEVEL PIPELINE OVERVIEW

Stage → Output directory (relative to data/) → What it produces

1  download_raw   → raw/dukascopy/PAIR/DATE/HHh_ticks.bi5
   • Exact Dukascopy ticks, 1-hour compressed chunks.

2  bin_to_csv     → raw/dukascopy/PAIR/DATE/HHh_ticks.bin, *.csv
   • Decompress .bi5 to binary → CSV preview for inspection.

3  weekify        → weekly/PAIR/week_DATE.csv
   • 1 Hz midpoint & spread snapshot for quick charts.

4  label_pl       → labels/L/PAIR/window_W/week_DATE.csv
   • Append buyPL, sellPL, no_hit using ±PL-limit and time-limit rules.

5  fit_quadratic  → features/L/F/PAIR/window_W/week_DATE.csv
   • OLS quadratic fit on log-price window → a, bc, , r² per tick.

6  filter_digest  → digest/L/F/PAIR/window_W/week_DATE.csv
   • Drop rows with r² < r2_floor (no spacing yet).

7  knn_gridsearch → knn/grids|trades|viz/L/F/K/...
   • For each DEV week:
     – τ binary search to get ~N trades
     – Apply spacing, KD-tree k-NN
     – Apply γ (cv) and θ (edge) thresholds
     – Save:
       ▫ grids (npy tensor)
       ▫ trades (executed parquet)
       ▫ viz (all DEV rows + w/d/l/cv)

8  select_params  → knn/params/L/F/K/week_DATE.json
   • DEV t-stat selection → best N, θ, τ, side.

9  knn_eval       → eval/knn_v2/live/PAIR/week_DATE.csv
   • Apply param cell to TEST grid; no replay needed.

(End of section 3)
──────────────────────────────────────────────────────────────
4 · DIRECTORY & TAG CONVENTION

Three tag folders appear only after the labelling stage:
<LABEL_TAG> / <FEAT_TAG> / <KNN_TAG>

raw tick source
raw/dukascopy/PAIR/DATE/HHh_ticks.bi5  (plus .bin .csv previews)

weekly snapshot
weekly/PAIR/week_DATE.csv

labelled ticks (PL rules only)
labels/L/PAIR/window_W/week_DATE.csv

r²‑filtered digest (still dense)
digest/L/F/PAIR/window_W/week_DATE.csv

quadratic features
features/L/F/PAIR/window_W/week_DATE.csv

k‑NN outputs (same tag triplet)
knn/grids/L/F/K/PAIR/window_W/week_DATE.npy        – summary tensor
knn/trades/L/F/K/PAIR/window_W/week_DATE/…parquet  – executed trades
knn/viz/L/F/K/PAIR/window_W/week_DATE/…parquet     – all DEV rows
knn/params/PAIR/week_DATE.json                     – chosen parameters

eval equity
eval/knn_v2/live/PAIR/week_DATE.csv

(End of section 4)

─────────────────
5 · STAGE-BY-STAGE SPECIFICATION
(Inputs → Algorithm → Key params → Outputs → Failure notes)
All paths are relative to data/ and include L/F/K tags when applicable.

5.1 download_raw
• Inputs    : Dukascopy HTTP endpoints; pair list from config.ini.
• Algorithm : stream-download .bi5 files; rename as HHh_ticks.bi5.
• Params    : pairs, date_from, date_to, parallel=6, force
• Outputs   : raw/dukascopy/PAIR/DATE/HHh_ticks.bi5
• Errors    : 404s are skipped with warnings; checksum mismatch aborts.

5.2 bin_to_csv
• Inputs    : raw/dukascopy/.../*.bi5
• Algorithm : decompress to .bin, convert to .csv (same base name).
• Params    : none (conversion is full and deterministic)
• Outputs   : raw/dukascopy/PAIR/DATE/HHh_ticks.{bin,csv}
• Errors    : corrupted bi5 → file skipped; invalid decode triggers warning.

5.3 weekify
• Inputs    : raw .csv files (per-hour tick data).
• Algorithm : concatenate, sort, resample to 1 Hz midpoint & spread.
• Params    : none (UTC timestamps; weeks end Fri 17:00 NY time).
• Outputs   : weekly/PAIR/week_DATE.csv
• Errors    : missing hour → row of NaNs; warnings logged.

5.4 label_pl
• Inputs    : weekly csv + per-tick .bin data for simulating exits.
• Algorithm : compute P/L at ±pl_limit within time_limit (ratio×window).
Mark row as no_hit if neither hit occurs in time.
• Params    : pl_limit (pips), time_ratio (fractional duration)
• Outputs   : labels/L/PAIR/window_W/week_DATE.csv
• Errors    : all future ticks unreachable → no_hit flagged

5.5 fit_quadratic
• Inputs    : labels csv
• Algorithm : fit quadratic (a,b,r²) on bid/ask log prices over window W.
• Params    : window list from config
• Outputs   : features/L/F/PAIR/window_W/week_DATE.csv
• Errors    : insufficient data or degenerate fit → row dropped

5.6 filter_digest
• Inputs    : feature csv (5.5)
• Algorithm : retain only rows with r² ≥ r2_floor (per window).
No spacing at this stage.
• Params    : r2_floor (thresholds from config)
• Outputs   : digest/L/F/PAIR/window_W/week_DATE.csv
• Errors    : no rows survive → file skipped, caller warned

5.7 knn_gridsearch
• Inputs    : features (TRAIN), labels (DEV)
• Algorithm : binary search τ to get ~N trades/week; apply spacing;
build KD-tree; compute w/l/d, edge, cv; reject if cv > gamma or |edge| < θ.
• Params    : k, Ns_week, theta_list, gamma, spacing_ms
• Outputs   : knn/grids/...npy, knn/trades/...parquet, knn/viz/...parquet
• Errors    : not enough training points → window skipped

5.8 select_params
• Inputs    : last D grid files
• Algorithm : pick (N*, θ*, τ*, side) via weighted t-statistic
• Params    : dev_weeks, min_trades, trade-weighted scoring
• Outputs   : knn/params/.../week_DATE.json
• Errors    : no valid cells → no param file

5.9 knn_eval
• Inputs    : TEST grids, params JSON, trade logs
• Algorithm : read optimal cell, evaluate trades and aggregate PnL
• Params    : none (frozen once selected)
• Outputs   : eval/knn_v2/live/PAIR/week_DATE.csv
• Errors    : missing grid → week skipped

(End of section 5)

6 · K-N N MODEL DETAILS  (updated)

Feature space
  • Vector = (a, b) obtained from quadratic fit
        p(t) ≈ a·t² + b·t + c
    Why is c ignored?  The window is anchored so that t = 0 is the
    decision tick; for any *good* fit the curve must pass close to that
    origin, hence |c| is small and mostly measures noise.  We still use
    |c| as a quick-and-dirty quality filter upstream, but not as a k-NN
    feature.

  • Per-week z-score scaling of a and b:
        a′ = (a − μ_a)/σ_a ,  b′ = (b − μ_b)/σ_b
    KD-trees therefore share a roughly spherical space regardless of
    volatility shifts.

Distance & neighbour search
  • Euclidean distance in (a′, b′) space.
  • KD-tree built once per TRAIN slice, independently for BUY and SELL.
  • k (neighbour count) read from `config.ini`.

Statistics returned by `KNNModel.scores(point)`
  w  – neighbours with PL  > 0               (“wins”)
  d  – neighbours with PL == 0 *and* no_hit = 0 (“draws”—hit limit but flat)
  l  – neighbours with PL  < 0               (“losses”)
  nh – neighbours with no_hit = 1            (±PL limit not reached)
  edge = (w − l) / (w + d + l + nh)          ∈ [−1,+1]  
  cv   = σ(dist) / μ(dist)                   local coefficient of variation

`no_hit` in detail
  A tick becomes *no_hit* when neither +PL_LIMIT nor –PL_LIMIT is touched
  before TIME_LIMIT expires (TIME_LIMIT = time_ratio × window length).
  • These rows still feed the KD-tree: their PL is whatever the price did
    at timeout (can be small win, loss or zero).  
  • They are counted separately (nh) so that γ and θ tuning can decide
    whether to tolerate or reject regions with frequent stalemates.

Decision filters inside grid-search (DEV phase)
  1. γ-filter  → reject the query if cv > gamma  
     guards against “edge-of-cluster” queries with a highly uneven
     neighbour shell.
  2. θ-filter  → trade only if |edge| ≥ θ  
     θ is grid-searched jointly with N; when draws / no_hits are present
     the optimal θ need not be an even integer.

Outputs stored for visualisation
  For every DEV tick the viz parquet records:
    time_ms, a, b, r2, pl, no_hit,
    w, d, l, nh, edge,
    passed_hull, passed_theta, passed (final trade flag)

(End of section 6)

7 · EVALUATION METHODOLOGY
(The “rolling TRAIN-DEV-TEST” logic that often causes off-by-one errors)

Notation
  T  = TRAIN length  (weeks used to build KD-tree + τ search)  
  D  = DEV length    (weeks used to score parameter grid)  
  E  = TEST horizon  (weeks we actually report)  
  k  = calendar week index (Monday label)  
  grid k = full (N, θ, side) table simulated on week k  

One-time grid build  (front-loaded, causal)
  FOR k = (T+1) .. (T + D + E) inclusive
      TRAIN weeks = [k-T .. k-1]       (length T)
      DEV week    = k                  (single week)
      → build KD-tree on TRAIN rows
      → run KD-queries on *that* DEV week for every (N, θ)
      → save grids/.../week_k/...npy  (+ optional trades & viz)

      *Important*: grid k already contains the realised trade outcomes
      of calendar week k; it never looks into the future.

Parameter selection for each TEST week
  A TEST week starts only after we have at least D completed DEV grids.

  For TEST Monday k (k ≥ T + D):
      DEV set   = { grid(k-D), grid(k-D+1), … , grid(k-1) }   # D files
      score(N,θ) = weighted-t-statistic over those D cells  
                   (weight √trades to favour dense weeks)
      choose (N*, θ*, τ*, side*) = arg-max score
      → write knn/params/…/week_k.json

No recomputation for TEST
  TEST week k simply **reads** the chosen cell inside *grid k*:
      cell  = grids[side*][N_idx*, θ_idx*]
      trades = int(cell[0])
      mean   = cell[1]
      weekly PnL = trades × mean
      τ*     = cell[4]   (duplicated for completeness)

  If Kelly or path-risk is required, load the exact trade Parquet from
  knn/trades/…/week_k/ and replay in timestamp order; still no KD-tree
  rebuild or tick-stream seek is needed.

Example with T = D = 2, E = 2
  Weeks:   1  2 | 3  4 | 5  6
             └T┘   └ DEV 3 ┘      → grid 3
              2  3 | 4  5 |
                 └T┘   └ DEV 4 ┘  → grid 4
              3  4 | 5  6 |
                 └T┘   └ DEV 5 ┘  → grid 5
  Parameter for TEST 5  = best over grids 3 & 4
  TEST 5 PnL            = cell (N*,θ*) inside grid 5
  Parameter for TEST 6  = best over grids 4 & 5
  TEST 6 PnL            = cell (N*,θ*) inside grid 6

Aggregation metrics
  • Weekly equity curve = cumulative sum of weekly PnL.  
  • Sharpe ratio        = mean(PnL) / stdev(PnL) over E weeks.  
  • Optional drawback   = max equity peak – next trough (CSV column).

Common pitfalls
  ✗ Re-running KD-trees for DEV or TEST (wastes hours, may leak future).  
  ✗ Using DEV rows of week k in DEV set for week k (off-by-one).  
  ✗ Forgetting γ or θ thresholds when summing edge in DEV scoring.

Mental mantra  
    “Grid k simulates week k; TEST k just reads one cell from grid k.”

(End of section 7)

8 · VISUALISATION TOOLS  (updated logic for PL / no-hit colouring)

Two Streamlit apps live in src/viz/ and consume only the parquet files
written by knn_gridsearch.  They never touch raw ticks.

8.1 knn_scatter.py   – “a-b space” microscope
———————————————————————————————————————
Inputs
  • Folder pickers: LABEL_TAG, FEATURE_TAG, KNN_TAG, Pair, Window, Week
    (+ N, θ, Side) parsed from path_utils.
  • Parquet: knn/viz/L/F/K/PAIR/window_W/week_DATE/side_N*_θ*.parquet

Visual encoding
  SIZE  → dataset
      small point  = TRAIN row
      large point  = DEV row
  COLOUR → outcome at PL_LIMIT / TIME_LIMIT
      blue   = +PL_LIMIT hit    (win)
      red    = –PL_LIMIT hit    (loss)
      grey   = no_hit timeout   (trade exited at TIME_LIMIT)

Layers
  ▸ TRAIN (blue / grey / red)        small dots  
  ▸ DEV   (blue / grey / red)        large dots  
  ▸ DEV rejected (failed γ or θ)     large ✕ markers (optional)

Additional widgets
  • θ slider (match grid-search values).  
  • “Show rejection reasons” overlays cv, edge on hover.  
  • Plotly native zoom & selection.

8.2 grid_heat.py   – parameter surface explorer
———————————————————————————————————————
Inputs
  • Same tag pickers + Pair, Window, Week.
  • Tensor from knn/grids/…/window_W/week_DATE.npy.

Display
  • Heat-map of mean P/L, t-stat, or trades (select box).  
  • Hatched cells where trades < MIN_TRADES.  
  • Right panel shows τ, trades, w/d/l/nh counts of hovered cell.  
  • Colour bar fixed to ±PL_LIMIT so weeks are comparable.

8.3 launch_viz.sh convenience script
————————————————
#!/bin/bash
export FX_LABEL_TAG=pl30
export FX_FEAT_TAG=quad_v1
export FX_KNN_TAG=knn_g0.40
streamlit run src/viz/knn_scatter.py &
streamlit run src/viz/grid_heat.py &


8.4 Typical workflow
————————
1. Run the pipeline up to **knn_gridsearch**.  
2. Open **grid_heat**; locate promising (N, θ) cells.  
3. Copy the path button → paste into **knn_scatter**.  
4. Inspect neighbour cloud; adjust γ / θ if DEV greys dominate.  
5. Re-run only grid & eval stages after parameter tweaks.

8.5 Maintenance notes
————————
* Tag folders resolved via path_utils → changing tags only requires  
  `export FX_LABEL_TAG=…`, etc.  
* The parquet schema is read at runtime; adding new columns (e.g. edge,
  cv) needs no code change unless you want to colour by them.

(End of section 8)

9 · CONFIGURATION GUIDE
————————
[pipeline] – global run-time defaults
currency_pair = USDJPY # default pair when CLI omits --pair
weeks_default = 80 # fallback for --weeks
windows = 10000,20000,40000,80000,160000 # ms tick windows
pl_limit = 30 # ±pips hit-test in label_pl
spread_delta = 2 # extra pips subtracted on exits
time_ratio = 0.50 # TIME_LIMIT = time_ratio × window
default_time_limit = 60000 # ms when time_ratio is blank

These keys are read by label_pl, param_utils, and echoed downstream.
————————
[digest] – quality / density gates before k-NN
r2_threshold = 0.20
min_abs_a = 0.0 max_abs_a = 4.0
min_abs_b = 0.0 max_abs_b = 4.0
max_abs_c = 2.0
max_ms_per_tick = 250 # sparsity guard

Only filter_digest.py consumes this block.
————————
[knn] – sliding-window back-test and k-NN hyper-params
train_weeks = 10 # T
dev_weeks = 4 # D
test_weeks = 26 # E
k = 20 # neighbours in KD-tree
spacing_buffer = 200 # ms trade-spacing
Ns_week = 5,10,20,40 # rows per TRAIN week
thetas = 1,2,3,4 # edge thresholds
gamma = 0.40 # CV rejection
min_trades_dev = 5 # DEV cell must have ≥ this many trades

Used by knn_gridsearch → echoed by select_params and knn_eval.
————————
Environment overrides (checked first, then config.ini)
FX_WINDOWS comma list, shadows [pipeline] windows
FX_GAMMA single float, shadows [knn] gamma
FX_THETAS comma list, shadows [knn] thetas
FX_NS_WEEK comma list, shadows [knn] Ns_week
FX_LABEL_TAG / FX_FEAT_TAG / FX_KNN_TAG force folder tags in all stages
————————
Example:
FX_GAMMA=0.30 FX_WINDOWS=20000,40000 python run_pipeline.py --start knn_gridsearch
————————
CLI flags present in every stage
--pair PAIR overrides currency_pair
--weeks N overrides weeks_default
--force rebuild even if output exists

Stage-specific flags are documented in their module help.

Sanity checklist after editing config or env vars

run_pipeline.py --start knn_gridsearch --force

run_pipeline.py --start select_params

run_pipeline.py --start knn_eval

Each step aborts with a clear error if a required grid, param or trade
file is missing.

(End of section 9)

10 · RUNNING THE FULL PIPELINE
(A quick-start “cookbook” for a fresh workstation)

------------------------------------------------------------
0.  Prerequisites
    • Python ≥ 3.10  (pandas, numpy, numba, pyarrow, scikit-learn,
      streamlit).  requirements.txt is provided.
    • Disk:  ≈10 GB per month of tick data per pair.
    • CPU:   8+ cores recommended for grid-search; RAM ≈8 GB is enough.

------------------------------------------------------------
1.  Clone and set up
    git clone https://github.com/hiroshi-manabe/FX.git
    cd FX
    python -m venv .venv
    . .venv/bin/activate
    pip install -r requirements.txt

------------------------------------------------------------
2.  Configure
    • Edit config.ini for windows, pl_limit, gamma, etc.
    • Or override temporarily:
        export FX_GAMMA=0.30
        export FX_KNN_TAG=knn_g0.30

------------------------------------------------------------
3.  Download raw Dukascopy ticks
    python src/pipeline/run_pipeline.py --start download_raw \
           --pair USDJPY --weeks 80 --jobs 8

------------------------------------------------------------
4.  Weekly snapshots and labels
    python src/pipeline/run_pipeline.py --start weekify  --weeks 80
    python src/pipeline/run_pipeline.py --start label_pl --weeks 80

------------------------------------------------------------
5.  Fit quadratics → digest → k-NN grid-search
    python src/pipeline/run_pipeline.py --start fit_quadratic  --weeks 80
    python src/pipeline/run_pipeline.py --start knn_gridsearch \
           --weeks 80 --jobs 6

------------------------------------------------------------
6.  Select parameters from DEV windows
    python src/pipeline/run_pipeline.py --start select_params --weeks 80

------------------------------------------------------------
7.  Evaluate TEST weeks
    python src/pipeline/run_pipeline.py --start knn_eval --weeks 80

------------------------------------------------------------
8.  Visual inspection (optional)
    streamlit run src/viz/grid_heat.py   &
    streamlit run src/viz/knn_scatter.py &

------------------------------------------------------------
9.  Incremental rebuild guide
    • Change γ or θ       → gridsearch → select_params → knn_eval
    • Change pl_limit     → label_pl   → … → knn_eval
    • Add/remove windows  → fit_quadratic → … → knn_eval
    Use --force to overwrite outdated outputs.

------------------------------------------------------------
10.  Common pitfalls
    • Forgot to bump FX_KNN_TAG after gamma change  → old grids reused.
    • Mixed --weeks horizons between stages        → select_params fails.
    • Ran knn_eval before select_params            → manifest missing.

------------------------------------------------------------
Typical runtime (6-core laptop, one pair, 80 weeks)
    download_raw            ~6  min
    weekify + label_pl      ~3  min
    fit_quadratic + digest  ~4  min
    knn_gridsearch          ~40 min
    select_params           <1  sec
    knn_eval                <1  sec
    --------------------------------
    TOTAL                   ~53 min

(End of section 10)
