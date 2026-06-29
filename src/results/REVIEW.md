# Review summary - Walk On! EMA analysis

Human-in-the-loop review guide. States the research questions, the central methodological
decision, every analysis run, the key numbers, the robustness battery, and the open choices.
Figures are in `paper/assets/figures/`, tables in `paper/assets/tables/{main,supplementary}`,
and the compiled manuscript is `paper/report/main.pdf`.

## Research questions

1. **RQ1.** How do pain, fatigue, and stress influence physical activity within individual
   patients with fibromyalgia (optionally adding self-efficacy, intention, outcome
   expectancy)?
2. **RQ2.** Are there meaningful subgroups based on baseline activity patterns (POAM-P:
   avoidance / overdoing / pacing), and do the momentary dynamics differ across them?

## Central methodological decision (and the empirical answer)

The literature recommends ~100-120 timepoints/person for fully separate idiographic
networks; here the median is 44. We answered the feasibility question empirically:

- **graphicalVAR** (separate per-person regularized networks) selects a **median of 0
  temporal edges** of 16; 16 of 30 fitted participants have none. Fully idiographic networks
  are **not identifiable** here.
- **S-GIMME** finds no group-level cross-variable path and only weak subgroups (modularity
  0.27).
- Therefore the **primary model is multilevel VAR (mlVAR)** with partial pooling: a stable
  group network plus quantified individual heterogeneity. S-GIMME and graphicalVAR are
  reported as transparent complements. This is exactly the "add a robustness analysis"
  position Stijn raised with Annick.

## Pipeline (clean sequential stages)

| Stage | Method | Engine |
|-------|--------|--------|
| 01 preprocessing | exclusions, cleaning | Python |
| 02 descriptives (+ context) | compliance, correlations, location/social | Python |
| 03 variance decomposition | null multilevel models | R / lme4 |
| 04 stationarity / missingness | skew, KPSS, MNAR probe | R |
| 05 mlVAR (primary) + residual diagnostics | RQ1 networks | R / mlVAR |
| 06 S-GIMME | complement | R / gimme |
| 07 graphicalVAR + per-person OLS VAR | feasibility + coupling strengths | R |
| 08 POAM-P subgroups | typology + clustering | Python |
| 09 network <-> POAM-P link | RQ1<->RQ2 bridge | Python |
| 10 robustness | detrend, LOPO, bootstrap, extended, cant-move, threshold, transform, permutation | R |
| 11 pacing | pacing dynamics | R / lme4 |
| 12 figures + tables | MAIN_/SUP_ PNGs, markdown + LaTeX tables | Python |

## Key results

**RQ1 (group temporal network).** All states self-persistent. Two significant cross-lagged
effects: **Activity(t-1) -> Fatigue(t) = -0.13** (p = .015; bootstrap 95% CI [-0.25, -0.04])
and **Stress(t-1) -> Pain(t) = +0.08** (p = .027; bootstrap 95% CI [0.02, 0.15]).
Symptom -> activity effects ~0 at the mean but highly heterogeneous between persons
(per-person Pain -> Activity ranges -0.68 to +0.54). Activity is 68% within-person variance.

**RQ2 (subgroups + bridge).** Balanced dominant-pattern typology (Avoidance 10, Overdoing
12, Pacing 9). **Pain -> Activity coupling differs by dominant pattern** (Kruskal-Wallis
p = .040; permutation p = .037): avoiders pain -> less activity (-0.15), pacers pain -> more
activity (+0.13). Spearman with Avoidance score rho = -0.39 (permutation p = .033).
Exploratory (N = 30).

**Extended (6-node).** Adding self-efficacy + intention leaves core edges unchanged
(r = 0.999) and shows activity -> higher subsequent self-efficacy and intention (a HAPA
mastery feed-forward).

## Robustness battery (stage 10)

| Check | Result |
|-------|--------|
| Within-person detrended (stationarity) | r = 0.97, no sign flips |
| Leave-one-participant-out (34 refits) | every cross-lagged edge keeps its sign in 100% of refits |
| Person cluster bootstrap (500) | both significant edges' 95% CIs exclude 0; sign-consistency > 0.99 |
| Stricter compliance (>= 40 prompts) | r = 0.98, no sign flips |
| ENMO raw / sqrt scale | r >= 0.997 |
| Could-not-move excluded (~13%) | r = 0.98, no sign flips |
| Residual diagnostics | independence and homoscedasticity hold; mild non-normality offset by bootstrap |

## Open choices to discuss

1. **Primary model framing.** mlVAR primary, graphicalVAR/S-GIMME as the "why not fully
   idiographic" evidence. (Recommended; now also supported by the full robustness battery.)
2. **Node set.** 4 core nodes primary, 6-node as supplement. Outcome expectancy
   (`UITKOMSTVERW`) currently left out of the temporal model; add as a 7th node?
3. **RQ2 strength.** The link is exploratory (N = 30); frame as hypothesis-generating for
   the planned single-case experimental study.
4. **Manuscript.** Discussion and Conclusion are intentionally not yet written.
