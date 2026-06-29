# Stage 05 - Multilevel VAR (PRIMARY network model, RQ1).
#
# Rationale (see stage README): with ~44 observations per person we are well below the
# 100-120 recommended for fully separate individual VAR / S-GIMME networks. mlVAR uses
# multilevel partial pooling: it borrows strength across the 34 persons to estimate a
# stable GROUP (fixed-effect) network while still quantifying individual heterogeneity
# (random effects). This is the methodologically defensible primary analysis for this
# n-persons / short-T regime.
#
# Three networks are estimated on the core nodes Pain, Fatigue, Stress, Activity(logENMO):
#   - temporal        : directed lag-1 effects (Granger-style), within-day only,
#   - contemporaneous : partial correlations of within-person residuals at the same beep,
#   - between-person  : partial correlations of person means.
# Day boundaries are respected via dayvar (no lag is built across the overnight gap);
# beepvar enforces adjacency. Variables are within-person standardized (scale = TRUE).
# Random effects are orthogonal (correlated REs are not estimable with N = 34 and 16
# temporal parameters).

args <- commandArgs(trailingOnly = TRUE)
this <- normalizePath(sub("--file=", "",
  grep("--file=", commandArgs(FALSE), value = TRUE)[1]), mustWork = FALSE)
lib <- file.path(dirname(this), "..", "..", "..", "lib")
source(file.path(lib, "common.R"))
need(c("mlVAR"))

# --- options: allow a "movement-only" sensitivity run (drops could-not-move beeps) ----
movement_only <- length(args) >= 1 && args[1] == "movement_only"
tag <- if (movement_only) "movementonly" else "core"

d <- read_ema()
d$pid <- as.factor(d$pid)
if (movement_only) {
  d <- d[is.na(d$MOGELIJKHEID_BEW) | d$MOGELIJKHEID_BEW == 1, ]
  cat(sprintf("[mlVAR] movement-only sensitivity: %d rows retained\n", nrow(d)))
}

vars <- c("PIJN", "MOE", "STRESS", "ENMO_log")
labels <- c("Pain", "Fatigue", "Stress", "Activity")

set.seed(20260626)
m <- mlVAR(d, vars = vars, idvar = "pid", dayvar = "day", beepvar = "beep",
           lags = 1, temporal = "orthogonal", contemporaneous = "orthogonal",
           estimator = "lmer", scale = TRUE, verbose = FALSE)

saveRDS(m, file.path(DIR_MODELS, sprintf("mlvar_%s.rds", tag)))
s <- summary(m)

# --- temporal edge list (directed) -------------------------------------------
temp <- s$temporal[, c("from", "to", "fixed", "SE", "P", "ran_SD")]
names(temp) <- c("from", "to", "weight", "SE", "P", "ran_SD")
write_result(temp, sprintf("05_mlvar_%s_temporal_edges.csv", tag), DIR_NETWORKS)

# --- contemporaneous edge list (undirected partial correlations) -------------
con <- s$contemporaneous[, c("v1", "v2", "pcor", "P 1->2", "P 1<-2", "ran_SD_pcor")]
names(con) <- c("node1", "node2", "pcor", "P_a", "P_b", "ran_SD")
con$P <- pmin(con$P_a, con$P_b)
write_result(con[, c("node1", "node2", "pcor", "P", "ran_SD")],
             sprintf("05_mlvar_%s_contemporaneous_edges.csv", tag), DIR_NETWORKS)

# --- between-person edge list ------------------------------------------------
btw <- s$between[, c("v1", "v2", "pcor", "P 1->2", "P 1<-2")]
names(btw) <- c("node1", "node2", "pcor", "P_a", "P_b")
btw$P <- pmin(btw$P_a, btw$P_b)
write_result(btw[, c("node1", "node2", "pcor", "P")],
             sprintf("05_mlvar_%s_between_edges.csv", tag), DIR_NETWORKS)

# --- verify subject-array orientation, then extract subject-specific temporal --
# Beta$subject[[s]] is a [response, predictor, lag] array. Confirm by matching the
# subject-average to the fixed temporal effect for one off-diagonal cell.
subj <- m$results$Beta$subject
mean_arr <- Reduce(`+`, subj) / length(subj)            # [resp, pred, 1]
# fixed effect of MOE(t-1) -> PIJN(t): from=MOE, to=PIJN
fix_moe_to_pijn <- temp$weight[temp$from == "MOE" & temp$to == "PIJN"]
arr_resp_pijn_pred_moe <- mean_arr["PIJN", "MOE", 1]    # response=PIJN, predictor=MOE
stopifnot(abs(arr_resp_pijn_pred_moe - fix_moe_to_pijn) < 0.05)
cat("[mlVAR] subject array orientation verified: [response, predictor, lag]\n")

# Build a tidy person x directed-edge table of subject-specific lag-1 coefficients.
edges <- expand.grid(predictor = vars, response = vars, stringsAsFactors = FALSE)
rows <- lapply(seq_along(subj), function(i) {
  a <- subj[[i]]
  vals <- mapply(function(pr, rs) a[rs, pr, 1], edges$predictor, edges$response)
  data.frame(pid = levels(d$pid)[i],
             from = edges$predictor, to = edges$response,
             coef = as.numeric(vals), stringsAsFactors = FALSE)
})
subj_long <- do.call(rbind, rows)
subj_long$edge <- paste0(subj_long$from, "__to__", subj_long$to)
subj_wide <- reshape(subj_long[, c("pid", "edge", "coef")],
                     idvar = "pid", timevar = "edge", direction = "wide")
names(subj_wide) <- sub("^coef\\.", "", names(subj_wide))

# Per-person temporal density (mean absolute lag-1 coefficient) and key edges.
subj_wide$temporal_density <- rowMeans(abs(subj_wide[, setdiff(names(subj_wide), "pid")]))
write_result(subj_wide, sprintf("05_mlvar_%s_subject_temporal_coefs.csv", tag), DIR_NETWORKS)

# --- compact console report ---------------------------------------------------
cat("\n=== mlVAR temporal fixed effects (significant, P<.05) ===\n")
sig <- temp[temp$P < 0.05, ]
print(sig[order(sig$P), ], row.names = FALSE)
cat("\nSaved model + edge lists for tag:", tag, "\n")
