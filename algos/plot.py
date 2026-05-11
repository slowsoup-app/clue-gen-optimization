import glob, json
from pathlib import Path

import matplotlib.pyplot as plt

RESULTS = Path(__file__).resolve().parent.parent / "results"


def latest(algo: str) -> Path:
    files = sorted(glob.glob(str(RESULTS / f"{algo}_*.json")))
    if not files:
        raise FileNotFoundError(f"no results for {algo}")
    return Path(files[-1])


def load_front(path: Path):
    data = json.loads(path.read_text())
    front = sorted(data["front"], key=lambda p: p["cost"])
    costs = [p["cost"] for p in front]
    quals = [p["quality"] for p in front]
    return costs, quals


def main():
    plt.figure(figsize=(7, 5))
    for algo, color in [("nsga2", "tab:blue"), ("spea2", "tab:orange")]:
        costs, quals = load_front(latest(algo))
        plt.plot(costs, quals, marker="o", color=color, label=algo.upper())

    plt.xscale("log")
    plt.xlabel("Generation cost per puzzle (USD)")
    plt.ylabel("Quality (non-revelation + coverage, 0-6)")
    plt.title("Pareto fronts: NSGA-II vs SPEA2")
    plt.legend()
    plt.grid(True, which="both", alpha=0.3)
    plt.tight_layout()

    out = RESULTS / "pareto.png"
    plt.savefig(out, dpi=150)
    print(f"saved -> {out}")


if __name__ == "__main__":
    main()
