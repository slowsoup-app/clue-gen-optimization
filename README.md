# MONRP x SlowSoup — Clue Generation Pipeline

A multi-objective optimization study of LLM-based clue generation for lateral-thinking puzzles, derived from the SlowSoup platform.

---

## Dataset

This project uses the lateral-thinking-puzzle dataset from **_Weak-eval-Strong: Evaluating and Eliciting Lateral Thinking of LLMs with Situation Puzzles_** (Chen et al., NeurIPS 2024). The dataset is **not redistributed in this repository** — please obtain `puzzles.xlsx` from the [official paper repository](https://github.com/chenqi008/LateralThinking) and place it at the project root before running. For more information, see the [Citation](#citation) section below.

---

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# fill in GROQ_API_KEY and ANTHROPIC_API_KEY in .env
# place puzzles.xlsx at the repo root (see Dataset section above)
```

Run the optimization:

```bash
python -m algos.run     # NSGA-II / SPEA2 search
python -m algos.plot    # Pareto front + diagnostic plots
```

Algorithm, population size, generations, and #puzzles per evaluation are configured at the top of [`algos/run.py`](algos/run.py).

---

## Decision Variables

- Groq model 
- Prompt template / decomposition strategy
- Number of clues
- Temperature

---

## Objectives

- **Minimize cost**: Groq API cost per puzzle
- **Maximize quality score**: Claude API (with `temperature = 0`) as grader
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
| Baseline | Uniform Random Search (same eval budget) |
| Puzzles + reference solutions | Chen et al. (2024) dataset |

---

## Experimental protocol

Because metaheuristic search is stochastic, a single run is not a reliable signal. The pipeline runs each algorithm — **NSGA-II**, **SPEA2**, and **Random Search** — across **10 independent seeds** on a fixed puzzle sample (`PUZZLE_SEED = 42`). Each `(algorithm, seed)` run uses the same `POP × GENS` evaluation budget so the comparison is apples-to-apples.

Random Search draws configurations uniformly from the same decision-variable space defined in [`algos/problem.py`](algos/problem.py) and returns its non-dominated front over all evaluated points.

For each run we compute the **2-D hypervolume** of the final non-dominated front against a shared reference point derived from all evaluated points across all runs. This yields 10 HV samples per algorithm.

We then run a **pairwise two-sided Mann-Whitney U test** on the HV samples for each algorithm pair (NSGA-II vs Random, SPEA2 vs Random, NSGA-II vs SPEA2). Results are written to [`results/stats.md`](results/stats.md).

---

## Output

- [`results/pareto.png`](results/pareto.png)
  - Pareto fronts (faded = each seed, bold = best-HV seed) per algorithm.
- [`results/hv_boxplot.png`](results/hv_boxplot.png)
  - final-HV distribution across seeds, per algorithm.
- [`results/convergence.png`](results/convergence.png)
  - median HV with IQR band over generations, per algorithm.
- [`results/stats.md`](results/stats.md)
  - per-algorithm HV summary table and Mann-Whitney U p-values.

Each `(algorithm, seed)` run is checkpointed to `results/{algo}_seed{NN}.json`, so the sweep can be interrupted and resumed without re-running completed seeds.

---

## Limitations & Future Works
* Number of Clues
  * Our current approach searches based on a hardcoded "Number of Clues", whereas in reality, a better approach might be to either let the model decide the exact number or adjust the limit based on puzzle difficulty.
* Grading: 1-run vs. 3-run averaged
  * Our intuition was to take the average of the quality scores across 3 runs, but after experimenting with the dataset, we found that the deviation between individual grading runs is quite minimal given that Claude is set to temperature = 0. 
  * Thus, we went with 1 run instead of 3 to save tokens, though ideally the 3-run average approach would be more bulletproof and better justified despite the minimal difference in effect.

---
## Citation

```bibtex
@article{chen2024weak,
  title={Weak-eval-Strong: Evaluating and Eliciting Lateral Thinking of LLMs with Situation Puzzles},
  author={Chen, Qi and Zhang, Bowen and Wang, Gang and Wu, Qi},
  journal={Conference on Neural Information Processing Systems (NeurIPS)},
  year={2024}
}
```