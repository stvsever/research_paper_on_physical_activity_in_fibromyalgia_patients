# Stage 05b - Residual diagnostics for the primary multilevel VAR.
#
# A reviewer will ask whether the mlVAR assumptions hold. We refit each node equation
# explicitly as the multilevel lag-1 model mlVAR uses (within-person standardized outcome
# regressed on the four within-day lagged predictors with a random person intercept) and
# interrogate the residuals for:
#   - normality (Shapiro-Wilk; skew/kurtosis),
#   - homoscedasticity (association between |residual| and fitted value),
#   - independence (within-person lag-1 residual autocorrelation; should be ~0 after the
#     autoregressive terms are included).
# Residuals and fitted values are exported for the assumptions supplementary figure.

this <- normalizePath(sub("--file=", "",
  grep("--file=", commandArgs(FALSE), value = TRUE)[1]), mustWork = FALSE)
lib <- file.path(dirname(this), "..", "..", "..", "lib")
source(file.path(lib, "common.R"))
need(c("lme4"))

skewf <- function(x){x<-x[!is.na(x)];m<-mean(x);s<-sqrt(mean((x-m)^2));mean((x-m)^3)/s^3}
kurtf <- function(x){x<-x[!is.na(x)];m<-mean(x);s<-sqrt(mean((x-m)^2));mean((x-m)^4)/s^4}

d <- read_ema()
vars <- c("PIJN", "MOE", "STRESS", "ENMO_log")
d <- d[order(d$pid, d$day, d$beep), ]
# within-person standardize
for (v in vars) d[[v]] <- ave(d[[v]], d$pid, FUN = function(x){
  s <- stats::sd(x, na.rm = TRUE); if (is.na(s) || s == 0) x - mean(x, na.rm = TRUE) else (x - mean(x, na.rm = TRUE)) / s })
# within-day lag-1 predictors
make_lag <- function(df, v){ n<-nrow(df); out<-rep(NA_real_,n)
  same <- df$pid[-1]==df$pid[-n] & df$day[-1]==df$day[-n] & (df$beep[-1]-df$beep[-n])==1
  out[-1] <- ifelse(same, df[[v]][-n], NA_real_); out }
for (v in vars) d[[paste0("L_", v)]] <- make_lag(d, v)

resid_long <- list(); diag_rows <- list()
for (yv in vars) {
  form <- stats::as.formula(paste0(yv, " ~ ", paste0("L_", vars, collapse = " + "), " + (1|pid)"))
  sub <- d[stats::complete.cases(d[, c(yv, paste0("L_", vars), "pid")]), ]
  m <- lme4::lmer(form, data = sub, control = lme4::lmerControl(calc.derivs = FALSE))
  r <- stats::residuals(m); f <- stats::fitted(m)
  sw <- tryCatch(stats::shapiro.test(if (length(r) > 5000) sample(r, 5000) else r),
                 error = function(e) list(statistic = NA, p.value = NA))
  # within-person lag-1 residual autocorrelation
  sub$res <- r
  acf1 <- sapply(split(sub$res, sub$pid), function(z){
    if (length(z) > 3) stats::cor(z[-1], z[-length(z)], use = "complete.obs") else NA })
  bp <- stats::cor(abs(r), f)  # |resid| vs fitted association (heteroscedasticity index)
  diag_rows[[yv]] <- data.frame(
    node = yv, n = nrow(sub),
    shapiro_W = round(as.numeric(sw$statistic), 3), shapiro_p = signif(sw$p.value, 3),
    resid_skew = round(skewf(r), 3), resid_kurtosis = round(kurtf(r), 3),
    mean_within_acf1 = round(mean(acf1, na.rm = TRUE), 3),
    abs_resid_fitted_cor = round(bp, 3))
  resid_long[[yv]] <- data.frame(node = yv, fitted = f, residual = r)
}
diag <- do.call(rbind, diag_rows)
write_result(diag, "05_mlvar_residual_diagnostics.csv")
write_result(do.call(rbind, resid_long), "05_mlvar_residuals_long.csv", DIR_NETWORKS)
cat("\nmlVAR residual diagnostics:\n"); print(diag, row.names = FALSE)
cat("\nNote: residual normality is expected to be mildly violated for bounded 0-10 items;\n",
    "mlVAR fixed effects are robust to this, and the bootstrap (stage 10) provides\n",
    "distribution-free CIs as a cross-check.\n", sep = "")
