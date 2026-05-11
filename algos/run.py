import json, time
from pathlib import Path

from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.algorithms.moo.spea2 import SPEA2
from pymoo.core.mixed import MixedVariableSampling, MixedVariableMating, MixedVariableDuplicateElimination

from pymoo.optimize import minimize
from algos.problem import ClueGenProblem
from clue_pipeline.runner import sample_puzzles

# ALGO = "spea2"
ALGO = "nsga2"
# POP = 10
# GENS = 5
# PUZZLES = 5

POP = 4
GENS = 2
PUZZLES = 2

SEED = 42
GRADER_RUNS = 1

def monrp():
    puzzle_indices = sample_puzzles(PUZZLES, seed=SEED)
    
    problem = ClueGenProblem(puzzle_indices=puzzle_indices, grader_runs=GRADER_RUNS)
    
    AlgoCls = NSGA2 if ALGO == "nsga2" else SPEA2
    algorithm = AlgoCls(
        pop_size=POP,
        sampling=MixedVariableSampling(),
        mating=MixedVariableMating(eliminate_duplicates=MixedVariableDuplicateElimination()),
        eliminate_duplicates=MixedVariableDuplicateElimination(),
    )
    
    res = minimize(problem, algorithm, ("n_gen", GENS), seed=SEED, verbose=True)
    
    Path("results").mkdir(exist_ok=True)
    data = {
        "algo": ALGO,
        "pop": POP, "gens": GENS, "puzzles": puzzle_indices, "seed": SEED,
        "front": [
            {"config": dict(x), "cost": float(f[0]), "quality": float(-f[1])}
            for x, f in zip(res.X, res.F)
        ],
    }
    Path(f"results/{ALGO}_{int(time.time())}.json").write_text(json.dumps(data, indent=2))

    
    
    
if __name__ == "__main__":
    monrp()


