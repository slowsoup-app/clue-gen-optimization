import argparse, json, time
from pathlib import Path

from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.algorithms.moo.spea2 import SPEA2
from pymoo.core.mixed import MixedVariableSampling, MixedVariableMating, MixedVariableDuplicateElimination

from pymoo.optimize import minimize
from algos.problem import ClueGenProblem
from clue_pipeline.runner import sample_puzzles

def monrp(*args):
    puzzle_indices = sample_puzzles(args.puzzles, seed=args.seed)
    
    problem = ClueGenProblem(puzzle_indices=puzzle_indices, grader_runs=args.grader_runs)
    
    AlgoCls = NSGA2 if args.algo == "nsga2" else SPEA2
    algorithm = AlgoCls(
        pop_size=args.pop,
        sampling=MixedVariableSampling(),
        mating=MixedVariableMating(eliminate_duplicates=MixedVariableDuplicateElimination()),
        eliminate_duplicates=MixedVariableDuplicateElimination(),
    )
    
    res = minimize(problem, algorithm, ("n_gen", args.gens), seed=args.seed, verbose=True)
    
    
    
if __name__ == "__main__":
    monrp()


