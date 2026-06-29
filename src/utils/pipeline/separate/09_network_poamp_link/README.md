# Stage 09 - Network <-> POAM-P link (exploratory bridge between RQ1 and RQ2)

**Goal.** Connect the idiographic dynamics (RQ1) to the activity-pattern subgroups (RQ2),
exactly as Annick proposed: use each person's network parameters as outcomes and relate
them to POAM-P.

`01_link.py` takes the unshrunken per-person VAR(1) coefficients (stage 07b) plus mlVAR
temporal density, joins them to POAM-P subscales and subgroups, and runs:
1. Spearman correlations of each coupling with the three POAM-P subscales.
2. Kruskal-Wallis comparisons of each coupling across the dominant-pattern subgroups.

**Headline (exploratory) finding.** **Pain -> Activity coupling differs by POAM-P dominant
pattern (Kruskal-Wallis p = .040):** Avoiders show pain followed by *less* activity
(mean -0.15), Pacers show pain followed by *more* activity (mean +0.13), Overdoers in
between. Consistently, Pain -> Activity correlates rho = -0.39 with the Avoidance subscale.
This is a theory-consistent bridge: the avoidance phenotype is visible in the moment-to-
moment dynamics.

**Caveats (stated in output and table).** N = 30 with both data types; estimates are noisy
per-person OLS; tests are uncorrected. Strictly hypothesis-generating, well-suited to the
exploratory framing Annick wanted.
