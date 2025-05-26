import configparser, pathlib

_cfg = configparser.ConfigParser(inline_comment_prefixes=(";",))
_cfg.read(pathlib.Path(__file__).parents[2] / "conf" / "config.ini")

def _cast(value: str, typ):
    return typ(value) if typ is not str else value

def get(section: str, key: str, typ=str):
    return _cast(_cfg[section][key], typ)

def getlist(section: str, key: str, typ=str):
    return [_cast(x.strip(), typ) for x in _cfg[section][key].split(",")]
