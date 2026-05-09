# MONRP x SlowSoup — Clue Generation Pipeline

## Dataset

SPLAT's `puzzles.xlsx`

---

## Decision Variables

- Groq model 
- Prompt template / decomposition strategy
- Number of clues
- Temperature

---

## Objectives

- **Minimize cost**: Groq API cost per puzzle
- **Maximize quality**: Claude API (with `temperature = 0`, 3-run avergaed) as grader
  - Non-revelation (0-3)
    - 3: No single clue reveals the core twist
    - 2: One clue is borderline but still requires inference
    - 1: One clue largely gives it away
    - 0: Multiple clues directly state the answer
  - Coverage (0-3)
    - 3: All key elements of the reference solution are pointed to
    - 2: Most key elements covered, minor gaps
    - 1: Significant elements missing
    - 0: Clues miss the core of the solution

---

## Stack

| Component | Tool |
|---|---|
| Clue generation | Groq API |
| Quality scoring | Claude API (rubric-based) |
| Optimization | NSGA-II / SPEA2 |
| Puzzles + reference solutions | SPLAT dataset |

---

## Output

A Pareto front showing cost vs quality tradeoffs across different clue generation configurations. Decision maker picks their preferred operating point.