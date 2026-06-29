# Robustness 07 - ENMO transformation sensitivity.
#
# The primary model uses log(ENMO) because raw ENMO is right-skewed (stage 04). Here we
# refit the network using the raw and square-root transforms of activity and compare the
# temporal edges. Because mlVAR within-person standardizes each node, the transform mainly
# affects the shape of the activity distribution; stability across transforms shows the
# activity edges are not an artefact of the log choice.

this <- normalizePath(sub("--file=", "",
  grep("--file=", commandArgs(FALSE), value = TRUE)[1]), mustWork = FALSE)
lib <- file.path(dirname(this), "..", "..", "..", "lib")
source(file.path(lib, "common.R"))
source(file.path(lib, "mlvar_helpers.R"))
need(c("mlVAR"))

d <- read_ema()
prim <- utils::read.csv(file.path(DIR_NETWORKS, "05_mlvar_core_temporal_edges.csv"))
prim$edge <- paste0(prim$from, "__to__", prim$to)

out <- list()
for (tf in c("raw", "sqrt")) {
  dd <- d
  dd$ENMO_log <- if (tf == "raw") dd$ENMO else dd$ENMO_sqrt  # reuse the ENMO_log slot
  m <- fit_mlvar(dd, CORE_VARS)
  e <- mlvar_temporal_edges(m)
  cmp <- compare_edges(prim, e, tf)
  out[[tf]] <- data.frame(transform = tf, r_vs_log = attr(cmp, "r"),
                          max_abs_diff = attr(cmp, "max_abs_diff"),
                          sign_flips = attr(cmp, "n_sign_flip"))
  write_result(e, sprintf("robust_enmo_%s_temporal_edges.csv", tf), DIR_NETWORKS)
}
summ <- do.call(rbind, out)
summ[, 2:3] <- round(summ[, 2:3], 3)
write_result(summ, "robust_enmo_transform_compare.csv", DIR_NETWORKS)
cat("\n[ENMO transform] agreement of temporal network with the log-based primary model:\n")
print(summ, row.names = FALSE)
