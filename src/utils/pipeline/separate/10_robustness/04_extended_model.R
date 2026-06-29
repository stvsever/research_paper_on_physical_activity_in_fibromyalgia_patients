# Robustness 04 - Extended mlVAR with motivational (HAPA) nodes.
#
# Annick asked whether self-efficacy, intention and outcome expectancy can be added as
# extra nodes "depending on how many nodes the sample size and completed triggers allow".
# This stage first adds Self-efficacy and Intention to the core 4-node network, yielding the
# previously reported 6-node mlVAR. It then adds rest-favouring outcome expectancy as a
# seventh node. Both extensions report whether the core four-node temporal structure changes
# when motivational states are included.

this <- normalizePath(sub("--file=", "",
  grep("--file=", commandArgs(FALSE), value = TRUE)[1]), mustWork = FALSE)
lib <- file.path(dirname(this), "..", "..", "..", "lib")
source(file.path(lib, "common.R"))
need(c("mlVAR"))

d <- read_ema()
d$pid <- as.factor(d$pid)
core_nodes <- c("PIJN", "MOE", "STRESS", "ENMO_log")
prim <- utils::read.csv(file.path(DIR_NETWORKS, "05_mlvar_core_temporal_edges.csv"))

fit_extended <- function(vars, model_name, out_prefix, compare_file, compare_suffix) {
  set.seed(20260626)
  m <- mlVAR(d, vars = vars, idvar = "pid", dayvar = "day", beepvar = "beep",
             lags = 1, temporal = "orthogonal", contemporaneous = "orthogonal",
             estimator = "lmer", scale = TRUE, verbose = FALSE)
  saveRDS(m, file.path(DIR_MODELS, model_name))
  s <- summary(m)

  temp <- s$temporal[, c("from", "to", "fixed", "SE", "P", "ran_SD")]
  names(temp) <- c("from", "to", "weight", "SE", "P", "ran_SD")
  write_result(temp, paste0(out_prefix, "_mlvar_temporal_edges.csv"), DIR_NETWORKS)

  con <- s$contemporaneous[, c("v1", "v2", "pcor", "P 1->2", "P 1<-2")]
  names(con) <- c("node1", "node2", "pcor", "P_a", "P_b")
  con$P <- pmin(con$P_a, con$P_b)
  write_result(con[, c("node1", "node2", "pcor", "P")],
               paste0(out_prefix, "_mlvar_contemporaneous_edges.csv"), DIR_NETWORKS)

  ext_core <- temp[temp$from %in% core_nodes & temp$to %in% core_nodes, ]
  cmp <- merge(prim[, c("from", "to", "weight")],
               ext_core[, c("from", "to", "weight")],
               by = c("from", "to"), suffixes = c("_core4", compare_suffix))
  names(cmp)[names(cmp) == paste0("weight", compare_suffix)] <- "weight_extended"
  cmp$abs_diff <- round(abs(cmp$weight_core4 - cmp$weight_extended), 3)
  write_result(cmp, compare_file, DIR_NETWORKS)

  r_core <- stats::cor(cmp$weight_core4, cmp$weight_extended)
  cat(sprintf("\n[%s] correlation of core edge weights with 4-node model: r = %.3f\n",
              out_prefix, r_core))
  cat(sprintf("[%s] max |change| in a core edge: %.3f\n", out_prefix, max(cmp$abs_diff)))

  cat(sprintf("\n[%s] significant temporal effects INTO Activity (P<.10):\n", out_prefix))
  act <- temp[temp$to == "ENMO_log" & temp$P < 0.10, ]
  print(act[order(act$P), ], row.names = FALSE)
  cat(sprintf("\n[%s] significant motivational temporal effects (P<.05):\n", out_prefix))
  mot_nodes <- setdiff(vars, core_nodes)
  mot <- temp[(temp$from %in% mot_nodes | temp$to %in% mot_nodes) & temp$P < 0.05, ]
  print(mot[order(mot$P), ], row.names = FALSE)

  invisible(list(model = m, temporal = temp, contemporaneous = con, comparison = cmp))
}

vars6 <- c("PIJN", "MOE", "STRESS", "ENMO_log", "EIGENEFF", "INTENTIE")
vars7 <- c("PIJN", "MOE", "STRESS", "ENMO_log", "EIGENEFF", "INTENTIE", "UITKOMSTVERW")

fit_extended(vars6, "mlvar_extended.rds", "extended",
             "extended_core_vs_full_compare.csv", "_ext6")
fit_extended(vars7, "mlvar_extended7.rds", "extended7",
             "extended7_core_vs_full_compare.csv", "_ext7")
