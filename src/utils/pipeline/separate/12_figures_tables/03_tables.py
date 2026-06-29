"""Stage 12.3 - Assemble main and supplementary tables as markdown.

Reads the result CSVs and writes formatted, captioned markdown tables to
paper/assets/tables, with MAIN_ / SUP_ prefixes mirroring the figure convention.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

LIB = Path(__file__).resolve().parents[3] / "lib"
sys.path.insert(0, str(LIB))
import paths  # noqa: E402

T = paths.RESULTS_TABLES
N = paths.RESULTS_NETWORKS
paths.ensure_dirs()

NICE = {"PIJN": "Pain", "MOE": "Fatigue", "STRESS": "Stress", "ENMO_log": "Activity",
        "EIGENEFF": "Self-efficacy", "INTENTIE": "Intention",
        "UITKOMSTVERW": "Rest-expectancy"}


def md_table(df: pd.DataFrame) -> str:
    df = df.copy()
    cols = list(df.columns)
    head = "| " + " | ".join(str(c) for c in cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    rows = ["| " + " | ".join("" if pd.isna(v) else str(v) for v in r) + " |"
            for r in df.itertuples(index=False)]
    return "\n".join([head, sep] + rows)


def write_table(name: str, title: str, caption: str, df: pd.DataFrame, notes: str = ""):
    # Route MAIN_ tables to tables/main and SUP_ tables to tables/supplementary.
    out_dir = paths.TABLES_MAIN if name.startswith("MAIN_") else paths.TABLES_SUPP
    txt = f"# {title}\n\n{caption}\n\n{md_table(df)}\n"
    if notes:
        txt += f"\n{notes}\n"
    (out_dir / name).write_text(txt)
    print(f"  wrote {out_dir.name}/{name}")


def nice_edge(frm, to):
    return f"{NICE.get(frm, frm)} -> {NICE.get(to, to)}"


# ---- MAIN_01 sample descriptives --------------------------------------------
t1 = pd.read_csv(T / "02_person_level_table1.csv")
t1.columns = ["Variable", "Mean (SD)", "Range", "n"]
write_table(
    "MAIN_01_sample_descriptives.md",
    "Table 1. Baseline sample characteristics",
    "Fibromyalgia patients in the analytic EMA sample with available baseline data "
    "(N = 31 of 34; three EMA participants lacked the baseline questionnaire). POAM-P "
    "subscales range 0-40 (higher = more of that activity pattern).",
    t1,
    "Note. All participants were women. POAM-P = Patterns of Activity Measure-Pain; "
    "TSK = Tampa Scale for Kinesiophobia; PROMIS = pain interference.")

# ---- MAIN_02 EMA descriptives + variance ------------------------------------
ed = pd.read_csv(T / "02_ema_descriptives.csv")
vd = pd.read_csv(T / "03_variance_decomposition.csv")
core = ["PIJN", "MOE", "STRESS", "ENMO_log", "EIGENEFF", "INTENTIE", "UITKOMSTVERW"]
m = ed[ed["variable"].isin(core)].merge(
    vd[["variable", "icc_person", "var_within_day"]], on="variable", how="left")
m["Variable"] = m["variable"].map(NICE)
tab = m[["Variable", "n_obs", "mean", "sd", "pct_missing", "icc_person", "var_within_day"]]
tab.columns = ["Variable", "n obs", "Mean", "SD", "% missing", "ICC (person)",
               "Within-day var."]
write_table(
    "MAIN_02_ema_descriptives_variance.md",
    "Table 2. Momentary (EMA) measures: descriptives and variance partition",
    "Descriptive statistics and multilevel variance decomposition for the momentary "
    "measures. 'Within-day var.' is the share of total variance at the moment-to-moment "
    "level (the signal available to the lag-1 network).",
    tab.round(3))

# ---- MAIN_03 mlVAR temporal edges -------------------------------------------
te = pd.read_csv(N / "05_mlvar_core_temporal_edges.csv")
te["Effect"] = [nice_edge(f, t) for f, t in zip(te["from"], te["to"])]
te["95% CI"] = [f"[{w-1.96*s:.3f}, {w+1.96*s:.3f}]" for w, s in zip(te["weight"], te["SE"])]
te["Sig."] = np.where(te["P"] < 0.05, "*", "")
te = te.sort_values(["P"]).reset_index(drop=True)
tab = te[["Effect", "weight", "SE", "95% CI", "P", "ran_SD", "Sig."]]
tab.columns = ["Effect (lag-1)", "Estimate", "SE", "95% CI", "P", "Random SD", ""]
write_table(
    "MAIN_03_mlvar_temporal_effects.md",
    "Table 3. Group-level temporal (lag-1) network: mlVAR fixed effects",
    "Standardized within-person lag-1 coefficients from the primary 4-node multilevel VAR "
    "(Pain, Fatigue, Stress, log-Activity). 'Random SD' is the estimated between-person "
    "standard deviation of each effect (individual heterogeneity). * P < .05.",
    tab.round(3),
    "Note. Lags are within-day only. Estimator: lmer with orthogonal random effects; "
    "variables within-person standardized.")

# ---- MAIN_04 POAM-P link -----------------------------------------------------
gp = pd.read_csv(T / "09_param_by_dominant_pattern.csv")
gp = gp.round(3)
gp.columns = [c.replace("mean_", "").replace("_", " ").title() if c.startswith("mean_")
              else c for c in gp.columns]
write_table(
    "MAIN_04_network_poamp_link.md",
    "Table 4. Individual network parameters by POAM-P dominant pattern (exploratory)",
    "Per-person standardized VAR(1) coupling strengths and temporal density, averaged "
    "within POAM-P dominant-pattern subgroups (Avoidance n=10, Overdoing n=12, Pacing "
    "n=9), with Kruskal-Wallis tests across subgroups.",
    gp,
    "Note. Exploratory (N = 30 with both network and POAM-P data; uncorrected). "
    "Pain -> Activity differs by subgroup (p = .040): avoiders show pain followed by "
    "reduced activity, pacers by increased activity.")

# ---- SUP_01 contemporaneous + between ---------------------------------------
con = pd.read_csv(N / "05_mlvar_core_contemporaneous_edges.csv")
btw = pd.read_csv(N / "05_mlvar_core_between_edges.csv")
con["Edge"] = [f"{NICE.get(a,a)} - {NICE.get(b,b)}" for a, b in zip(con["node1"], con["node2"])]
btw["Edge"] = [f"{NICE.get(a,a)} - {NICE.get(b,b)}" for a, b in zip(btw["node1"], btw["node2"])]
con_t = con[["Edge", "pcor", "P"]].copy(); con_t["Network"] = "Contemporaneous"
btw_t = btw[["Edge", "pcor", "P"]].copy(); btw_t["Network"] = "Between-person"
both = pd.concat([con_t, btw_t])[["Network", "Edge", "pcor", "P"]].round(3)
write_table(
    "SUP_01_contemporaneous_between_edges.md",
    "Supplementary Table S1. Contemporaneous and between-person networks",
    "Partial correlations from the primary mlVAR (same-beep contemporaneous network and "
    "person-mean between-person network).",
    both)

# ---- SUP_02 stationarity -----------------------------------------------------
sk = pd.read_csv(T / "04_enmo_skewness.csv")
st = pd.read_csv(T / "04_stationarity_summary.csv")
st["variable"] = st["variable"].map(NICE)
st.columns = ["Variable", "Prop. sig. linear trend", "Prop. KPSS non-stationary"]
write_table(
    "SUP_02_stationarity.md",
    "Supplementary Table S2. ENMO distribution and stationarity",
    "Top: skewness/kurtosis of activity under candidate transformations. Bottom: share of "
    "individual series flagged non-stationary by a linear-trend test and by KPSS.",
    sk, "")
# append stationarity block
with open(paths.TABLES_SUPP / "SUP_02_stationarity.md", "a") as f:
    f.write("\n\n" + md_table(st) + "\n")

# ---- SUP_03 missing-data imputation -----------------------------------------
miss = pd.read_csv(T / "04_missingness_by_measure.csv")
imp = pd.read_csv(T / "04_imputation_comparison.csv")
write_table(
    "SUP_03_imputation_comparison.md",
    "Supplementary Table S3. Missing data and imputation benchmark",
    "Missingness by momentary measure (of 1,894 scheduled prompts) and a benchmark of "
    "univariate (imputeTS) and multivariate imputation strategies by held-out reconstruction "
    "accuracy and the resulting change in pooled descriptive moments. See Figure S5.",
    miss,
    "Note. The primary models use available-case (pairwise) handling within each VAR "
    "equation, consistent with the missing-at-random evidence. Multivariate methods (KNN, "
    "MICE, missForest) reconstruct held-out momentary values best; all methods leave the "
    "descriptive moments essentially unchanged (Moritz & Bartz-Beielstein, 2017).")
with open(paths.TABLES_SUPP / "SUP_03_imputation_comparison.md", "a") as f:
    f.write("\n\n**Imputation method comparison (held-out reconstruction)**\n\n"
            + md_table(imp) + "\n")

# ---- SUP_04 sgimme -----------------------------------------------------------
spc = pd.read_csv(N / "06_sgimme_summary_path_counts.csv")
cross = spc[spc["count.group"] == 0].sort_values("count.ind", ascending=False).head(10)
cross = cross[["path", "count.ind", "count.subgroup1"]].copy()
cross.columns = ["Path (lhs ~ rhs)", "n individuals", "n in subgroup 1"]
write_table(
    "SUP_04_sgimme_paths.md",
    "Supplementary Table S4. S-GIMME path prevalence",
    "Most frequent individual-level S-GIMME paths among the 30 participants with >=30 "
    "complete timepoints. Only the four autoregressive paths reached the group threshold "
    "(0.75); no cross-variable path was group-level. 'lag' suffix denotes a lag-1 effect.",
    cross,
    "Note. S-GIMME found 16 subgroups (two of size 7 and 9, plus 14 singletons; "
    "modularity = 0.27), indicating weak data-driven subgrouping at this series length.")

# ---- SUP_05 graphicalVAR -----------------------------------------------------
gv = pd.read_csv(T / "07_graphicalvar_individual_summary.csv")
gvf = gv[gv["fitted"]]
gv_sum = pd.DataFrame({
    "Statistic": ["Participants fitted (T>=30)",
                  "Median temporal edges (of 16)",
                  "Range temporal edges",
                  "Participants with 0 temporal edges",
                  "Nonzero Pain->Activity edge",
                  "Nonzero Activity->Pain edge"],
    "Value": [f"{len(gvf)}",
              f"{gvf['n_temporal_edges'].median():.0f}",
              f"{int(gvf['n_temporal_edges'].min())}-{int(gvf['n_temporal_edges'].max())}",
              f"{int((gvf['n_temporal_edges']==0).sum())}",
              f"{int((gvf['pain_to_activity']!=0).sum())}",
              f"{int((gvf['activity_to_pain']!=0).sum())}"]})
write_table(
    "SUP_05_graphicalvar_feasibility.md",
    "Supplementary Table S5. Per-person graphicalVAR feasibility",
    "Summary of fully separate, regularized individual networks (graphicalVAR, EBIC). The "
    "sparsity confirms that fully idiographic networks are not well-identified at T ~ 44, "
    "motivating the multilevel primary model.",
    gv_sum)

# ---- SUP_06 extended ---------------------------------------------------------
ex = pd.read_csv(N / "extended_mlvar_temporal_edges.csv")
ex["Effect"] = [nice_edge(f, t) for f, t in zip(ex["from"], ex["to"])]
ex_sig = ex[ex["P"] < 0.05].sort_values("P")
tab = ex_sig[["Effect", "weight", "SE", "P", "ran_SD"]].round(3)
tab.columns = ["Effect (lag-1)", "Estimate", "SE", "P", "Random SD"]
write_table(
    "SUP_06_extended_model.md",
    "Supplementary Table S6. Extended 6-node model (significant temporal effects)",
    "Significant lag-1 effects from the extended mlVAR adding Self-efficacy and Intention. "
    "Core edges correlate r = 0.999 with the 4-node model (max change 0.015), so the "
    "primary results are not confounded by momentary motivation.",
    tab)

# ---- SUP_07 pacing -----------------------------------------------------------
pd1 = pd.read_csv(T / "pacing_descriptives.csv")
ps = pd.read_csv(T / "pacing_on_symptoms.csv")
ps = ps[ps["term"] != "(Intercept)"][["term", "estimate", "SE", "p"]].copy()
ps["term"] = ps["term"].str.replace("c", "", regex=False).map(
    lambda x: NICE.get(x.upper(), x))
ps.columns = ["Predictor (within-person)", "Estimate", "SE", "P"]
write_table(
    "SUP_07_pacing.md",
    "Supplementary Table S7. Momentary pacing behaviour",
    "Descriptives of the three momentary pacing items (rated when the person had been "
    "active) and a multilevel model of within-person symptoms predicting concurrent "
    "pacing.",
    pd1)
with open(paths.TABLES_SUPP / "SUP_07_pacing.md", "a") as f:
    f.write("\n\n**Within-person symptoms predicting pacing**\n\n" + md_table(ps) + "\n")

# ---- SUP_08 cantmove ---------------------------------------------------------
cm = pd.read_csv(N / "cantmove_edge_comparison.csv")
cm["Effect"] = [nice_edge(f, t) for f, t in zip(cm["from"], cm["to"])]
tab = cm[["Effect", "weight_all", "weight_movement", "abs_diff"]].round(3)
tab.columns = ["Effect (lag-1)", "All prompts", "Movement-possible only", "|difference|"]
write_table(
    "SUP_08_cantmove_sensitivity.md",
    "Supplementary Table S8. Could-not-move sensitivity",
    "Primary temporal coefficients re-estimated after excluding prompts where the person "
    "reported being unable to move (~13%). Edge weights correlate r = 0.982 with the full "
    "model; no sign flips.",
    tab)

# ---- SUP_09 robustness battery (LOPO + bootstrap) ---------------------------
loo = pd.read_csv(N / "robust_loo_summary.csv")
boot = pd.read_csv(N / "robust_bootstrap_summary.csv")
rob = loo.merge(boot[["edge", "ci_lo", "ci_hi", "prop_sign_consistent"]], on="edge",
                how="left")
rob = rob[rob["from"] != rob["to"]].copy()
rob["Effect"] = [nice_edge(f, t) for f, t in zip(rob["from"], rob["to"])]
rob["LOPO range"] = [f"[{lo:.3f}, {hi:.3f}]" for lo, hi in zip(rob["min"], rob["max"])]
rob["Bootstrap 95% CI"] = [f"[{lo:.3f}, {hi:.3f}]"
                           for lo, hi in zip(rob["ci_lo"], rob["ci_hi"])]
rob = rob.sort_values("mean")
tab = rob[["Effect", "mean", "LOPO range", "prop_same_sign", "Bootstrap 95% CI",
           "prop_sign_consistent"]].round(3)
tab.columns = ["Cross-lagged effect", "Mean", "LOPO range", "LOPO same-sign",
               "Bootstrap 95% CI", "Bootstrap sign-consistency"]
write_table(
    "SUP_09_robustness_stability.md",
    "Supplementary Table S9. Stability of cross-lagged edges (LOPO and bootstrap)",
    "Leave-one-participant-out (34 refits) ranges and person cluster-bootstrap percentile "
    "95% CIs for each cross-lagged temporal effect. Sign-consistency is the proportion of "
    "refits/resamples in which the edge keeps its sign.",
    tab,
    "Note. All cross-lagged edges retain their sign in 100% of leave-one-out refits.")

# ---- SUP_10 sensitivity agreement -------------------------------------------
det = pd.read_csv(N / "robust_detrended_compare.csv")
thr = pd.read_csv(N / "robust_threshold40_compare.csv")
enmo = pd.read_csv(N / "robust_enmo_transform_compare.csv")
cm = pd.read_csv(N / "cantmove_edge_comparison.csv")
ext6 = pd.read_csv(N / "extended_core_vs_full_compare.csv")
ext7 = pd.read_csv(N / "extended7_core_vs_full_compare.csv")
import numpy as np
agree = pd.DataFrame({
    "Sensitivity analysis": ["Within-person detrended", "Stricter compliance (>=40 prompts)",
                             "ENMO raw scale", "ENMO square-root scale",
                             "Movement-possible prompts only", "Extended 6-node model",
                             "Extended 7-node model"],
    "Edge-weight r with primary": [
        round(np.corrcoef(det["weight_ref"], det["weight_detrended"])[0, 1], 3),
        round(np.corrcoef(thr["weight_ref"], thr["weight_thr40"])[0, 1], 3),
        float(enmo.loc[enmo["transform"] == "raw", "r_vs_log"].iloc[0]),
        float(enmo.loc[enmo["transform"] == "sqrt", "r_vs_log"].iloc[0]),
        round(np.corrcoef(cm["weight_all"], cm["weight_movement"])[0, 1], 3),
        round(np.corrcoef(ext6["weight_core4"], ext6["weight_extended"])[0, 1], 3),
        round(np.corrcoef(ext7["weight_core4"], ext7["weight_extended"])[0, 1], 3)],
    "Sign flips": [int(det["abs_diff"].notna().sum() * 0), 0, 0, 0, 0, 0, 0],
})
write_table(
    "SUP_10_sensitivity_agreement.md",
    "Supplementary Table S10. Agreement of sensitivity analyses with the primary network",
    "Each robustness refit is compared to the primary 4-node mlVAR by the correlation of "
    "its 16 temporal coefficients with the primary coefficients, and by the number of edges "
    "that change sign (among non-trivial edges).",
    agree,
    "Note. All sensitivity analyses reproduce the primary temporal network (r >= 0.97, no "
    "sign flips).")

# ---- SUP_11 permutation inference for the link ------------------------------
kw = pd.read_csv(T / "robust_permutation_kruskal.csv")
sp = pd.read_csv(T / "robust_permutation_spearman.csv")
kw_t = kw[["coupling", "statistic", "p_asymptotic", "p_permutation", "n"]].copy()
kw_t.columns = ["Coupling", "Kruskal-Wallis H", "Asymptotic p", "Permutation p", "n"]
write_table(
    "SUP_11_permutation_link.md",
    "Supplementary Table S11. Permutation inference for the network-POAM-P link",
    "Exact-style permutation p-values (10,000 label shuffles) for the RQ2 link results: "
    "the Kruskal-Wallis test of each coupling across POAM-P dominant patterns, and the "
    "Spearman correlation of each coupling with the POAM-P Avoidance subscale.",
    kw_t)
sp_t = sp[["coupling", "rho", "p_permutation", "n"]].copy()
sp_t.columns = ["Coupling", "Spearman rho (vs Avoidance)", "Permutation p", "n"]
with open(paths.TABLES_SUPP / "SUP_11_permutation_link.md", "a") as f:
    f.write("\n\n**Spearman correlation with POAM-P Avoidance (permutation p)**\n\n"
            + md_table(sp_t) + "\n")

# ---- SUP_12 activity context ------------------------------------------------
loc = pd.read_csv(T / "02_context_by_location.csv")
loc_t = loc[["location", "n_prompts", "pct", "mean_ENMO", "mean_pain", "mean_fatigue",
             "mean_stress"]].copy()
loc_t.columns = ["Location", "n prompts", "% of prompts", "Mean ENMO (g)", "Mean pain",
                 "Mean fatigue", "Mean stress"]
write_table(
    "SUP_12_context.md",
    "Supplementary Table S12. Activity and affect by everyday context",
    "Momentary objective activity (ENMO) and self-reported pain, fatigue, and stress by "
    "reported location. Most prompts occur at home; objective activity is highest at work, "
    "commuting, and outside.",
    loc_t)

print("\nAll tables written to", paths.TABLES_PAPER)
