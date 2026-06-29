# Stage 03 - Multilevel variance decomposition

**Goal.** Quantify how much variance lives within vs between persons, to justify
idiographic / within-person modelling. Pure replication and extension of Annick's
original null-model analysis.

`01_variance_decomposition.R` fits null mixed models (`lme4`) with random person and
nested person/day intercepts for each momentary measure, and reports the ICC plus the
between-person / between-day / within-day variance shares.

**Headline numbers (reproduce the original script).**
- Pain ICC(person) = 0.585, Fatigue 0.580, Stress 0.593.
- Activity (log ENMO): only 29% between persons, **67.5% within day** - the moment-to-moment
  signal the lag-1 network exploits. This is the single strongest justification for the
  idiographic / multilevel-VAR approach.

Output: `results/tables/03_variance_decomposition.csv` -> MAIN Figure 2 and Table 2.
