import json
import random as pyrandom
from pathlib import Path

from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.algorithms.moo.spea2 import SPEA2
from pymoo.core.callback import Callback
from pymoo.core.mixed import MixedVariableSampling, MixedVariableMating, MixedVariableDuplicateElimination
from pymoo.optimize import minimize

from algos.problem import ClueGenProblem
from clue_pipeline.generator import MODELS, PROMPT_TEMPLATES
from clue_pipeline.runner import evaluate_config, sample_puzzles


class HistoryCallback(Callback):
    def __init__(self):
        super().__init__()
        self.history = []

    def notify(self, algorithm):
        F = algorithm.pop.get("F")
        self.history.append([[float(f0), float(f1)] for f0, f1 in F])


ALGOS = ["nsga2", "spea2", "random"]
SEEDS = list(range(1, 11))
POP = 10
GENS = 5
PUZZLES = 5
PUZZLE_SEED = 42
GRADER_RUNS = 1


def _non_dominated(F):
    n = len(F)
    keep = [True] * n
    for i in range(n):
        if not keep[i]:
            continue
        for j in range(n):
            if i == j or not keep[j]:
                continue
            if (F[j][0] <= F[i][0] and F[j][1] <= F[i][1]
                    and (F[j][0] < F[i][0] or F[j][1] < F[i][1])):
                keep[i] = False
                break
    return [i for i, k in enumerate(keep) if k]


def run_pymoo(algo, seed, problem):
    AlgoCls = NSGA2 if algo == "nsga2" else SPEA2
    algorithm = AlgoCls(
        pop_size=POP,
        sampling=MixedVariableSampling(),
        mating=MixedVariableMating(eliminate_duplicates=MixedVariableDuplicateElimination()),
        eliminate_duplicates=MixedVariableDuplicateElimination(),
    )
    callback = HistoryCallback()
    res = minimize(problem, algorithm, ("n_gen", GENS), seed=seed, verbose=True, callback=callback)
    front = [
        {
            "config": {
                "model": str(x["model"]),
                "template": str(x["template"]),
                "n_clues": int(x["n_clues"]),
                "temperature": float(x["temperature"]),
            },
            "cost": float(f[0]),
            "quality": float(-f[1]),
        }
        for x, f in zip(res.X, res.F)
    ]
    return callback.history, front


def run_random(seed, puzzle_indices, grader_runs):
    rng = pyrandom.Random(seed)
    models = list(MODELS.keys())
    templates = list(PROMPT_TEMPLATES.keys())
    history = []
    all_evals = []
    for _ in range(GENS):
        gen_F = []
        for _ in range(POP):
            x = {
                "model": rng.choice(models),
                "template": rng.choice(templates),
                "n_clues": rng.randint(3, 8),
                "temperature": rng.uniform(0.0, 1.0),
            }
            cfg = f"{x['model']}/{x['template']}/n={x['n_clues']}/T={x['temperature']:.2f}"
            try:
                result = evaluate_config(
                    model=x["model"], template=x["template"],
                    n_clues=x["n_clues"], temperature=x["temperature"],
                    puzzle_indices=puzzle_indices,
                    grader_runs=grader_runs, progress=False,
                )
                F = [float(result.mean_gen_cost), float(-result.mean_quality)]
                print(f"[eval] {cfg} -> cost=${result.mean_gen_cost:.5f} q={result.mean_quality:.2f}", flush=True)
            except Exception as e:
                print(f"[eval failed] {cfg} -> {type(e).__name__}: {e}", flush=True)
                F = [1.0, 0.0]
            gen_F.append(F)
            all_evals.append((x, F))
        history.append(gen_F)

    F_all = [F for _, F in all_evals]
    nd_idx = _non_dominated(F_all)
    front = [
        {
            "config": {
                "model": all_evals[i][0]["model"],
                "template": all_evals[i][0]["template"],
                "n_clues": all_evals[i][0]["n_clues"],
                "temperature": all_evals[i][0]["temperature"],
            },
            "cost": all_evals[i][1][0],
            "quality": -all_evals[i][1][1],
        }
        for i in nd_idx
    ]
    return history, front


def monrp():
    puzzle_indices = sample_puzzles(PUZZLES, seed=PUZZLE_SEED)
    problem = ClueGenProblem(puzzle_indices=puzzle_indices, grader_runs=GRADER_RUNS)
    Path("results").mkdir(exist_ok=True)

    for algo in ALGOS:
        for seed in SEEDS:
            out_path = Path(f"results/{algo}_seed{seed:02d}.json")
            if out_path.exists():
                print(f"[skip] {out_path.name} already exists")
                continue
            print(f"\n=== {algo} seed={seed} ===")
            if algo == "random":
                history, front = run_random(seed, puzzle_indices, GRADER_RUNS)
            else:
                history, front = run_pymoo(algo, seed, problem)
            data = {
                "algo": algo,
                "seed": seed,
                "pop": POP,
                "gens": GENS,
                "puzzles": puzzle_indices,
                "puzzle_seed": PUZZLE_SEED,
                "history": history,
                "front": front,
            }
            out_path.write_text(json.dumps(data, indent=2))
            print(f"saved -> {out_path}")


if __name__ == "__main__":
    monrp()
