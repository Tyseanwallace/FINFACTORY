import os, tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass


def load():
    with open(ROOT / "config.toml", "rb") as f:
        cfg = tomllib.load(f)
    cfg["root"] = ROOT
    return cfg


def playbook() -> str:
    """The content rules every script must follow (PLAYBOOK.md)."""
    return (ROOT / "PLAYBOOK.md").read_text(encoding="utf-8")
