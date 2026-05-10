import pandas as pd

from .config import PUZZLES_PATH


def load_puzzles():
    return pd.read_excel(PUZZLES_PATH)
