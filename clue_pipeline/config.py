import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

PUZZLES_PATH = PROJECT_ROOT / "puzzles.xlsx"


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} not found")
    return value


def groq_api_key() -> str:
    return _require("GROQ_API_KEY")


def anthropic_api_key() -> str:
    return _require("ANTHROPIC_API_KEY")
