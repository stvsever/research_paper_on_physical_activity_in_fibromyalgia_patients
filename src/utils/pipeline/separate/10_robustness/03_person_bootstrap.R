# Robustness 03 - Person-level (cluster) bootstrap of the temporal network.
#
# Annick's central concern is the low number of observations per person. Beyond the
# model-based standard errors, we quantify the sampling stability of the group-level edges
# with a nonparametric cluster bootstrap: resample the 34 participants WITH replacement
# (keeping each person's full series intact), refit the primary mlVAR, and repeat B times.
# We report percentile 95% CIs and the proportion of bootstrap samples in which each edge
# keeps its sign (sign-consistency). This is robust to the distributional assumptions of
# the model-based SEs and directly addresses small-sample stability.

this <- normalizePath(sub("--file=", "",
  grep("--file=", commandArgs(FALSE), value = TRUE)[1]), mustWork = FALSE)
lib <- file.path(dirname(this), "..", "..", "..", "lib")
source(file.path(lib, "common.R"))
source(file.path(lib, "mlvar_helpers.R"))
need(c("mlVAR"))

args <- commandArgs(trailingOnly = TRUE)
B <- if (length(args) >= 1) as.integer(args[1]) else 500

d <- read_ema()
vars <- CORE_VARS
ids <- sort(unique(d$pid))
n <- length(ids)

boot_rows <- list()
done <- 0
for (b in seq_len(B)) {
  set.seed(20260626 + b)               # distinct, reproducible resample each iteration
  samp <- sample(ids, n, replace = TRUE)
  # rebuild data with unique relabelled ids so duplicates are distinct clusters
  parts <- lapply(seq_along(samp), function(k) {
    s <- d[d$pid == samp[k], ]
    s$pid <- paste0(samp[k], "_", k)
    s
  })
  db <- do.call(rbind, parts)
  m <- tryCatch(fit_mlvar(db, vars), error = function(e) NULL)
  if (is.null(m)) next
  e <- mlvar_temporal_edges(m)
  e$b <- b
  boot_rows[[length(boot_rows) + 1]] <- e[, c("b", "edge", "from", "to", "weight")]
  done <- done + 1
  if (b %% 50 == 0) cat(sprintf("  bootstrap %d/%d\n", b, B))
}
boot <- do.call(rbind, boot_rows)
write_result(boot, "robust_bootstrap_edges_long.csv", DIR_NETWORKS)

prim <- utils::read.csv(file.path(DIR_NETWORKS, "05_mlvar_core_temporal_edges.csv"))
prim$edge <- paste0(prim$from, "__to__", prim$to)

agg <- do.call(rbind, lapply(split(boot, boot$edge), function(g) {
  w <- g$weight
  data.frame(edge = g$edge[1], from = g$from[1], to = g$to[1],
             boot_mean = mean(w),
             ci_lo = stats::quantile(w, 0.025, names = FALSE),
             ci_hi = stats::quantile(w, 0.975, names = FALSE),
             prop_sign_consistent = max(mean(w > 0), mean(w < 0)))
}))
agg <- merge(agg, prim[, c("edge", "weight", "P")], by = "edge")
names(agg)[names(agg) == "weight"] <- "primary_weight"
agg[, sapply(agg, is.numeric)] <- round(agg[, sapply(agg, is.numeric)], 3)
agg <- agg[order(-abs(agg$primary_weight)), ]
write_result(agg, "robust_bootstrap_summary.csv", DIR_NETWORKS)

cat(sprintf("\n[bootstrap] B = %d successful resamples\n", done))
cat("Key cross-lagged edges (percentile 95% CI, sign-consistency):\n")
key <- agg[agg$from != agg$to, ]
print(utils::head(key[, c("edge", "primary_weight", "ci_lo", "ci_hi",
                          "prop_sign_consistent")], 8), row.names = FALSE)
