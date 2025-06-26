# utils/env.py
import os, json, ast, pathlib

def get(name: str, default=None):
    """
    Return an environment variable, converted to Python types when possible.

    • "42"  → 42
    • "3.14"→ 3.14
    • "true"/"false" (case-ins.) → bool
    • JSON literals ("[1,2]","{\"a\":1}") are parsed.
    Anything else stays as a plain str.
    """
    raw = os.getenv(name)
    if raw is None:
        return default
    lo = raw.lower()
    if lo in {"true", "false"}:
        return lo == "true"
    for cast in (int, float):
        try:
            return cast(raw)
        except ValueError:
            pass
    try:                       # JSON or Python literal
        return json.loads(raw)
    except Exception:
        try:
            return ast.literal_eval(raw)
        except Exception:
            return raw         # fallback: str
