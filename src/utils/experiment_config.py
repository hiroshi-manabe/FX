"""
Experiment-level configuration object.

Captures *all* hyper-parameters that influence stages **after
filter_digest** (k-NN grid-search → eval).  Key capabilities:

    • from_ini()        – read conf/config.ini plus hard-coded fallbacks
    • override(dict)    – apply CLI overrides *before* first run
    • freeze(exp_dir)   – write YAML + SHA-1, abort if settings differ
    • load(exp_dir)     – resume an existing experiment, hash-checked
"""

from __future__ import annotations

import configparser
import datetime
import hashlib
import json
import pathlib
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List
from utils import tag_ctx
import yaml

# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------


def _ini_path() -> pathlib.Path:
    """Return repo-local path to conf/config.ini."""
    return pathlib.Path(__file__).resolve().parents[2] / "conf" / "config.ini"


def _parse_int_list(value: Any) -> List[int]:
    """‘5,10 20’ → [5, 10, 20]."""
    if value is None:
        return []
    if isinstance(value, list):
        return [int(x) for x in value]
    parts = [p.strip() for p in str(value).replace(",", " ").split()]
    return [int(p) for p in parts if p]


# ----------------------------------------------------------------------
# dataclass
# ----------------------------------------------------------------------


@dataclass
class ExperimentConfig:
    # immutable tags (up-stream artefacts)
    label_tag: str
    feature_tag: str

    # rolling windows
    train_weeks: int
    dev_weeks: int
    test_weeks: int

    # k-NN hyper-parameters
    k: int
    Ns_week: List[int] = field(default_factory=list)
    thetas: List[int] = field(default_factory=list)
    gamma: float = 0.40
    spacing_ms: int = 80_000

    # bookkeeping
    created_at: str = field(
        default_factory=lambda: datetime.datetime.now().isoformat()
    )
    sha1: str = ""  # filled in by freeze()

    # ------------------------------------------------------------------
    # builders
    # ------------------------------------------------------------------

    @classmethod
    def from_ini(cls) -> "ExperimentConfig":
        """Populate from conf/config.ini with internal fallbacks."""
        ini = configparser.ConfigParser()
        ini.read(_ini_path(), encoding="utf-8")

        # --- fallbacks used if key missing ----------------------------
        fallback = {
            "label_tag": "pl30",
            "feature_tag": "quad_v1",
            "train_weeks": 10,
            "dev_weeks": 4,
            "test_weeks": 26,
            "k": 20,
            "Ns_week": "5,10,20,40",
            "thetas": "1,2,3,4",
            "gamma": 0.40,
            "spacing_buffer": 80_000,
        }

        p = ini["pipeline"] if "pipeline" in ini else {}
        knn = ini["knn"] if "knn" in ini else {}

        return cls(
            label_tag=tag_ctx.label_tag(),
            feature_tag=tag_ctx.feat_tag()
            train_weeks=int(knn.get("train_weeks", fallback["train_weeks"])),
            dev_weeks=int(knn.get("dev_weeks", fallback["dev_weeks"])),
            test_weeks=int(knn.get("test_weeks", fallback["test_weeks"])),
            k=int(knn.get("k", fallback["k"])),
            Ns_week=_parse_int_list(knn.get("Ns_week", fallback["Ns_week"])),
            thetas=_parse_int_list(knn.get("thetas", fallback["thetas"])),
            gamma=float(knn.get("gamma", fallback["gamma"])),
            spacing_ms=int(knn.get("spacing_buffer", fallback["spacing_buffer"])),
        )

    # ------------------------------------------------------------------
    # mutation
    # ------------------------------------------------------------------

    def override(self, overrides: Dict[str, Any]) -> "ExperimentConfig":
        """Patch values *before* freezing (only on first run)."""
        for key, val in overrides.items():
            if val is None or not hasattr(self, key):
                continue
            current = getattr(self, key)
            if isinstance(current, list):
                setattr(self, key, _parse_int_list(val))
            else:
                setattr(self, key, type(current)(val))
        return self

    # ------------------------------------------------------------------
    # (de)serialisation helpers
    # ------------------------------------------------------------------

    def _payload_json(self) -> str:
        """Return JSON dump *excluding* sha1 for deterministic hash."""
        return json.dumps(
            {k: v for k, v in self.as_dict().items() if k != "sha1"},
            sort_keys=True,
            separators=(",", ":"),
        )

    def _compute_sha1(self) -> str:
        return hashlib.sha1(self._payload_json().encode()).hexdigest()[:8]

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def freeze(self, exp_dir: str | pathlib.Path) -> None:
        """Write experiments/<name>/config.yaml.  Abort if content differs."""
        exp_dir = pathlib.Path(exp_dir)
        exp_dir.mkdir(parents=True, exist_ok=True)
        yml = exp_dir / "config.yaml"

        if not self.sha1:
            self.sha1 = self._compute_sha1()

        if yml.exists():
            loaded = ExperimentConfig.load(exp_dir)
            if loaded.sha1 != self.sha1:
                raise RuntimeError(
                    f"Experiment at {exp_dir} already exists with different settings."
                )
            return  # identical – nothing to do

        with yml.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(self.as_dict(), fh, sort_keys=False)

    # -------------

    @classmethod
    def load(cls, exp_dir: str | pathlib.Path) -> "ExperimentConfig":
        """Resume an existing experiment; validate SHA."""
        exp_dir = pathlib.Path(exp_dir)
        yml = exp_dir / "config.yaml"
        if not yml.exists():
            raise FileNotFoundError(f"No config.yaml under {exp_dir}")

        with yml.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh)

        cfg = cls(**{k: data[k] for k in data if k != "sha1"})
        cfg.sha1 = data.get("sha1", "")

        if cfg._compute_sha1() != cfg.sha1:
            raise RuntimeError(f"Hash mismatch in {yml}; file may be edited.")
        return cfg


# ----------------------------------------------------------------------
# smoke-test
# ----------------------------------------------------------------------

if __name__ == "__main__":
    import tempfile, pprint

    tmp_exp = pathlib.Path(tempfile.mkdtemp()) / "demo_exp"
    cfg = ExperimentConfig.from_ini().override({"gamma": 0.25, "k": 30})
    cfg.freeze(tmp_exp)
    print("Reloaded config:")
    pprint.pprint(ExperimentConfig.load(tmp_exp).as_dict())
