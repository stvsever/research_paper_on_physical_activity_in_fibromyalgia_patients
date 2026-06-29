# Stage 04 - Stationarity, detrending need, ENMO distribution, and missingness/MNAR.
#
# Addresses three of Annick's explicit technical concerns:
#   (1) ENMO is right-skewed  -> quantify skew of raw vs log/sqrt; justify the log transform.
#   (2) Stationarity?          -> per-person linear-trend test (mean non-stationarity) and
#                                 KPSS level-stationarity test; report the share of series
#                                 that need detrending. mlVAR/graphicalVAR remove person
#                                 means; a remaining time trend is the main threat.
#   (3) Missingness / could-not-move -> compliance over the 14 days, and a test of whether
#       missing ENMO is associated with momentary symptoms (informative-missingness / MNAR
#       probe). Feeds a supplementary figure and the methods text.

this <- normalizePath(sub("--file=", "",
  grep("--file=", commandArgs(FALSE), value = TRUE)[1]), mustWork = FALSE)
lib <- file.path(dirname(this), "..", "..", "..", "lib")
source(file.path(lib, "common.R"))
need(c("tseries", "lme4"))

# Sample skewness / excess-free kurtosis (no extra package dependency).
skewness <- function(x) { x <- x[!is.na(x)]; n <- length(x)
  m <- mean(x); s <- sqrt(mean((x - m)^2)); mean((x - m)^3) / s^3 }
kurtosis <- function(x) { x <- x[!is.na(x)]; n <- length(x)
  m <- mean(x); s <- sqrt(mean((x - m)^2)); mean((x - m)^4) / s^4 }

d <- read_ema()
d$pid <- factor(d$pid)
core <- c("PIJN", "MOE", "STRESS", "ENMO", "ENMO_log")

# ---- (1) ENMO skew ----------------------------------------------------------
skew_tbl <- data.frame(
  measure = c("ENMO (raw)", "ENMO (sqrt)", "ENMO (log)"),
  skewness = c(skewness(d$ENMO), skewness(d$ENMO_sqrt), skewness(d$ENMO_log)),
  kurtosis = c(kurtosis(d$ENMO), kurtosis(d$ENMO_sqrt), kurtosis(d$ENMO_log)))
skew_tbl[, 2:3] <- round(skew_tbl[, 2:3], 3)
write_result(skew_tbl, "04_enmo_skewness.csv")
cat("ENMO distribution (skewness):\n"); print(skew_tbl)

# ---- (2) per-person stationarity -------------------------------------------
vars <- c("PIJN", "MOE", "STRESS", "ENMO_log")
rows <- list()
for (v in vars) {
  for (id in levels(d$pid)) {
    s <- d[d$pid == id, ]
    y <- s[[v]]
    t <- s$obs
    ok <- !is.na(y)
    y <- y[ok]; t <- t[ok]
    if (length(y) < 20 || stats::sd(y) == 0) next
    # linear trend (mean non-stationarity)
    lm_fit <- stats::lm(y ~ t)
    p_trend <- summary(lm_fit)$coefficients[2, 4]
    # KPSS level-stationarity (H0 = stationary); small p => reject stationarity
    kp <- suppressWarnings(tryCatch(tseries::kpss.test(y, null = "Level")$p.value,
                                    error = function(e) NA))
    rows[[length(rows) + 1]] <- data.frame(
      variable = v, pid = id, n = length(y),
      trend_p = p_trend, trend_sig = p_trend < 0.05,
      kpss_p = kp, kpss_nonstationary = !is.na(kp) & kp < 0.05)
  }
}
stat_df <- do.call(rbind, rows)
write_result(stat_df, "04_stationarity_perperson.csv")

stat_sum <- aggregate(cbind(trend_sig, kpss_nonstationary) ~ variable,
                      data = stat_df, FUN = function(x) round(mean(x), 3))
names(stat_sum) <- c("variable", "prop_sig_linear_trend", "prop_kpss_nonstationary")
write_result(stat_sum, "04_stationarity_summary.csv")
cat("\nShare of individual series that are non-stationary:\n"); print(stat_sum)

# ---- (3) compliance over time + informative missingness ---------------------
d$missing_enmo <- as.integer(is.na(d$ENMO))
d$completed <- as.logical(d$completed)          # CSV stores "True"/"False"
d$responded <- as.integer(d$completed)
comp_day <- aggregate(responded ~ day, data = d, FUN = mean)
comp_day$responded <- round(comp_day$responded, 3)
write_result(comp_day, "04_compliance_by_day.csv")

# Does momentary symptom level predict NON-response at the same prompt?
# (response indicator regressed on previous-completed symptom carries selection; instead
#  test whether ENMO-missingness covaries with reported symptoms when the survey WAS done.)
d_done <- d[d$completed %in% TRUE, ]
mnar <- tryCatch({
  m <- lme4::glmer(missing_enmo ~ scale(PIJN) + scale(MOE) + scale(STRESS) + (1 | pid),
                   data = d_done, family = binomial,
                   control = lme4::glmerControl(optimizer = "bobyqa"))
  co <- summary(m)$coefficients
  data.frame(term = rownames(co), estimate_logit = round(co[, 1], 3),
             SE = round(co[, 2], 3), p = round(co[, 4], 4))
}, error = function(e) data.frame(term = NA, note = conditionMessage(e)))
write_result(mnar, "04_enmo_missingness_mnar_probe.csv")
cat("\nENMO-missingness vs momentary symptoms (MNAR probe, logit):\n"); print(mnar)

cat("\nDecision: ENMO is modelled on the log scale (skew reduced toward symmetry).\n",
    "mlVAR removes person means; the residual stationarity threat is the per-person\n",
    "time trend, present in a minority of series (see summary) and addressed in a\n",
    "supplementary detrended sensitivity analysis.\n", sep = "")
