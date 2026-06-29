# Stage 07 - Idiographic networks (feasibility) + per-person VAR coefficients

**Goal.** Answer Annick's central question empirically - "can we justify individual
networks at all?" - and produce the unshrunken per-person coupling strengths used in the
RQ2 link.

| Script | Output |
|--------|--------|
| `01_graphicalvar_perperson.R` | Fully separate regularized (EBIC LASSO) networks per person; sparsity and edge-selection frequencies |
| `02_perperson_var_ols.R` | Unregularized per-person standardized VAR(1) coefficients (lags within day) |

**Feasibility verdict (graphicalVAR).** At T ~ 44 the per-person LASSO selects a **median
of 0 temporal edges** (range 0-9 of 16); only 1 person has a Pain -> Activity edge and 2
have Activity -> Pain. Fully idiographic networks are therefore **not identifiable** in
this dataset - the empirical justification for using mlVAR (partial pooling) as the primary
model rather than separate individual networks.

**Why the OLS VAR.** The mlVAR subject coefficients are empirical-Bayes shrunken (constant
where the random SD is ~0), and graphicalVAR coefficients are mostly zero. The
unregularized per-person OLS VAR gives genuine between-person variation in coupling
strengths (e.g., Pain -> Activity SD = 0.27, range -0.68 to +0.54), exactly the
"individual network parameter" Annick proposed using as an outcome. These feed stage 09.
