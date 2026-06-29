# Stage 06 - S-GIMME (complementary idiographic / data-driven subgrouping).
#
# Annick proposed S-GIMME (Subgrouping Group Iterative Multiple Model Estimation).
# GIMME estimates a unified SEM per person that contains (a) a group-level structure
# recovered across persons, (b) data-driven subgroups (S-GIMME), and (c) individual-
# specific paths, for both contemporaneous and lag-1 (directed) relations.
#
# Caveat (reported, not hidden): GIMME is recommended at ~100+ time points per person.
# Here T is ~44, with missingness, so individual maps are expected to be sparse and the
# subgroup solution unstable. We therefore run S-GIMME as a COMPLEMENT to mlVAR and read
# it qualitatively: does a data-driven method recover a similar group backbone, and does
# it spontaneously suggest subgroups? Per-person complete-case series are used; a person
# is included only with >= 25 complete observations on the four core nodes.

this <- normalizePath(sub("--file=", "",
  grep("--file=", commandArgs(FALSE), value = TRUE)[1]), mustWork = FALSE)
lib <- file.path(dirname(this), "..", "..", "..", "lib")
source(file.path(lib, "common.R"))
need(c("gimme"))

d <- read_ema()
vars <- c("PIJN", "MOE", "STRESS", "ENMO_log")
MIN_OBS <- 30  # gimme hard-requires >= 30 complete timepoints per person

# Build per-person, time-ordered, complete-case matrices.
d <- d[order(d$pid, d$day, d$beep), ]
ids <- unique(d$pid)

out_dir <- file.path(DIR_MODELS, "gimme_out")
if (dir.exists(out_dir)) unlink(out_dir, recursive = TRUE)
data_dir <- file.path(out_dir, "data")
dir.create(data_dir, recursive = TRUE, showWarnings = FALSE)

# gimme is most robust when fed a directory of per-person CSVs (avoids an in-memory
# list bug). Write standardized complete-case series, one file per included person.
incl <- data.frame(pid = character(), n_complete = integer(), included = logical())
for (id in ids) {
  sub <- d[d$pid == id, vars]
  cc <- stats::complete.cases(sub)
  sub <- sub[cc, , drop = FALSE]
  n <- nrow(sub)
  ok <- n >= MIN_OBS
  incl <- rbind(incl, data.frame(pid = id, n_complete = n, included = ok))
  if (ok) {
    m <- scale(as.matrix(sub))
    colnames(m) <- vars
    utils::write.csv(as.data.frame(m),
                     file.path(data_dir, paste0(id, ".csv")), row.names = FALSE)
  }
}
write_result(incl, "06_sgimme_inclusion.csv", DIR_TABLES)
cat(sprintf("[S-GIMME] %d / %d persons meet T>=%d\n",
            sum(incl$included), length(ids), MIN_OBS))

fit_dir <- file.path(out_dir, "fit")
set.seed(20260626)
# NB: data are already within-person standardized; do NOT pass standardize = TRUE, and do
# NOT wrap this call in tryCatch -- gimme uses non-standard evaluation on its arguments and
# both paths trigger a "promise already under evaluation" bug in this build. A hard failure
# here is acceptable: the orchestrator surfaces it. subgroup = TRUE requests the S-GIMME
# data-driven subgrouping (Walktrap community detection on the similarity matrix).
fit <- gimme::gimme(
  data = data_dir, out = fit_dir, sep = ",", header = TRUE,
  ar = TRUE, plot = FALSE, subgroup = TRUE,
  groupcutoff = 0.75, subcutoff = 0.50
)

if (!is.null(fit)) {
  saveRDS(fit, file.path(DIR_MODELS, "sgimme_fit.rds"))

  # gimme writes tidy CSVs to the output dir; curate them into results/.
  sf <- utils::read.csv(file.path(fit_dir, "summaryFit.csv"))
  memb <- sf[, intersect(c("file", "sub_membership", "status", "rmsea", "cfi", "srmr"),
                         names(sf))]
  names(memb)[names(memb) == "file"] <- "pid"
  names(memb)[names(memb) == "sub_membership"] <- "subgroup"
  write_result(memb, "06_sgimme_subgroup_membership.csv", DIR_TABLES)

  spc <- utils::read.csv(file.path(fit_dir, "summaryPathCounts.csv"))
  spc$path <- paste(spc$lhs, spc$op, spc$rhs)
  write_result(spc, "06_sgimme_summary_path_counts.csv", DIR_NETWORKS)

  ipe <- utils::read.csv(file.path(fit_dir, "indivPathEstimates.csv"))
  write_result(ipe, "06_sgimme_individual_path_estimates.csv", DIR_NETWORKS)

  n_sub <- length(unique(memb$subgroup))
  sizes <- as.data.frame(table(subgroup = memb$subgroup))
  modularity <- suppressWarnings(stats::na.omit(sf$modularity))
  cat(sprintf("\n[S-GIMME] %d persons fit; %d subgroups (modularity = %.3f)\n",
              nrow(memb), n_sub,
              ifelse(length(modularity) > 0, modularity[1], NA_real_)))
  cat("[S-GIMME] subgroup sizes:\n"); print(sizes)
  cat("\n[S-GIMME] non-AR paths present in the most individuals:\n")
  cross <- spc[!grepl("lag", spc$rhs) | spc$lhs != sub("lag", "", spc$rhs), ]
  cross <- spc[spc$count.group == 0, ]
  print(utils::head(cross[order(-cross$count.ind),
                          c("path", "count.ind", "count.subgroup1")], 8),
        row.names = FALSE)
} else {
  cat("[S-GIMME] model did not converge / errored; see message above.\n")
}
