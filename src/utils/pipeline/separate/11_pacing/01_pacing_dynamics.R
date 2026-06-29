# Supplement (Stage 11) - Pacing behaviour dynamics.
#
# Beyond the core symptom-activity system, the EMA captured momentary pacing behaviour on
# prompts where the person had been active: SPEED (deliberate slowing), PIECES (breaking
# tasks into parts), BREAKS (inserting extra breaks). These operationalize the adaptive
# self-regulation that the POAM-P pacing subscale measures at baseline. This supplement:
#   (1) describes the three pacing items (conditional on having been active),
#   (2) tests whether momentary pain / fatigue / stress predict more pacing (multilevel),
#   (3) tests whether momentary pacing predicts the objective activity in that window.

this <- normalizePath(sub("--file=", "",
  grep("--file=", commandArgs(FALSE), value = TRUE)[1]), mustWork = FALSE)
lib <- file.path(dirname(this), "..", "..", "..", "lib")
source(file.path(lib, "common.R"))
need(c("lme4", "lmerTest"))

d <- read_ema()
d$pid <- factor(d$pid)
pacing <- c("SPEED", "PIECES", "BREAKS")

# (1) descriptives (rows where pacing was shown, i.e. participant had been active)
desc <- do.call(rbind, lapply(pacing, function(v) {
  x <- d[[v]]
  data.frame(item = v, n_obs = sum(!is.na(x)),
             mean = round(mean(x, na.rm = TRUE), 2), sd = round(sd(x, na.rm = TRUE), 2),
             median = stats::median(x, na.rm = TRUE),
             min = min(x, na.rm = TRUE), max = max(x, na.rm = TRUE))
}))
write_result(desc, "pacing_descriptives.csv")
cat("Pacing item descriptives:\n"); print(desc, row.names = FALSE)

# Composite pacing index (mean of available items) for the models.
d$PACING <- rowMeans(d[, pacing], na.rm = TRUE)
d$PACING[is.nan(d$PACING)] <- NA

# within-person centering helper
wpc <- function(v) ave(d[[v]], d$pid, FUN = function(x) x - mean(x, na.rm = TRUE))
for (v in c("PIJN", "MOE", "STRESS", "PACING", "ENMO_log")) d[[paste0("c", v)]] <- wpc(v)

# (2) do momentary symptoms predict concurrent pacing? (within-person effects)
m_sym <- lmerTest::lmer(PACING ~ cPIJN + cMOE + cSTRESS + (1 | pid), data = d,
                        control = lme4::lmerControl(calc.derivs = FALSE))
co <- summary(m_sym)$coefficients
tab1 <- data.frame(model = "pacing ~ symptoms (within)",
                   term = rownames(co), estimate = round(co[, 1], 3),
                   SE = round(co[, 2], 3), p = round(co[, ncol(co)], 4))
write_result(tab1, "pacing_on_symptoms.csv")
cat("\n(2) Within-person symptoms -> concurrent pacing:\n"); print(tab1, row.names = FALSE)

# (3) does momentary pacing relate to the objective activity in the window?
m_act <- lmerTest::lmer(ENMO_log ~ cPACING + (1 | pid), data = d,
                        control = lme4::lmerControl(calc.derivs = FALSE))
co2 <- summary(m_act)$coefficients
tab2 <- data.frame(model = "logENMO ~ pacing (within)",
                   term = rownames(co2), estimate = round(co2[, 1], 3),
                   SE = round(co2[, 2], 3), p = round(co2[, ncol(co2)], 4))
write_result(tab2, "pacing_on_activity.csv")
cat("\n(3) Within-person pacing -> objective activity (logENMO):\n")
print(tab2, row.names = FALSE)
