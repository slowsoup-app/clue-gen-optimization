from pymoo.core.problem import ElementwiseProblem
from pymoo.core.variable import Choice, Integer, Real

from clue_pipeline.generator import MODELS, PROMPT_TEMPLATES
from clue_pipeline.grader import DEFAULT_GRADER_MODEL
from clue_pipeline.runner import evaluate_config


class ClueGenProblem(ElementwiseProblem):
    """minimize generation cost, maximize quality.
    """

    def __init__(
        self,
        puzzle_indices: list[int],
        grader_model: str = DEFAULT_GRADER_MODEL,
        grader_runs: int = 1,
        n_clues_bounds: tuple[int, int] = (3, 8),
        temperature_bounds: tuple[float, float] = (0.0, 1.0),
    ):
        vars = {
            "model": Choice(options=list(MODELS.keys())),
            "template": Choice(options=list(PROMPT_TEMPLATES.keys())),
            "n_clues": Integer(bounds=n_clues_bounds),
            "temperature": Real(bounds=temperature_bounds),
        }
        super().__init__(vars=vars, n_obj=2, n_ieq_constr=0)
        self.puzzle_indices = list(puzzle_indices)
        self.grader_model = grader_model
        self.grader_runs = grader_runs

    def _evaluate(self, X, out, *args, **kwargs):
        try:
            result = evaluate_config(
                model=X["model"],
                template=X["template"],
                n_clues=int(X["n_clues"]),
                temperature=float(X["temperature"]),
                puzzle_indices=self.puzzle_indices,
                grader_model=self.grader_model,
                grader_runs=self.grader_runs,
                progress=False,
            )
            out["F"] = [result.mean_gen_cost, -result.mean_quality]
        except Exception as e:
            print(f"[eval failed] {dict(X)} -> {type(e).__name__}: {e}", flush=True)
            out["F"] = [1.0, 0.0]
