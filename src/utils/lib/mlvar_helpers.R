# Shared mlVAR fitting helpers, sourced by the primary model (stage 05) and the
# robustness battery (stage 10) so that every refit uses an identical specification.
#
# Specification rationale (fixed across the project):
#   - lags = 1 (lag-1 vector autoregression),
#   - dayvar + beepvar: lags are only built between adjacent beeps WITHIN a day (no lag is
#     constructed across the overnight gap),
#   - within-person standardization (scale = TRUE),
#   - orthogonal random effects: with N = 34 persons and 16 temporal parameters, correlated
#     random effects are not estimable; orthogonal REs are the stable choice (Epskamp,
#     Waldorp, Mottus, & Borsboom, 2018),
#   - estimator = "lmer".

suppressWarnings(suppressMessages(require(mlVAR)))

CORE_VARS <- c("PIJN", "MOE", "STRESS", "ENMO_log")

# Fit the project-standard mlVAR and return the model object.
# NOTE: the lmer estimator is deterministic, so no internal seeding is performed. (An
# earlier internal set.seed() silently broke the cluster bootstrap by resetting the RNG to
# a constant after every fit, making every resample identical.)
fit_mlvar <- function(d, vars = CORE_VARS) {
  d <- d[, c("pid", "day", "beep", vars)]
  d$pid <- as.factor(d$pid)
  mlVAR::mlVAR(d, vars = vars, idvar = "pid", dayvar = "day", beepvar = "beep",
               lags = 1, temporal = "orthogonal", contemporaneous = "orthogonal",
               estimator = "lmer", scale = TRUE, verbose = FALSE)
}

# Tidy temporal edge list (from = predictor at t-1, to = outcome at t).
mlvar_temporal_edges <- function(m) {
  s <- summary(m)$temporal
  out <- s[, c("from", "to", "fixed", "SE", "P", "ran_SD")]
  names(out) <- c("from", "to", "weight", "SE", "P", "ran_SD")
  out$edge <- paste0(out$from, "__to__", out$to)
  out
}

# Compare two temporal edge lists; returns merged frame + summary stats.
compare_edges <- function(reference, alternative, label = "alt") {
  m <- merge(reference[, c("edge", "from", "to", "weight")],
             alternative[, c("edge", "weight")], by = "edge",
             suffixes = c("_ref", paste0("_", label)))
  wr <- m[["weight_ref"]]
  wa <- m[[paste0("weight_", label)]]
  m$abs_diff <- abs(wr - wa)
  attr(m, "r") <- stats::cor(wr, wa)
  attr(m, "max_abs_diff") <- max(m$abs_diff)
  attr(m, "n_sign_flip") <- sum(sign(wr) != sign(wa) &
                                  pmax(abs(wr), abs(wa)) > 0.05)
  m
}
