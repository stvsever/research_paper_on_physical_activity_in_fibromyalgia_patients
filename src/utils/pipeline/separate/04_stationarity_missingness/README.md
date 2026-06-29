# Stage 04 - Stationarity, ENMO distribution, and missingness

**Goal.** Address Annick's three technical concerns head-on: ENMO skew, stationarity, and
informative missingness / could-not-move trials.

`01_stationarity.R` produces:
- ENMO skewness by transformation: raw 1.32 -> log -0.50 (near-symmetric). **Decision: model
  log ENMO.**
- Per-person stationarity: a linear-trend test and KPSS test per series. A minority of
  series show trends (e.g., Pain ~35% by the liberal trend test, ~18% by KPSS); mlVAR removes
  person means, and a supplementary detrended check is available. Activity is the most
  stationary (only ~9-12%).
- Compliance by study day and an MNAR probe: ENMO-missingness is **not** significantly
  predicted by momentary pain/fatigue/stress (all p > .13), supporting a missing-at-random
  working assumption for the objective activity gaps.

**Review note.** The could-not-move trials (~13%) are handled later by a dedicated
sensitivity analysis (stage 92), not dropped from the primary model.
