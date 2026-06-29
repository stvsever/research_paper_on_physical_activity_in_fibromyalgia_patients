# Robustness 08 - Permutation inference for the RQ2 network <-> POAM-P link.
#
# The link analyses (stage 09) use rank-based tests, but with N = 30 the asymptotic
# p-values are approximate. Here we recompute exact-style p-values by permutation
# (label shuffling, 10,000 resamples) for the two headline link results:
#   (a) Kruskal-Wallis of Pain->Activity coupling across POAM-P dominant patterns,
#   (b) Spearman correlation of each per-person coupling with the POAM-P Avoidance score.
# Permutation p-values are valid under minimal assumptions and appropriate at this N.

this <- normalizePath(sub("--file=", "",
  grep("--file=", commandArgs(FALSE), value = TRUE)[1]), mustWork = FALSE)
lib <- file.path(dirname(this), "..", "..", "..", "lib")
source(file.path(lib, "common.R"))

set.seed(20260626)
NPERM <- 10000
fr <- utils::read.csv(file.path(DIR_PROCESSED, "link_analysis_frame.csv"))

couplings <- c(PIJN__to__ENMO_log = "Pain -> Activity",
               ENMO_log__to__PIJN = "Activity -> Pain",
               ENMO_log__to__MOE = "Activity -> Fatigue",
               STRESS__to__ENMO_log = "Stress -> Activity")

# (a) Kruskal-Wallis permutation test by dominant pattern
kw_rows <- list()
for (cp in names(couplings)) {
  sub <- fr[!is.na(fr[[cp]]) & !is.na(fr$dominant_pattern), ]
  y <- sub[[cp]]; g <- factor(sub$dominant_pattern)
  obs <- stats::kruskal.test(y, g)$statistic
  perm <- replicate(NPERM, stats::kruskal.test(y, sample(g))$statistic)
  p_perm <- (1 + sum(perm >= obs)) / (NPERM + 1)
  kw_rows[[cp]] <- data.frame(coupling = couplings[cp], test = "Kruskal-Wallis by POAM-P type",
                              statistic = round(as.numeric(obs), 3),
                              p_asymptotic = round(stats::kruskal.test(y, g)$p.value, 4),
                              p_permutation = round(p_perm, 4), n = length(y))
}
kw <- do.call(rbind, kw_rows)

# (b) Spearman permutation test vs Avoidance subscale
sp_rows <- list()
for (cp in names(couplings)) {
  sub <- fr[!is.na(fr[[cp]]) & !is.na(fr$POAMP_Avoidance), ]
  x <- sub[[cp]]; z <- sub$POAMP_Avoidance
  obs <- suppressWarnings(stats::cor(x, z, method = "spearman"))
  perm <- replicate(NPERM, suppressWarnings(stats::cor(x, sample(z), method = "spearman")))
  p_perm <- (1 + sum(abs(perm) >= abs(obs))) / (NPERM + 1)
  sp_rows[[cp]] <- data.frame(coupling = couplings[cp],
                              test = "Spearman vs POAM-P Avoidance",
                              rho = round(obs, 3),
                              p_permutation = round(p_perm, 4), n = length(x))
}
sp <- do.call(rbind, sp_rows)

write_result(kw, "robust_permutation_kruskal.csv")
write_result(sp, "robust_permutation_spearman.csv")
cat("\n[permutation] Kruskal-Wallis by POAM-P dominant pattern:\n"); print(kw, row.names = FALSE)
cat("\n[permutation] Spearman vs Avoidance subscale:\n"); print(sp, row.names = FALSE)
