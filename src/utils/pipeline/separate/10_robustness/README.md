# Stage 10 - Robustness and sensitivity battery

This stage stress-tests the primary multilevel VAR (stage 05) against every concern a
reviewer (or Annick's email) would raise about a small, intensively measured sample. All
scripts reuse the identical mlVAR specification via `src/utils/lib/mlvar_helpers.R`.

| Script | What it does | Headline result |
|--------|--------------|-----------------|
| `01_detrended_mlvar.R` | Refit after within-person linear detrending (stationarity) | r = 0.97 with primary, no sign flips |
| `02_leave_one_out.R` | 34 refits, each dropping one participant | every cross-lagged edge keeps its sign in 100% of refits |
| `03_person_bootstrap.R` | Person-level cluster bootstrap (500 resamples) | the two significant edges have bootstrap 95% CIs excluding 0 |
| `04_extended_model.R` | 6-node model adding self-efficacy + intention | core edges r = 0.999; reveals activity -> self-efficacy/intention feed-forward |
| `05_cantmove_sensitivity.R` | Exclude could-not-move prompts (~13%) | r = 0.98, no sign flips |
| `06_compliance_threshold.R` | Restrict to participants with >= 40 prompts | r = 0.98, no sign flips |
| `07_enmo_transform.R` | Raw and sqrt activity instead of log | r >= 0.997 |
| `08_permutation_link.R` | Exact permutation inference for the RQ2 link | Pain->Activity by POAM-P type permutation p = .037 |

**Why this matters for review.** Stijn's note to Annick flagged that individual networks
are hard to justify at this series length and that a robustness analysis is needed. Stage
07 shows fully idiographic networks are not identifiable; this stage shows the *group*
(partial-pooling) network that we do report is exceptionally stable: it survives detrending,
transformation, influential-participant removal, stricter compliance, and the could-not-move
exclusion, and its key edges are bootstrap- and LOPO-stable. Outputs feed `SUP_09` (figure),
`SUP_08`/`SUP_09`/`SUP_10` (tables), and the bootstrap CIs quoted in the main text.

**Implementation note.** `mlvar_helpers.R::fit_mlvar` deliberately does **not** set an
internal RNG seed: an earlier internal `set.seed()` silently broke the cluster bootstrap by
resetting the RNG to a constant after each fit (every resample became identical). The
bootstrap now seeds per iteration before resampling.
