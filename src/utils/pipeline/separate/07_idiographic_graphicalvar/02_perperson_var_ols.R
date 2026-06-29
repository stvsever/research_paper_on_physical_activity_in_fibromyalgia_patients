# Stage 07b - Per-person unregularized VAR(1) by OLS (individual coupling strengths).
#
# graphicalVAR (stage 07a) regularizes individual networks toward sparsity, so the
# theoretically central symptom->activity edges are usually shrunk to exactly zero, and
# the mlVAR subject coefficients are empirical-Bayes shrunken (constant where the random
# SD is ~0). To obtain genuine, person-specific coupling strengths for the RQ2 link (e.g.
# "strength of Pain -> Activity per person", exactly as Annick proposed), we fit an
# UNREGULARIZED lag-1 VAR per person by OLS:
#
#     y_t = b0 + B * y_{t-1} + e_t,   lags built WITHIN day only.
#
# These coefficients are noisy at T ~ 44 (we report their SE and R^2) but they are
# unbiased and vary across persons, making them the appropriate individual-difference
# outcome to regress on POAM-P. One row per person x directed edge.

this <- normalizePath(sub("--file=", "",
  grep("--file=", commandArgs(FALSE), value = TRUE)[1]), mustWork = FALSE)
lib <- file.path(dirname(this), "..", "..", "..", "lib")
source(file.path(lib, "common.R"))

d <- read_ema()
vars <- c("PIJN", "MOE", "STRESS", "ENMO_log")
d <- d[order(d$pid, d$day, d$beep), ]

# Within-person standardize each node so per-person OLS coefficients are on a comparable
# (standardized) metric across individuals and across the symptom/activity scales.
for (v in vars) {
  d[[v]] <- ave(d[[v]], d$pid, FUN = function(x) {
    s <- stats::sd(x, na.rm = TRUE)
    if (is.na(s) || s == 0) return(x - mean(x, na.rm = TRUE))
    (x - mean(x, na.rm = TRUE)) / s
  })
}

# within-day lag: previous row must be same person, same day, and adjacent beep.
make_lag <- function(df, v) {
  n <- nrow(df)
  out <- rep(NA_real_, n)
  if (n >= 2) {
    same <- df$pid[-1] == df$pid[-n] & df$day[-1] == df$day[-n] &
            (df$beep[-1] - df$beep[-n]) == 1
    out[-1] <- ifelse(same, df[[v]][-n], NA_real_)
  }
  out
}
for (v in vars) d[[paste0("L_", v)]] <- make_lag(d, v)

rows <- list()
summ <- list()
for (id in unique(d$pid)) {
  s <- d[d$pid == id, ]
  r2 <- c()
  for (yv in vars) {
    form <- stats::as.formula(paste0(yv, " ~ ",
              paste0("L_", vars, collapse = " + ")))
    sub <- s[stats::complete.cases(s[, c(yv, paste0("L_", vars))]), ]
    if (nrow(sub) < 15) next
    fit <- stats::lm(form, data = sub)
    co <- summary(fit)$coefficients
    r2 <- c(r2, summary(fit)$r.squared)
    for (pv in vars) {
      term <- paste0("L_", pv)
      if (term %in% rownames(co)) {
        rows[[length(rows) + 1]] <- data.frame(
          pid = id, from = pv, to = yv,
          coef = unname(co[term, 1]), se = unname(co[term, 2]),
          p = unname(co[term, 4]), n_pairs = nrow(sub))
      }
    }
  }
  summ[[id]] <- data.frame(pid = id, mean_R2 = ifelse(length(r2) > 0, mean(r2), NA))
}
edges <- do.call(rbind, rows)
edges$edge <- paste0(edges$from, "__to__", edges$to)
write_result(edges, "07_perperson_var_ols_edges.csv", DIR_NETWORKS)

# wide: one row per person, one column per directed edge coefficient
wide <- reshape(edges[, c("pid", "edge", "coef")],
                idvar = "pid", timevar = "edge", direction = "wide")
names(wide) <- sub("^coef\\.", "", names(wide))
sm <- do.call(rbind, summ)
wide <- merge(wide, sm, by = "pid", all.x = TRUE)
write_result(wide, "07_perperson_var_ols_wide.csv", DIR_NETWORKS)

cat("\n[per-person OLS VAR] fitted for", nrow(wide), "persons.\n")
key <- c("PIJN__to__ENMO_log", "MOE__to__ENMO_log", "STRESS__to__ENMO_log",
         "ENMO_log__to__PIJN", "ENMO_log__to__MOE")
for (k in key) if (k %in% names(wide)) {
  x <- wide[[k]]
  cat(sprintf("  %-22s mean %+.3f  SD %.3f  range [%+.2f, %+.2f]\n",
              k, mean(x, na.rm = TRUE), sd(x, na.rm = TRUE),
              min(x, na.rm = TRUE), max(x, na.rm = TRUE)))
}
