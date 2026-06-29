# Robustness 01 - Stationarity: detrended mlVAR.
#
# Stage 04 showed a minority of individual series carry a linear time trend (a threat to
# the weak-stationarity assumption of VAR models). Here we ACT on that: within each person
# we remove a linear trend over the observation index from every core variable, then refit
# the primary mlVAR on the residuals and compare the temporal network to the primary fit.
# If the network is stable, the lag-1 dynamics are not artefacts of slow drift.

this <- normalizePath(sub("--file=", "",
  grep("--file=", commandArgs(FALSE), value = TRUE)[1]), mustWork = FALSE)
lib <- file.path(dirname(this), "..", "..", "..", "lib")
source(file.path(lib, "common.R"))
source(file.path(lib, "mlvar_helpers.R"))
need(c("mlVAR"))

d <- read_ema()
vars <- CORE_VARS

# Within-person linear detrending: residuals of y ~ obs, computed per person, NAs kept.
detrend <- function(y, t, pid) {
  out <- y
  for (id in unique(pid)) {
    idx <- which(pid == id)
    yi <- y[idx]; ti <- t[idx]
    ok <- !is.na(yi)
    if (sum(ok) >= 5 && stats::sd(yi[ok]) > 0) {
      fit <- stats::lm(yi[ok] ~ ti[ok])
      r <- rep(NA_real_, length(yi))
      r[ok] <- stats::residuals(fit)
      out[idx] <- r
    }
  }
  out
}

dd <- d
for (v in vars) dd[[v]] <- detrend(d[[v]], d$obs, d$pid)

m <- fit_mlvar(dd, vars)
saveRDS(m, file.path(DIR_MODELS, "mlvar_detrended.rds"))
edges <- mlvar_temporal_edges(m)
write_result(edges, "robust_detrended_temporal_edges.csv", DIR_NETWORKS)

prim <- utils::read.csv(file.path(DIR_NETWORKS, "05_mlvar_core_temporal_edges.csv"))
prim$edge <- paste0(prim$from, "__to__", prim$to)
cmp <- compare_edges(prim, edges, "detrended")
write_result(cmp, "robust_detrended_compare.csv", DIR_NETWORKS)

cat(sprintf("\n[detrended] edge-weight r(primary, detrended) = %.3f, max |diff| = %.3f, sign flips = %d\n",
            attr(cmp, "r"), attr(cmp, "max_abs_diff"), attr(cmp, "n_sign_flip")))
