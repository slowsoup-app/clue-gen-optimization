import json
from dataclasses import dataclass

from groq import Groq


@dataclass
class GroqModel:
    id: str
    input_price_per_1m: float
    output_price_per_1m: float


MODELS: dict[str, GroqModel] = {
    "llama-3.1-8b-instant": GroqModel("llama-3.1-8b-instant", 0.05, 0.08),
    "openai/gpt-oss-20b": GroqModel("openai/gpt-oss-20b", 0.075, 0.30),
    "openai/gpt-oss-120b": GroqModel("openai/gpt-oss-120b", 0.15, 0.60),
    "llama-3.3-70b-versatile": GroqModel("llama-3.3-70b-versatile", 0.59, 0.79),
}


PROMPT_TEMPLATES: dict[str, str] = {
    "direct": (
        "You are helping create hint clues for a lateral thinking situation puzzle.\n\n"
        "Puzzle title: {title}\n"
        "Puzzle story (what the solver sees):\n{story}\n\n"
        "Hidden solution (do NOT reveal directly):\n{answer}\n\n"
        "Generate exactly {n} clues that nudge the solver toward the solution without giving it away. Each clue must add new information.\n\n"
        'Respond ONLY with a JSON object of the form: {{"clues": ["clue 1", "clue 2", ...]}}. '
        "No other additional text."
    ),
    "decomposed": (
        "You are helping create hint clues for a lateral thinking situation puzzle.\n\n"
        "Puzzle title: {title}\n"
        "Puzzle story (what the solver sees):\n{story}\n\n"
        "Hidden solution (do NOT reveal directly):\n{answer}\n\n"
        "Step 1 (silent): identify the {n} most important elements of the solution.\n"
        "Step 2: for each element, write one clue that points the solver toward it without stating it directly.\n\n"
        "No headings, no explanations."
    ),
}


@dataclass
class GenerationResult:
    clues: list[str]
    model: str
    template: str
    temperature: float
    input_tokens: int
    output_tokens: int
    cost_usd: float
    raw_response: str


groq = Groq()


def _parse_clues(text: str, expected: int) -> list[str]:
    data = json.loads(text)
    if isinstance(data, dict) and isinstance(data.get("clues"), list):
        items = data["clues"]
    elif isinstance(data, list):
        items = data
    else:
        raise ValueError(f"Unexpected JSON shape from generator: {type(data).__name__}")
    return [str(c).strip() for c in items[:expected]]


def generate_clues(
    *,
    title: str,
    story: str,
    answer: str,
    model: str,
    n_clues: int,
    temperature: float,
    template: str = "direct",
) -> GenerationResult:

    spec = MODELS[model]
    prompt = PROMPT_TEMPLATES[template].format(
        title=title, story=story, answer=answer, n=n_clues
    )

    response = groq.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,

        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "clue_set",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "clues": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": n_clues,
                            "maxItems": n_clues,
                        }
                    },
                    "required": ["clues"],
                    "additionalProperties": False,
                }
            }
        }

        )


    raw = response.choices[0].message.content or ""
    usage = response.usage
    input_tokens = usage.prompt_tokens
    output_tokens = usage.completion_tokens
    cost = (
        input_tokens * spec.input_price_per_1m / 1_000_000
        + output_tokens * spec.output_price_per_1m / 1_000_000
    )

    return GenerationResult(
        clues=_parse_clues(raw, n_clues),
        model=model,
        template=template,
        temperature=temperature,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost,
        raw_response=raw,
    )
