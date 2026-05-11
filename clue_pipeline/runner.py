import hashlib
import json
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path

from .config import PROJECT_ROOT
from .data import load_puzzles
from .generator import generate_clues
from .grader import DEFAULT_GRADER_MODEL, grade_clues


CACHE_DIR = PROJECT_ROOT / "cache" / "evaluations"


@dataclass
class PuzzleEval:
    puzzle_idx: int
    title: str
    clues: list[str]
    non_revelation: float
    coverage: float
    quality: float
    gen_cost: float


@dataclass
class ConfigEval:
    config: dict
    puzzle_indices: list[int]
    mean_gen_cost: float
    mean_quality: float
    mean_non_revelation: float
    mean_coverage: float
    per_puzzle: list[PuzzleEval]


def sample_puzzles(n: int, seed: int = 42) -> list[int]:
    df = load_puzzles()
    return df.sample(n=n, random_state=seed).index.tolist()


def _config_key(config: dict, puzzle_indices: list[int]) -> str:
    payload = {**config, "puzzle_indices": sorted(puzzle_indices)}
    return json.dumps(payload, sort_keys=True)


def _cache_path(key: str) -> Path:
    h = hashlib.sha256(key.encode()).hexdigest()[:16]
    return CACHE_DIR / f"{h}.json"


def evaluate_config(
    *,
    model: str,
    template: str,
    n_clues: int,
    temperature: float,
    puzzle_indices: list[int],
    grader_model: str = DEFAULT_GRADER_MODEL,
    grader_runs: int = 1,
    use_cache: bool = True,
    progress: bool = True,
) -> ConfigEval:
    config = {
        "model": model,
        "template": template,
        "n_clues": int(n_clues),
        "temperature": round(float(temperature), 4),
        "grader_model": grader_model,
        "grader_runs": grader_runs,
    }
    key = _config_key(config, puzzle_indices)
    cache_file = _cache_path(key)

    if use_cache and cache_file.exists():
        data = json.loads(cache_file.read_text())
        per_puzzle = [PuzzleEval(**p) for p in data["per_puzzle"]]
        return ConfigEval(
            config=data["config"],
            puzzle_indices=data["puzzle_indices"],
            mean_gen_cost=data["mean_gen_cost"],
            mean_quality=data["mean_quality"],
            mean_non_revelation=data["mean_non_revelation"],
            mean_coverage=data["mean_coverage"],
            per_puzzle=per_puzzle,
        )

    df = load_puzzles()
    per_puzzle: list[PuzzleEval] = []
    for i, idx in enumerate(puzzle_indices, 1):
        row = df.iloc[idx]
        if progress:
            print(f"  [{i}/{len(puzzle_indices)}] puzzle {idx}: {row['title']!r}", flush=True)

        gen = generate_clues(
            title=row["title"], story=row["story"], answer=row["answer"],
            model=model, n_clues=int(n_clues),
            temperature=float(temperature), template=template,
        )
        grade = grade_clues(
            title=row["title"], story=row["story"], answer=row["answer"],
            clues=gen.clues, model=grader_model, n_runs=grader_runs,
        )
        per_puzzle.append(PuzzleEval(
            puzzle_idx=int(idx),
            title=row["title"],
            clues=gen.clues,
            non_revelation=grade.avg_non_revelation,
            coverage=grade.avg_coverage,
            quality=grade.avg_quality,
            gen_cost=gen.cost_usd,
        ))

    result = ConfigEval(
        config=config,
        puzzle_indices=list(puzzle_indices),
        mean_gen_cost=statistics.mean(p.gen_cost for p in per_puzzle),
        mean_quality=statistics.mean(p.quality for p in per_puzzle),
        mean_non_revelation=statistics.mean(p.non_revelation for p in per_puzzle),
        mean_coverage=statistics.mean(p.coverage for p in per_puzzle),
        per_puzzle=per_puzzle,
    )

    if use_cache:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(asdict(result), indent=2))

    return result
