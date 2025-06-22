# utils/tag_ctx.py  – imported by path_utils

from utils import config, param_utils, env

def _from_env(name: str, fallback: str) -> str:
    return env.get(name.upper(), fallback)          # env helper just wraps os.getenv

def label_tag() -> str:
    return _from_env("FX_LABEL_TAG", param_utils.label_tag())

def feat_tag() -> str:
    return _from_env("FX_FEAT_TAG",
                     config.get("pipeline", "quadratic_alg_tag"))

def knn_tag() -> str:
    return _from_env("FX_KNN_TAG",
                     config.get("pipeline", "knn_alg_tag"))
