# Robustness 05 - Could-not-move sensitivity analysis.
#
# On ~13% of answered prompts participants reported being in a situation that did not
# allow movement (MOGELIJKHEID_BEW == 0). Annick suggested re-estimating without those
# trials. We refit the primary 4-node mlVAR on movement-possible prompts only and compare
# the temporal network to the primary model. If the conclusions are stable, the primary
# results are not driven by structurally inactive moments.
#
# The movement-only fit is produced by the primary script with the "movement_only" flag;
# this script ensures that fit exists, then quantifies the difference.

this <- normalizePath(sub("--file=", "",
  grep("--file=", commandArgs(FALSE), value = TRUE)[1]), mustWork = FALSE)
lib <- file.path(dirname(this), "..", "..", "..", "lib")
source(file.path(lib, "common.R"))

primary_edges <- file.path(DIR_NETWORKS, "05_mlvar_core_temporal_edges.csv")
mov_edges <- file.path(DIR_NETWORKS, "05_mlvar_movementonly_temporal_edges.csv")

if (!file.exists(mov_edges)) {
  core_script <- normalizePath(file.path(dirname(this), "..", "05_mlvar",
                                         "01_mlvar_core.R"))
  cat("[cantmove] producing movement-only fit via primary script...\n")
  status <- system2("Rscript", c("--vanilla", shQuote(core_script), "movement_only"),
                    stdout = FALSE, stderr = FALSE)
  if (status != 0 || !file.exists(mov_edges))
    stop("movement-only mlVAR did not produce edge output")
}

prim <- utils::read.csv(primary_edges)
mov <- utils::read.csv(mov_edges)
cmp <- merge(prim[, c("from", "to", "weight", "P")],
             mov[, c("from", "to", "weight", "P")],
             by = c("from", "to"), suffixes = c("_all", "_movement"))
cmp$abs_diff <- round(abs(cmp$weight_all - cmp$weight_movement), 3)
cmp$sign_flip <- sign(cmp$weight_all) != sign(cmp$weight_movement)
cmp <- cmp[order(-cmp$abs_diff), ]
write_result(cmp, "cantmove_edge_comparison.csv", DIR_NETWORKS)

cat(sprintf("\n[cantmove] edge-weight correlation (all vs movement-only): r = %.3f\n",
            stats::cor(cmp$weight_all, cmp$weight_movement)))
cat(sprintf("[cantmove] max |change|: %.3f ; sign flips among |w|>0.05: %d\n",
            max(cmp$abs_diff),
            sum(cmp$sign_flip & pmax(abs(cmp$weight_all), abs(cmp$weight_movement)) > 0.05)))
cat("\nLargest changes:\n")
print(utils::head(cmp[, c("from", "to", "weight_all", "weight_movement", "abs_diff")], 6),
      row.names = FALSE)
