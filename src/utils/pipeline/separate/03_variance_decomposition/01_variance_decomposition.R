# Stage 03 - Multilevel variance decomposition (ICC).
#
# Why: idiographic / within-person network modelling is only justified if a meaningful
# share of variance lives WITHIN persons (and within days). This stage partitions the
# variance of each momentary variable into:
#   - between persons,
#   - between days within a person,
#   - within days (residual, the moment-to-moment signal the VAR models use).
#
# Models: null (intercept-only) mixed models with random person, and nested person/day
# intercepts (lme4). Output feeds MAIN figure (variance decomposition) and a main table.

suppressPackageStartupMessages({
  this <- normalizePath(sub("--file=", "",
    grep("--file=", commandArgs(FALSE), value = TRUE)[1]), mustWork = FALSE)
})
lib <- file.path(dirname(this), "..", "..", "..", "lib")
source(file.path(lib, "common.R"))
need(c("lme4"))

d <- read_ema()
d$pid <- factor(d$pid)
d$day <- factor(d$day)

vars <- c(PIJN = "Pain", MOE = "Fatigue", STRESS = "Stress",
          ENMO_log = "Activity (log ENMO)",
          EIGENEFF = "Self-efficacy", INTENTIE = "Intention",
          UITKOMSTVERW = "Rest-expectancy")

res <- list()
for (v in names(vars)) {
  dd <- d[!is.na(d[[v]]), ]
  dd$y <- dd[[v]]
  # person-only null model -> ICC(person)
  m1 <- lme4::lmer(y ~ 1 + (1 | pid), data = dd, REML = TRUE,
                   control = lme4::lmerControl(calc.derivs = FALSE))
  vc1 <- as.data.frame(lme4::VarCorr(m1))
  v_pid1 <- vc1$vcov[vc1$grp == "pid"]
  v_res1 <- vc1$vcov[vc1$grp == "Residual"]
  icc_person <- v_pid1 / (v_pid1 + v_res1)

  # nested person/day null model -> partition person / day-within-person / residual
  m2 <- lme4::lmer(y ~ 1 + (1 | pid/day), data = dd, REML = TRUE,
                   control = lme4::lmerControl(calc.derivs = FALSE))
  vc2 <- as.data.frame(lme4::VarCorr(m2))
  v_day <- vc2$vcov[vc2$grp == "day:pid"]
  v_pid2 <- vc2$vcov[vc2$grp == "pid"]
  v_res2 <- vc2$vcov[vc2$grp == "Residual"]
  tot2 <- v_day + v_pid2 + v_res2

  res[[v]] <- data.frame(
    variable = v,
    label = unname(vars[v]),
    n_obs = nrow(dd),
    n_persons = nlevels(droplevels(dd$pid)),
    icc_person = round(icc_person, 3),
    var_between_person = round(v_pid2 / tot2, 3),
    var_between_day = round(v_day / tot2, 3),
    var_within_day = round(v_res2 / tot2, 3)
  )
}

out <- do.call(rbind, res)
rownames(out) <- NULL
print(out)
write_result(out, "03_variance_decomposition.csv")

cat("\nInterpretation: 'var_within_day' is the share of variance available to the\n",
    "moment-to-moment (lag-1) network. Higher within-person variance => stronger\n",
    "justification for idiographic / multilevel VAR modelling.\n", sep = "")
