from dataclasses import dataclass
import anthropic


CLAUDE_MODELS: list[str] = [
    "claude-sonnet-4-6",
    "claude-haiku-4-5",
    "claude-opus-4-7",
]

DEFAULT_GRADER_MODEL = "claude-sonnet-4-6"
GRADER_RUNS = 1


SYSTEM_PROMPT = """You are a strict rubric grader for hint-clue quality on lateral thinking situation puzzles.

You will be given a puzzle (title, story shown to the solver, and the hidden solution) and a numbered list of clues that were generated to nudge the solver toward the solution.

Score the SET of clues on two independent rubrics, each 0-3:

NON-REVELATION (does any clue give away the twist?):
- 3: No single clue reveals the core twist; all require inference.
- 2: One clue is borderline but still requires inference.
- 1: One clue largely gives the twist away.
- 0: Multiple clues directly state the answer.

COVERAGE (do the clues collectively point to the solution's key elements?):
- 3: All key elements of the reference solution are pointed to.
- 2: Most key elements covered, minor gaps.
- 1: Significant elements missing.
- 0: Clues miss the core of the solution.

Use the integers 0, 1, 2, or 3 only - no fractional scores. Be calibrated; reserve 3s for genuinely strong sets and 0s for clear failures."""


GRADER_TOOL = {
    "name": "submit_grade",
    "description": "Submit your rubric-based grading of the clue set.",
    "input_schema": {
        "type": "object",
        "properties": {
            "rationale": {
                "type": "string",
                "description": "Brief justification for the scores.",
            },
            "non_revelation": {"type": "integer", "minimum": 0, "maximum": 3},
            "coverage": {"type": "integer", "minimum": 0, "maximum": 3},

        },
        "required": ["rationale", "non_revelation", "coverage"],
    },
}


@dataclass
class GradeRun:
    non_revelation: int
    coverage: int
    rationale: str
    input_tokens: int
    output_tokens: int


@dataclass
class GradingResult:
    runs: list[GradeRun]
    avg_non_revelation: float
    avg_coverage: float
    avg_quality: float
    model: str


claude = anthropic.Anthropic(max_retries=10)


def _build_user_prompt(title: str, story: str, answer: str, clues: list[str]) -> str:
    numbered = "\n".join(f"{i}. {c}" for i, c in enumerate(clues, 1))
    return (
        f"Puzzle title: {title}\n"
        f"Puzzle story: {story}\n"
        f"Hidden solution: {answer}\n\n"
        f"Clues to grade:\n{numbered}\n\n"
        f"Submit your grades using the submit_grade tool."
    )


def _grade_once(prompt: str, model: str) -> GradeRun:
    response = claude.messages.create(
        model=model,
        max_tokens=1024,
        temperature=0,
        system=SYSTEM_PROMPT,
        tools=[GRADER_TOOL],
        tool_choice={"type": "tool", "name": "submit_grade"},
        messages=[{"role": "user", "content": prompt}],
    )

    tool_block = next(
        (b for b in response.content if b.type == "tool_use" and b.name == "submit_grade"),
        None,
    )
    if tool_block is None:
        raise RuntimeError(
            f"Grader did not call submit_grade. Stop reason: {response.stop_reason}"
        )

    grade = tool_block.input
    usage = response.usage

    return GradeRun(
        non_revelation=grade["non_revelation"],
        coverage=grade["coverage"],
        rationale=grade["rationale"],
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
    )


def grade_clues(
    *,
    title: str,
    story: str,
    answer: str,
    clues: list[str],
    model: str = DEFAULT_GRADER_MODEL,
    n_runs: int = GRADER_RUNS,
) -> GradingResult:
    
    prompt = _build_user_prompt(title, story, answer, clues)
    runs: list[GradeRun] = []
    for _ in range(n_runs):
        runs.append(_grade_once(prompt, model))

    avg_nr = sum(r.non_revelation for r in runs) / len(runs)
    avg_cov = sum(r.coverage for r in runs) / len(runs)
    return GradingResult(
        runs=runs,
        avg_non_revelation=avg_nr,
        avg_coverage=avg_cov,
        avg_quality=avg_nr + avg_cov,
        model=model,
    )
