# Statistical comparison: final hypervolume across seeds

Seeds per algorithm: **5**

## Per-algorithm summary

| Algorithm | Median | Mean | Std | Min | Max |
|---|---|---|---|---|---|
| NSGA2 | 0.001062 | 0.001103 | 0.0001123 | 0.0009906 | 0.001257 |
| SPEA2 | 0.001058 | 0.001065 | 5.225e-05 | 0.0009993 | 0.001145 |
| RANDOM | 0.001059 | 0.001019 | 0.0001029 | 0.0008806 | 0.001139 |

## Pairwise Mann-Whitney U (two-sided)

Null hypothesis: the two algorithms produce hypervolume distributions with the same median.

| A | B | U | p | significant (alpha=0.05) |
|---|---|---|---|---|
| NSGA2 | SPEA2 | 14.0 | 0.8413 | no |
| NSGA2 | RANDOM | 17.0 | 0.4206 | no |
| SPEA2 | RANDOM | 15.0 | 0.6905 | no |
