# Statistical comparison: final hypervolume across seeds

Seeds per algorithm: **5**

## Per-algorithm summary

| Algorithm | Median | Mean | Std | Min | Max |
|---|---|---|---|---|---|
| NSGA2 | 0.002687 | 0.002727 | 0.0001136 | 0.002614 | 0.002883 |
| SPEA2 | 0.002679 | 0.00269 | 5.243e-05 | 0.002625 | 0.002771 |
| RANDOM | 0.002683 | 0.002643 | 0.0001047 | 0.002505 | 0.002766 |

## Pairwise Mann-Whitney U (two-sided) and Vargha-Delaney A12

Mann-Whitney null hypothesis: the two algorithms produce hypervolume distributions with the same median. A12 is the probability that a random run of A produces a higher hypervolume than a random run of B; A12 > 0.5 favors A.

| A | B | U | p | A12 | magnitude |
|---|---|---|---|---|---|
| NSGA2 | SPEA2 | 14.0 | 0.8413 | 0.560 | small |
| NSGA2 | RANDOM | 17.0 | 0.4206 | 0.680 | medium |
| SPEA2 | RANDOM | 15.0 | 0.6905 | 0.600 | small |
