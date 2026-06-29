# Stage 05 - Multilevel VAR (PRIMARY network model, RQ1)

**Goal.** Estimate the group-level temporal, contemporaneous, and between-person networks
of Pain, Fatigue, Stress, and Activity, while quantifying individual heterogeneity. This
is the methodologically defensible primary analysis for the n-persons / short-T regime
(N = 34, T ~ 44), because mlVAR partially pools across persons rather than estimating each
network in isolation (which stage 07 shows is not identifiable here).

`01_mlvar_core.R` fits the 4-node `mlVAR` (lmer estimator, orthogonal random effects,
within-person standardized, lag-1, **lags within day only** via `dayvar`/`beepvar`). It
also accepts a `movement_only` argument used by the can't-move sensitivity (stage 92).

**Key results (RQ1).**
- All four states are self-persistent (significant positive autoregression).
- Significant cross-lagged effects: **Activity(t-1) -> Fatigue(t) = -0.131** (more activity
  predicts *less* subsequent fatigue) and **Stress(t-1) -> Pain(t) = +0.081**.
- Symptom -> Activity effects are ~0 at the group mean **but carry large random SDs**
  (e.g., Pain -> Activity random SD ~0.24), i.e. the direction/strength of how symptoms
  drive activity differs strongly across individuals. This heterogeneity is the core
  idiographic story and motivates RQ2.

`02_residual_diagnostics.R` refits each node equation explicitly and interrogates the
residuals for normality, homoscedasticity, and independence (within-person lag-1 residual
autocorrelation near zero), feeding the diagnostics supplement (`SUP_10`).

Outputs (to `results/networks/`): temporal/contemporaneous/between edge lists, the saved
model (`results/models/mlvar_core.rds`), per-person subject coefficients, and residuals.

**Orientation safeguard.** The script asserts the subject-coefficient array orientation
(`[response, predictor, lag]`) against the fixed effects before exporting.
