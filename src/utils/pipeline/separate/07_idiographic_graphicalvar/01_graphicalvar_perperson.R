# Stage 07 - Per-person graphicalVAR (idiographic feasibility / sensitivity).
#
# This stage fits a fully SEPARATE regularized VAR network for each individual
# (graphicalVAR: LASSO-penalized temporal + contemporaneous networks selected by EBIC).
# Its purpose is to answer Annick's central question directly and empirically: "can we
# justify individual networks at all?" By fitting them and quantifying their sparsity and
# stability, we show concretely how much (or how little) signal a fully idiographic model
# recovers at T ~ 44, motivating the multilevel (mlVAR) primary analysis.
#
# Outputs: per-person edge lists, a per-person summary (density, key edges), and a tally
# of how often each directed edge is selected across individuals.

this <- normalizePath(sub("--file=", "",
  grep("--file=", commandArgs(FALSE), value = TRUE)[1]), mustWork = FALSE)
lib <- file.path(dirname(this), "..", "..", "..", "lib")
source(file.path(lib, "common.R"))
need(c("graphicalVAR"))

d <- read_ema()
vars <- c("PIJN", "MOE", "STRESS", "ENMO_log")
labels <- c(PIJN = "Pain", MOE = "Fatigue", STRESS = "Stress", ENMO_log = "Activity")
MIN_OBS <- 30

d <- d[order(d$pid, d$day, d$beep), ]
ids <- unique(d$pid)

all_edges <- list()
summ <- list()
for (id in ids) {
  sub <- d[d$pid == id, c("day", "beep", vars)]
  n_cc <- sum(stats::complete.cases(sub[, vars]))
  if (n_cc < MIN_OBS) {
    summ[[id]] <- data.frame(pid = id, n_complete = n_cc, fitted = FALSE,
                             n_temporal_edges = NA, n_contemp_edges = NA,
                             temporal_density = NA, pain_to_activity = NA,
                             activity_to_pain = NA)
    next
  }
  fit <- tryCatch(
    graphicalVAR::graphicalVAR(
      sub, vars = vars, beepvar = "beep", dayvar = "day",
      nLambda = 50, gamma = 0.25, scale = TRUE, verbose = FALSE),
    error = function(e) NULL)
  if (is.null(fit)) {
    summ[[id]] <- data.frame(pid = id, n_complete = n_cc, fitted = FALSE,
                             n_temporal_edges = NA, n_contemp_edges = NA,
                             temporal_density = NA, pain_to_activity = NA,
                             activity_to_pain = NA)
    next
  }
  # PDC = directed temporal matrix [from row, to col]; PCC = contemporaneous partial corr.
  PDC <- fit$PDC
  PCC <- fit$PCC
  rownames(PDC) <- colnames(PDC) <- vars
  rownames(PCC) <- colnames(PCC) <- vars

  for (i in vars) for (j in vars) {
    all_edges[[length(all_edges) + 1]] <- data.frame(
      pid = id, type = "temporal", from = i, to = j, weight = PDC[i, j])
  }
  for (i in vars) for (j in vars) if (i != j) {
    all_edges[[length(all_edges) + 1]] <- data.frame(
      pid = id, type = "contemporaneous", from = i, to = j, weight = PCC[i, j])
  }
  summ[[id]] <- data.frame(
    pid = id, n_complete = n_cc, fitted = TRUE,
    n_temporal_edges = sum(PDC != 0),
    n_contemp_edges = sum(PCC[upper.tri(PCC)] != 0),
    temporal_density = mean(PDC != 0),
    pain_to_activity = PDC["PIJN", "ENMO_log"],
    activity_to_pain = PDC["ENMO_log", "PIJN"])
}

edges_df <- do.call(rbind, all_edges)
summ_df <- do.call(rbind, summ)
write_result(edges_df, "07_graphicalvar_individual_edges.csv", DIR_NETWORKS)
write_result(summ_df, "07_graphicalvar_individual_summary.csv", DIR_TABLES)

fitted <- summ_df[summ_df$fitted, ]
cat(sprintf("\n[graphicalVAR] fitted %d / %d persons (T >= %d complete)\n",
            nrow(fitted), nrow(summ_df), MIN_OBS))
cat(sprintf("[graphicalVAR] temporal edges per person: median %.0f (range %d-%d) out of 16 possible\n",
            median(fitted$n_temporal_edges), min(fitted$n_temporal_edges),
            max(fitted$n_temporal_edges)))
cat(sprintf("[graphicalVAR] persons with a nonzero Pain->Activity temporal edge: %d (%d positive, %d negative)\n",
            sum(fitted$pain_to_activity != 0),
            sum(fitted$pain_to_activity > 0), sum(fitted$pain_to_activity < 0)))
cat(sprintf("[graphicalVAR] persons with a nonzero Activity->Pain temporal edge: %d (%d positive, %d negative)\n",
            sum(fitted$activity_to_pain != 0),
            sum(fitted$activity_to_pain > 0), sum(fitted$activity_to_pain < 0)))

# Edge-selection frequency across persons (directed temporal).
tmp <- edges_df[edges_df$type == "temporal", ]
tmp$selected <- tmp$weight != 0
freq <- aggregate(selected ~ from + to, data = tmp, FUN = function(x) mean(x))
freq$pct_selected <- round(100 * freq$selected, 1)
freq$selected <- NULL
write_result(freq[order(-freq$pct_selected), ],
             "07_graphicalvar_edge_selection_freq.csv", DIR_NETWORKS)
