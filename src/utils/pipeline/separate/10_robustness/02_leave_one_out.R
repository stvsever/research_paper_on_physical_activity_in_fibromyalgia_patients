# Robustness 02 - Leave-one-participant-out (LOPO) stability.
#
# With only N = 34 persons, a single influential participant could drive a group-level
# edge. We refit the primary mlVAR 34 times, each time dropping one participant, and record
# every temporal edge across the refits. For each edge we report the full fixed-effect
# range, SD, and how often it stays on the same side of zero. Stable edges (narrow range,
# consistent sign) are trustworthy; volatile edges are flagged.

this <- normalizePath(sub("--file=", "",
  grep("--file=", commandArgs(FALSE), value = TRUE)[1]), mustWork = FALSE)
lib <- file.path(dirname(this), "..", "..", "..", "lib")
source(file.path(lib, "common.R"))
source(file.path(lib, "mlvar_helpers.R"))
need(c("mlVAR"))

d <- read_ema()
vars <- CORE_VARS
ids <- sort(unique(d$pid))

rows <- list()
for (i in seq_along(ids)) {
  di <- d[d$pid != ids[i], ]
  m <- tryCatch(fit_mlvar(di, vars), error = function(e) NULL)
  if (is.null(m)) next
  e <- mlvar_temporal_edges(m)
  e$dropped <- ids[i]
  rows[[length(rows) + 1]] <- e[, c("dropped", "edge", "from", "to", "weight", "P")]
  cat(sprintf("  LOPO %d/%d (dropped %s)\n", i, length(ids), ids[i]))
}
loo <- do.call(rbind, rows)
write_result(loo, "robust_loo_edges_long.csv", DIR_NETWORKS)

# Per-edge stability summary.
agg <- do.call(rbind, lapply(split(loo, loo$edge), function(g) {
  data.frame(edge = g$edge[1], from = g$from[1], to = g$to[1],
             mean = mean(g$weight), sd = stats::sd(g$weight),
             min = min(g$weight), max = max(g$weight),
             prop_same_sign = max(mean(g$weight > 0), mean(g$weight < 0)),
             prop_p_lt_05 = mean(g$P < 0.05))
}))
agg[, 4:9] <- round(agg[, 4:9], 3)
agg <- agg[order(-abs(agg$mean)), ]
write_result(agg, "robust_loo_summary.csv", DIR_NETWORKS)

cat("\n[LOPO] key edges (range across 34 refits):\n")
key <- agg[agg$from != agg$to, ]
print(utils::head(key[, c("edge", "mean", "min", "max", "prop_same_sign")], 8),
      row.names = FALSE)
