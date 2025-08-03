#!/usr/bin/env python3
"""
exp_runner.py  – experiment-level driver for k-NN stages

Usage examples
--------------

# create new experiment "k30" with an override, run grid-search
python -m pipeline.exp_runner --exp k30 \
        --k 30 \
        --start knn_gridsearch --pair USDJPY --weeks 80

# resume the same experiment, run select_params
python -m pipeline.exp_runner --exp k30 --start select_params
"""

from __future__ import annotations

import argparse
import importlib
import os
import subprocess
import sys
sys.path.append(Path(__file__).resolve().parents[1])   # add src/ to PYTHONPATH
from pathlib import Path
from typing import Dict, List, Tuple

from utils.experiment_config import ExperimentConfig
from utils.path_utils import exp_root

# ----------------------------------------------------------------------
STAGE_TO_MODULE: Dict[str, str] = {
    "knn_gridsearch": "pipeline.knn_gridsearch",
    "select_params":  "pipeline.select_params",
    "knn_eval":       "pipeline.knn_eval",
}

# CLI flags that *belong to the driver itself* and should not be treated
# as experiment overrides
_DRIVER_KEYS = {
    "exp", "start", "dry_run", "edit_config", "pair",
    "weeks", "jobs", "force", "debug",
}

# ----------------------------------------------------------------------


def _parse_cli(argv: List[str] | None = None) -> Tuple[argparse.Namespace, Dict[str, str]]:
    """Return (known_args, override_dict)."""
    ap = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument("--exp", help="experiment name (directory)")
    ap.add_argument("--start", choices=list(STAGE_TO_MODULE),
                    help="stage to run")
    ap.add_argument("--clone", nargs=2, metavar=("SRC", "DST"),
                    help="clone experiments/SRC -> experiments/DST and exit")
    
    # common passthrough flags for legacy stage CLIs --------------------
    ap.add_argument("--pair",  default="USDJPY")
    ap.add_argument("--weeks", type=int,  default=80)
    ap.add_argument("--jobs",  type=int,  default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--debug", action="store_true")
    # meta
    ap.add_argument("--dry-run",      action="store_true",
                    help="print what would be executed, then exit")
    ap.add_argument("--edit-config",  action="store_true",
                    help="allow overwriting existing config.yaml "
                         "(DANGEROUS – use with care)")
    # accept *any* extra --key value or --flag --------------------------
    known, unknown = ap.parse_known_args(argv)

    overrides = {}
    i = 0
    while i < len(unknown):
        key = unknown[i]
        if not key.startswith("--"):
            raise SystemExit(f"Unknown positional arg {key!r}")
        if i + 1 < len(unknown) and not unknown[i + 1].startswith("--"):
            overrides[key.lstrip("-")] = unknown[i + 1]
            i += 2
        else:                         # flag with no value
            overrides[key.lstrip("-")] = "true"
            i += 1
    return known, overrides


def _ensure_config(exp_dir: Path,
                   overrides: Dict[str, str],
                   allow_edit: bool) -> ExperimentConfig:
    """Create (if new) or load existing config.yaml."""
    if exp_dir.exists():
        cfg = ExperimentConfig.load(exp_dir, allow_dirty=allow_edit)
        if allow_edit:
            if overrides:
                cfg.override(overrides)
            cfg.freeze(exp_dir, overwrite=True)          # << always re-hash
            print(f"[exp_runner] config updated (new sha {cfg.sha1})")
        elif overrides:
            print("[exp_runner] Note: experiment exists; CLI overrides ignored.")
        return cfg

    cfg = ExperimentConfig.from_ini().override(overrides)
    cfg.freeze(exp_dir)
    print(f"[exp_runner] new experiment → {exp_dir}  (sha1 {cfg.sha1})")
    return cfg


def _as_cli_args(ns: argparse.Namespace) -> List[str]:
    """Translate driver namespace into argv for legacy stage scripts."""
    out: List[str] = []
    for k, v in vars(ns).items():
        if k in _DRIVER_KEYS and v is not None:
            if isinstance(v, bool):
                if v:                 # include flag only if True
                    out.append(f"--{k.replace('_','-')}")
            else:
                out += [f"--{k.replace('_','-')}", str(v)]
    return out


def _call_legacy_stage(module_name: str,
                       stage_args: List[str]) -> int:
    """Spawn `python -m module_name …`.  Returns exit code."""
    cmd = [sys.executable, "-m", module_name] + stage_args
    return subprocess.call(cmd)


def main(argv: List[str] | None = None):
    ns, overrides = _parse_cli(argv)

    # ---- clone-only mode -------------------------------------------
    if ns.clone:
        src, dst = ns.clone
        src_dir, dst_dir = exp_root(src), exp_root(dst)
        if dst_dir.exists():
            sys.exit(f"[clone] Destination {dst} already exists.")
        import shutil
        shutil.copytree(src_dir, dst_dir)
        cfg = ExperimentConfig.load(dst_dir)     # recompute SHA
        cfg.freeze(dst_dir, overwrite=True)
        print(f"[clone] Copied {src} ➜ {dst}.  Now edit config.yaml as needed.")
        return

    if not ns.exp or not ns.start:
        sys.exit("Either use --clone or provide both --exp and --start")

    exp_dir = exp_root(ns.exp)

    cfg = _ensure_config(exp_dir, overrides, ns.edit_config)

    if ns.dry_run:
        print("[exp_runner] dry-run only")
        return

    module_name = STAGE_TO_MODULE[ns.start]
    try:
        mod = importlib.import_module(module_name)
    except ModuleNotFoundError as e:
        sys.exit(f"[exp_runner] cannot import {module_name}: {e}")

    # Prefer an in-process entry point once the stage is refactored
    if hasattr(mod, "exp_main"):
        exit_code = mod.exp_main(cfg, exp_dir, ns)
        sys.exit(exit_code if isinstance(exit_code, int) else 0)

    # Fallback: call legacy CLI (writes to data/knn, will be removed in Step 4)
    print(f"[exp_runner] stage {ns.start} has no exp_main yet – "
          "calling legacy CLI")
    stage_args = _as_cli_args(ns)
    sys.exit(_call_legacy_stage(module_name, stage_args))


# ----------------------------------------------------------------------
if __name__ == "__main__":
    main()
