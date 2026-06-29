# Robustness 06 - Compliance-threshold sensitivity.
#
# mlVAR flags that a handful of participants contribute very few usable lag-1 observations
# (within-person centering with too few points can bias self-loops). We refit the primary
# network on the subset of participants with at least 40 completed prompts (a stricter
# data-density criterion) and compare to the full-sample network. Stability indicates the
# results are not driven by sparsely sampled participants.

this <- normalizePath(sub("--file=", "",
  grep("--file=", commandArgs(FALSE), value = TRUE)[1]), mustWork = FALSE)
lib <- file.path(dirname(this), "..", "..", "..", "lib")
source(file.path(lib, "common.R"))
source(file.path(lib, "mlvar_helpers.R"))
need(c("mlVAR"))

THRESHOLD <- 40
d <- read_ema()
d$completed <- as.logical(d$completed)
ncomp <- tapply(d$completed, d$pid, sum, na.rm = TRUE)
keep_ids <- names(ncomp)[ncomp >= THRESHOLD]
cat(sprintf("[threshold] retaining %d / %d participants with >= %d completed prompts\n",
            length(keep_ids), length(ncomp), THRESHOLD))
dk <- d[d$pid %in% keep_ids, ]

m <- fit_mlvar(dk, CORE_VARS)
edges <- mlvar_temporal_edges(m)
write_result(edges, "robust_threshold40_temporal_edges.csv", DIR_NETWORKS)

prim <- utils::read.csv(file.path(DIR_NETWORKS, "05_mlvar_core_temporal_edges.csv"))
prim$edge <- paste0(prim$from, "__to__", prim$to)
cmp <- compare_edges(prim, edges, "thr40")
write_result(cmp, "robust_threshold40_compare.csv", DIR_NETWORKS)
cat(sprintf("[threshold] edge-weight r = %.3f, max |diff| = %.3f, sign flips = %d\n",
            attr(cmp, "r"), attr(cmp, "max_abs_diff"), attr(cmp, "n_sign_flip")))
