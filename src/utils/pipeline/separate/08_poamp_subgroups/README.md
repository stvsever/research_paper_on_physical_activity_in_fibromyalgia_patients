# Stage 08 - POAM-P activity-pattern subgroups (RQ2)

**Goal.** Identify meaningful subgroups by baseline activity pattern (avoidance /
overdoing / pacing).

`01_poamp_subgroups.py` produces two complementary, deliberately exploratory views:
- **Dominant-pattern typology** (highest z-scored subscale): Avoidance n=10, Overdoing
  n=12, Pacing n=9. Simple, interpretable, robust at N=31, and maps directly onto the three
  POAM-P constructs. This is the lens carried into the RQ1<->RQ2 link.
- **Data-driven clustering** (k-means with silhouette + Gaussian mixture with BIC): the
  best solution is k=2 with a weak silhouette (0.31), separating "overdoers" (n=12) from
  "avoidant-pacers" (n=19). Reported with explicit small-N caveats.

Output: `data/processed/poamp_subgroups.csv` (per-person labels + subscale z-scores) and
profile/selection tables in `results/tables/`.

**Review note.** With N=31 and three correlated subscales, do not over-interpret the
clusters; the typology is the more stable basis for downstream comparison.
