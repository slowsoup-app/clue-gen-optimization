import glob
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import mannwhitneyu

RESULTS = Path(__file__).resolve().parent.parent / "results"
ALGOS = [("nsga2", "tab:blue"), ("spea2", "tab:orange"), ("random", "tab:gray")]


def load_runs(algo: str) -> list[dict]:
    files = sorted(glob.glob(str(RESULTS / f"{algo}_seed*.json")))
    if not files:
        raise FileNotFoundError(f"no results for {algo} (expected {algo}_seed*.json)")
    return [json.loads(Path(f).read_text()) for f in files]


def _hv_2d(points, ref):
    """Hypervolume for 2-D minimization. points: list of (f0, f1). ref: (r0, r1)."""
    pts = [(f0, f1) for f0, f1 in points if f0 <= ref[0] and f1 <= ref[1]]
    if not pts:
        return 0.0
    pts.sort(key=lambda p: p[0])
    nd = []
    best = float("inf")
    for f0, f1 in pts:
        if f1 < best:
            nd.append((f0, f1))
            best = f1
    hv = 0.0
    prev_f0 = ref[0]
    for f0, f1 in reversed(nd):
        hv += (prev_f0 - f0) * (ref[1] - f1)
        prev_f0 = f0
    return hv


def _global_ref(all_runs):
    f0s, f1s = [], []
    for runs in all_runs.values():
        for r in runs:
            for gen in r["history"]:
                for f0, f1 in gen:
                    f0s.append(f0)
                    f1s.append(f1)
    return max(f0s) * 1.05, max(f1s) * 1.05


def _final_hv(run, ref):
    pts = [(p["cost"], -p["quality"]) for p in run["front"]]
    return _hv_2d(pts, ref)


def plot_pareto(all_runs, ref):
    plt.figure(figsize=(7, 5))
    for algo, color in ALGOS:
        for r in all_runs[algo]:
            front = sorted(r["front"], key=lambda p: p["cost"])
            plt.plot([p["cost"] for p in front], [p["quality"] for p in front],
                     marker=".", color=color, alpha=0.2, linewidth=1)
        best_i = max(range(len(all_runs[algo])),
                     key=lambda i: _final_hv(all_runs[algo][i], ref))
        front = sorted(all_runs[algo][best_i]["front"], key=lambda p: p["cost"])
        plt.plot([p["cost"] for p in front], [p["quality"] for p in front],
                 marker="o", color=color,
                 label=f"{algo.upper()} (best of {len(all_runs[algo])})")
    plt.xscale("log")
    plt.xlabel("Generation cost per puzzle (USD)")
    plt.ylabel("Quality (non-revelation + coverage, 0-6)")
    plt.title("Pareto fronts (faded = all seeds, bold = best-HV seed)")
    plt.legend()
    plt.grid(True, which="both", alpha=0.3)
    plt.tight_layout()
    out = RESULTS / "pareto.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"saved -> {out}")


def plot_hv_boxplot(all_runs, ref):
    hv_per_algo = {a: [_final_hv(r, ref) for r in all_runs[a]] for a, _ in ALGOS}
    plt.figure(figsize=(7, 5))
    data = [hv_per_algo[a] for a, _ in ALGOS]
    labels = [a.upper() for a, _ in ALGOS]
    colors = [c for _, c in ALGOS]
    bp = plt.boxplot(data, labels=labels, patch_artist=True, showmeans=True)
    for patch, c in zip(bp["boxes"], colors):
        patch.set_facecolor(c)
        patch.set_alpha(0.5)
    for i, vals in enumerate(data):
        plt.scatter([i + 1] * len(vals), vals, color=colors[i], alpha=0.7, s=22, zorder=3)
    plt.ylabel(f"Final hypervolume (ref=({ref[0]:.2e}, {ref[1]:.2f}))")
    plt.title(f"Hypervolume across {len(data[0])} seeds")
    plt.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    out = RESULTS / "hv_boxplot.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"saved -> {out}")
    return hv_per_algo


def plot_convergence(all_runs, ref):
    plt.figure(figsize=(7, 5))
    for algo, color in ALGOS:
        all_traj = []
        for r in all_runs[algo]:
            seen = []
            traj = []
            for gen in r["history"]:
                seen.extend(gen)
                traj.append(_hv_2d(seen, ref))
            all_traj.append(traj)
        all_traj = np.array(all_traj)
        gens = np.arange(1, all_traj.shape[1] + 1)
        median = np.median(all_traj, axis=0)
        q25 = np.quantile(all_traj, 0.25, axis=0)
        q75 = np.quantile(all_traj, 0.75, axis=0)
        plt.plot(gens, median, marker="o", color=color, label=algo.upper())
        plt.fill_between(gens, q25, q75, color=color, alpha=0.2)
    plt.xlabel("Generation")
    plt.ylabel(f"Cumulative hypervolume (ref=({ref[0]:.2e}, {ref[1]:.2f}))")
    plt.title("Convergence: median HV with IQR band across seeds")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    out = RESULTS / "convergence.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"saved -> {out}")


def run_stats(hv_per_algo):
    algos = list(hv_per_algo.keys())
    n_seeds = len(hv_per_algo[algos[0]])
    lines = []
    lines.append("# Statistical comparison: final hypervolume across seeds")
    lines.append("")
    lines.append(f"Seeds per algorithm: **{n_seeds}**")
    lines.append("")
    lines.append("## Per-algorithm summary")
    lines.append("")
    lines.append("| Algorithm | Median | Mean | Std | Min | Max |")
    lines.append("|---|---|---|---|---|---|")
    for a in algos:
        vals = np.array(hv_per_algo[a])
        lines.append(
            f"| {a.upper()} | {np.median(vals):.4g} | {np.mean(vals):.4g} | "
            f"{np.std(vals, ddof=1):.4g} | {np.min(vals):.4g} | {np.max(vals):.4g} |"
        )
    lines.append("")
    lines.append("## Pairwise Mann-Whitney U (two-sided)")
    lines.append("")
    lines.append("Null hypothesis: the two algorithms produce hypervolume distributions with the same median.")
    lines.append("")
    lines.append("| A | B | U | p | significant (alpha=0.05) |")
    lines.append("|---|---|---|---|---|")
    for i, a in enumerate(algos):
        for b in algos[i + 1:]:
            u, p = mannwhitneyu(hv_per_algo[a], hv_per_algo[b], alternative="two-sided")
            sig = "yes" if p < 0.05 else "no"
            lines.append(f"| {a.upper()} | {b.upper()} | {u:.1f} | {p:.4g} | {sig} |")
    lines.append("")
    out = RESULTS / "stats.md"
    out.write_text("\n".join(lines))
    print(f"saved -> {out}")
    print()
    for ln in lines:
        print(ln)


def main():
    all_runs = {a: load_runs(a) for a, _ in ALGOS}
    ref = _global_ref(all_runs)
    plot_pareto(all_runs, ref)
    plot_convergence(all_runs, ref)
    hv_per_algo = plot_hv_boxplot(all_runs, ref)
    run_stats(hv_per_algo)


if __name__ == "__main__":
    main()
