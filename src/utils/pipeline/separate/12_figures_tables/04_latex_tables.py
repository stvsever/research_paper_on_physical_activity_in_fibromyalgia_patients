"""Stage 12.4 - Generate LaTeX (booktabs) tables for the manuscript.

The manuscript inputs these files directly, so table layout rules live here:
titles are above the table, notes are below the table, and all tables are
left-aligned. Main and supplementary tables are regenerated from the numeric
results rather than hand-typed in the manuscript.
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

NICE = {
    "PIJN": "Pain",
    "MOE": "Fatigue",
    "STRESS": "Stress",
    "ENMO_log": "Activity",
    "EIGENEFF": "Self-efficacy",
    "INTENTIE": "Intention",
    "UITKOMSTVERW": "Rest-expectancy",
}


def esc(value) -> str:
    """Escape plain table text while preserving intentional LaTeX snippets."""
    s = "" if pd.isna(value) else str(value)
    for a, b in [
        ("&", r"\&"),
        ("%", r"\%"),
        ("_", r"\_"),
        ("->", r"$\rightarrow$"),
        (">", r"$>$"),
    ]:
        s = s.replace(a, b)
    return s


def fmt_p(p) -> str:
    if pd.isna(p):
        return ""
    return "<.001" if p < .001 else f"{p:.3f}".lstrip("0")


def body(df: pd.DataFrame, colspec: str) -> list[str]:
    lines = [
        rf"\begin{{tabular*}}{{\textwidth}}{{@{{\extracolsep{{\fill}}}}{colspec}@{{}}}}",
        r"\toprule",
    ]
    lines.append(" & ".join(esc(c) for c in df.columns) + r" \\")
    lines.append(r"\midrule")
    for _, row in df.iterrows():
        lines.append(" & ".join(esc(v) for v in row.values) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular*}"])
    return lines


def latex_table(
    df: pd.DataFrame,
    caption: str,
    label: str,
    colspec: str | None = None,
    note: str | None = None,
    size: str = r"\footnotesize",
) -> str:
    if colspec is None:
        colspec = "l" + "r" * (len(df.columns) - 1)
    lines = [r"\begin{table}[H]", r"\raggedright"]
    lines.append(rf"\caption{{{caption}}}")
    lines.append(rf"\label{{{label}}}")
    if size:
        lines.append(size)
    lines.append(r"\begingroup")
    lines.append(r"\setlength{\tabcolsep}{4pt}")
    lines.append(r"\renewcommand{\arraystretch}{1.08}")
    lines.append(r"\noindent")
    lines.extend(body(df, colspec))
    if note:
        lines.append(rf"\par\vspace{{3pt}}\noindent\parbox{{\textwidth}}{{{size}\textit{{Note.}} {note}}}")
    lines.append(r"\endgroup")
    lines.append(r"\end{table}")
    return "\n".join(lines) + "\n"


def latex_two_panel_table(
    panel_a: pd.DataFrame,
    panel_b: pd.DataFrame,
    caption: str,
    label: str,
    colspec_a: str,
    colspec_b: str,
    panel_a_title: str,
    panel_b_title: str,
    note: str,
    size: str = r"\footnotesize",
) -> str:
    lines = [
        r"\begin{table}[H]",
        r"\raggedright",
        rf"\caption{{{caption}}}",
        rf"\label{{{label}}}",
        size,
        r"\begingroup",
        r"\setlength{\tabcolsep}{4pt}",
        r"\renewcommand{\arraystretch}{1.08}",
        rf"\noindent\textit{{Panel A.}} {panel_a_title}\par\vspace{{2pt}}",
    ]
    lines.extend(body(panel_a, colspec_a))
    lines.append(rf"\par\vspace{{6pt}}\noindent\textit{{Panel B.}} {panel_b_title}\par\vspace{{2pt}}")
    lines.extend(body(panel_b, colspec_b))
    lines.append(rf"\par\vspace{{3pt}}\noindent\parbox{{\textwidth}}{{{size}\textit{{Note.}} {note}}}")
    lines.append(r"\endgroup")
    lines.append(r"\end{table}")
    return "\n".join(lines) + "\n"


def latex_three_panel_table(
    panel_a: pd.DataFrame,
    panel_b: pd.DataFrame,
    panel_c: pd.DataFrame,
    caption: str,
    label: str,
    colspec_a: str,
    colspec_b: str,
    colspec_c: str,
    panel_a_title: str,
    panel_b_title: str,
    panel_c_title: str,
    note: str,
    size: str = r"\footnotesize",
) -> str:
    lines = [
        r"\begin{table}[H]",
        r"\raggedright",
        rf"\caption{{{caption}}}",
        rf"\label{{{label}}}",
        size,
        r"\begingroup",
        r"\setlength{\tabcolsep}{4pt}",
        r"\renewcommand{\arraystretch}{1.08}",
        rf"\noindent\textit{{Panel A.}} {panel_a_title}\par\vspace{{2pt}}",
    ]
    lines.extend(body(panel_a, colspec_a))
    lines.append(rf"\par\vspace{{6pt}}\noindent\textit{{Panel B.}} {panel_b_title}\par\vspace{{2pt}}")
    lines.extend(body(panel_b, colspec_b))
    lines.append(rf"\par\vspace{{6pt}}\noindent\textit{{Panel C.}} {panel_c_title}\par\vspace{{2pt}}")
    lines.extend(body(panel_c, colspec_c))
    lines.append(rf"\par\vspace{{3pt}}\noindent\parbox{{\textwidth}}{{{size}\textit{{Note.}} {note}}}")
    lines.append(r"\endgroup")
    lines.append(r"\end{table}")
    return "\n".join(lines) + "\n"


def write(fname: str, content: str) -> None:
    out_dir = paths.TABLES_MAIN if fname.startswith("MAIN_") else paths.TABLES_SUPP
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / fname).write_text(content)
    print("  wrote " + str((out_dir / fname).relative_to(paths.ROOT)))


def edge_name(frm, to) -> str:
    return f"{NICE.get(frm, frm)} -> {NICE.get(to, to)}"


def sgimme_path_name(path: str) -> str:
    out = path.replace("ENMO_log", "Activity")
    out = out.replace("PIJN", "Pain").replace("MOE", "Fatigue").replace("STRESS", "Stress")
    out = out.replace("Activitylag", "Activity(t-1)")
    out = out.replace("Painlag", "Pain(t-1)")
    out = out.replace("Fatiguelag", "Fatigue(t-1)")
    out = out.replace("Stresslag", "Stress(t-1)")
    out = out.replace(" ~ ", r" $\leftarrow$ ")
    return out


# ---- MAIN_01 sample ---------------------------------------------------------
t1 = pd.read_csv(T / "02_person_level_table1.csv")
t1.columns = ["Variable", "Mean (SD)", "Range", "n"]
write(
    "MAIN_01_sample_descriptives.tex",
    latex_table(
        t1,
        "Baseline characteristics of the analytic sample ($n=31$ with POAM-P data).",
        "tab:sample",
        colspec="lccc",
        note=(
            "POAM-P subscales range 0-40. All participants were women. "
            "BMI = body mass index; TSK = Tampa Scale for Kinesiophobia; "
            "PROMIS = pain interference."
        ),
    ),
)

# ---- MAIN_02 EMA descriptives + variance ------------------------------------
ed = pd.read_csv(T / "02_ema_descriptives.csv")
vd = pd.read_csv(T / "03_variance_decomposition.csv")
core = ["PIJN", "MOE", "STRESS", "ENMO_log", "EIGENEFF", "INTENTIE", "UITKOMSTVERW"]
m = ed[ed["variable"].isin(core)].merge(
    vd[["variable", "icc_person", "var_within_day"]], on="variable", how="left"
)
labels = {
    "PIJN": "Pain",
    "MOE": "Fatigue",
    "STRESS": "Stress",
    "ENMO_log": "Activity (log)",
    "EIGENEFF": "Self-efficacy",
    "INTENTIE": "Intention",
    "UITKOMSTVERW": "Rest-expectancy",
}
m["Measure"] = m["variable"].map(labels)
m = m.set_index("variable").loc[core].reset_index()
tab = m[["Measure", "n_obs", "mean", "sd", "pct_missing", "icc_person", "var_within_day"]].copy()
tab.columns = ["Measure", "$n$ obs", "Mean", "SD", "% miss.", "ICC", "Within-day var."]
for c in ["Mean", "SD", "ICC", "Within-day var."]:
    tab[c] = tab[c].round(2)
write(
    "MAIN_02_ema_descriptives_variance.tex",
    latex_table(
        tab,
        "Momentary measures: descriptive statistics and variance partition.",
        "tab:emadesc",
        colspec="lcccccc",
        note=(
            "ICC = intraclass correlation, the between-person share. Within-day var. is "
            "the moment-to-moment variance share available to the lag-1 network."
        ),
    ),
)

# ---- MAIN_03 temporal effects -----------------------------------------------
te = pd.read_csv(N / "05_mlvar_core_temporal_edges.csv")
te["Effect"] = [edge_name(f, t) for f, t in zip(te["from"], te["to"])]
te["95% CI"] = [f"[{w - 1.96 * s:.2f}, {w + 1.96 * s:.2f}]" for w, s in zip(te["weight"], te["SE"])]
te["is_ar"] = te["from"] == te["to"]
te = te.sort_values(["is_ar", "P"]).reset_index(drop=True)
tab = te[["Effect", "weight", "SE", "95% CI", "P", "ran_SD"]].copy()
tab["weight"] = tab["weight"].round(3)
tab["SE"] = tab["SE"].round(3)
tab["ran_SD"] = tab["ran_SD"].round(3)
tab["P"] = tab["P"].map(fmt_p)
tab.columns = ["Effect (lag-1)", "Estimate", "SE", "95% CI", "$p$", "Random SD"]
write(
    "MAIN_03_mlvar_temporal_effects.tex",
    latex_table(
        tab,
        "Group-level temporal (lag-1) network: multilevel VAR fixed effects.",
        "tab:temporal",
        colspec="lccccc",
        note=(
            "Standardized within-person coefficients. Cross-lagged effects are listed "
            "above autoregressive effects. Random SD = between-person standard deviation "
            "of the effect."
        ),
    ),
)

# ---- MAIN_04 link -----------------------------------------------------------
gp = pd.read_csv(T / "09_param_by_dominant_pattern.csv").round(3)
gp.columns = [
    c.replace("mean_", "").replace("_", " ").title() if c.startswith("mean_") else c
    for c in gp.columns
]
gp["p_value"] = gp["p_value"].map(fmt_p)
gp.columns = ["Coupling", "Avoidance", "Overdoing", "Pacing", "KW $H$", "$p$"]
write(
    "MAIN_04_network_poamp_link.tex",
    latex_table(
        gp,
        "Individual network parameters by POAM-P dominant pattern (exploratory).",
        "tab:link",
        colspec="lccccc",
        note=(
            "Mean per-person standardized VAR(1) coefficients by subgroup "
            "(Avoidance $n=10$, Overdoing $n=12$, Pacing $n=9$). KW = Kruskal-Wallis "
            "test across subgroups. Exploratory ($N=30$, uncorrected)."
        ),
    ),
)

# ---- SUP_01 contemporaneous + between ---------------------------------------
con = pd.read_csv(N / "05_mlvar_core_contemporaneous_edges.csv")
btw = pd.read_csv(N / "05_mlvar_core_between_edges.csv")
con["Edge"] = [f"{NICE.get(a, a)} - {NICE.get(b, b)}" for a, b in zip(con["node1"], con["node2"])]
btw["Edge"] = [f"{NICE.get(a, a)} - {NICE.get(b, b)}" for a, b in zip(btw["node1"], btw["node2"])]
con_t = con[["Edge", "pcor", "P"]].copy()
con_t["Network"] = "Contemporaneous"
btw_t = btw[["Edge", "pcor", "P"]].copy()
btw_t["Network"] = "Between-person"
both = pd.concat([con_t, btw_t])[["Network", "Edge", "pcor", "P"]].round(3)
both["P"] = both["P"].map(fmt_p)
both.columns = ["Network", "Edge", "Partial $r$", "$p$"]
write(
    "SUP_01_contemporaneous_between_edges.tex",
    latex_table(
        both,
        "Contemporaneous and between-person networks.",
        "tab:sup-contemporaneous-between",
        colspec="llcc",
        note=(
            "Partial correlations from the primary mlVAR. The contemporaneous network "
            "represents same-prompt residual associations; the between-person network "
            "represents associations among person means."
        ),
    ),
)

# ---- SUP_02 stationarity -----------------------------------------------------
sk = pd.read_csv(T / "04_enmo_skewness.csv").round(3)
sk.columns = ["Measure", "Skewness", "Kurtosis"]
st = pd.read_csv(T / "04_stationarity_summary.csv")
st["variable"] = st["variable"].map(NICE)
st.columns = ["Variable", "Prop. linear trend", "Prop. KPSS non-stationary"]
st[["Prop. linear trend", "Prop. KPSS non-stationary"]] = st[
    ["Prop. linear trend", "Prop. KPSS non-stationary"]
].round(3)
write(
    "SUP_02_stationarity.tex",
    latex_two_panel_table(
        sk,
        st,
        "ENMO distribution and stationarity checks.",
        "tab:sup-stationarity",
        "lcc",
        "lcc",
        "Skewness and kurtosis of candidate activity transformations.",
        "Share of individual series flagged by linear trend and KPSS diagnostics.",
        "ENMO was analysed on the log scale because the transformed distribution was "
        "closest to symmetry. KPSS = Kwiatkowski-Phillips-Schmidt-Shin test.",
    ),
)

# ---- SUP_03 missing-data imputation comparison ------------------------------
miss = pd.read_csv(T / "04_missingness_by_measure.csv")
miss.columns = ["Measure", "Observed", "Missing", "% missing"]
imp = pd.read_csv(T / "04_imputation_comparison.csv")
imp.columns = ["Method", "Type", "Std. RMSE", "Std. MAE", "$r$ (held-out)",
               "Mean shift (SD)", "SD change (%)"]
write(
    "SUP_03_imputation_comparison.tex",
    latex_two_panel_table(
        miss,
        imp,
        "Missing data and imputation benchmark.",
        "tab:sup-imputation",
        "lccc",
        "llccccc",
        "Missingness by momentary measure (of 1,894 scheduled prompts).",
        "Univariate and multivariate imputation compared by held-out reconstruction and "
        "moment stability.",
        "Symptom missingness reflects non-response; activity missingness reflects "
        "accelerometer non-wear. The primary analyses used available-case (pairwise) "
        "handling within each VAR equation, consistent with the missing-at-random evidence "
        "in the stationarity and missingness checks. As a sensitivity benchmark, 20\\% of "
        "observed values were held out at random and reconstructed with five univariate "
        "imputeTS-style univariate time-series methods (Moritz \\& Bartz-Beielstein, 2017) "
        "and three multivariate methods that borrow strength across the concurrent measures "
        "(k-nearest-neighbours, MICE with Bayesian ridge, and a random-forest chained "
        "imputer). Standardized RMSE, MAE, and the within-person held-out correlation are "
        "averaged over the four core measures; the last two columns give the change in each "
        "measure's pooled mean and SD after all gaps are imputed. Multivariate methods "
        "reconstructed momentary fluctuations best (MICE: RMSE = 0.95, $r$ = 0.32), the "
        "univariate mean and median did not track within-person fluctuations, and every "
        "method left the descriptive moments essentially unchanged, which supports the "
        "available-case decision. Figure S5 visualizes the full benchmark.",
    ),
)

# ---- SUP_04 sgimme -----------------------------------------------------------
spc = pd.read_csv(N / "06_sgimme_summary_path_counts.csv")
sg = spc.copy()
sg["Path"] = sg["path"].map(sgimme_path_name)
sg["Path class"] = np.where(
    sg["lhs"] == sg["rhs"].str.replace("lag", "", regex=False),
    "Autoregressive",
    "Cross-variable",
)
sg = sg.sort_values(["count.group", "count.ind", "count.subgroup1", "Path"],
                    ascending=[False, False, False, True])
sg = sg[["Path", "Path class", "count.group", "count.ind", "count.subgroup1"]]
sg.columns = [
    "Path",
    "Path class",
    "Group-level n",
    "Individual n",
    "Subgroup-1 n",
]
write(
    "SUP_04_sgimme_paths.tex",
    latex_table(
        sg,
        "S-GIMME path prevalence.",
        "tab:sup-sgimme",
        colspec="llccc",
        note=(
            "Counts are the number of participants for whom S-GIMME retained each path at "
            "the group, individual, or first subgroup level. The four autoregressive paths "
            "reached the group threshold; no cross-variable path reached that threshold. "
            "Path labels place the outcome on the left and the predictor on the right, with "
            "$(t-1)$ marking lagged terms. "
            "S-GIMME found 16 subgroups, including two small groups and 14 singletons."
        ),
        size=r"\scriptsize",
    ),
)

# ---- SUP_05 graphicalVAR -----------------------------------------------------
gv = pd.read_csv(T / "07_graphicalvar_individual_summary.csv")
gv_t = gv.copy()
gv_t["fitted"] = gv_t["fitted"].map({True: "yes", False: "no"})
for c in ["n_temporal_edges", "n_contemp_edges"]:
    gv_t[c] = gv_t[c].fillna(0).astype(int)
gv_t["temporal_density"] = gv_t["temporal_density"].fillna(0).round(3)
gv_t["pain_to_activity"] = gv_t["pain_to_activity"].fillna(0).map(lambda v: "yes" if v != 0 else "no")
gv_t["activity_to_pain"] = gv_t["activity_to_pain"].fillna(0).map(lambda v: "yes" if v != 0 else "no")
gv_t = gv_t[[
    "pid", "n_complete", "fitted", "n_temporal_edges", "n_contemp_edges",
    "temporal_density", "pain_to_activity", "activity_to_pain",
]]
gv_t.columns = [
    "ID", "Complete prompts", "Fitted", "Temporal edges", "Contemp. edges",
    "Temporal density", "Pain -> Activity", "Activity -> Pain",
]
write(
    "SUP_05_graphicalvar_feasibility.tex",
    latex_table(
        gv_t,
        "Per-person graphicalVAR feasibility.",
        "tab:sup-graphicalvar",
        colspec="lccccccc",
        note=(
            "Fully separate regularized individual networks were fitted with graphicalVAR "
            "and EBIC selection. Participants with fewer than 30 complete prompts were not "
            "fitted. Edge counts refer to nonzero selected edges in each person-specific "
            "network."
        ),
        size=r"\scriptsize",
    ),
)

# ---- SUP_06 extended ---------------------------------------------------------
ex = pd.read_csv(N / "extended_mlvar_temporal_edges.csv")
ex["Effect"] = [edge_name(f, t) for f, t in zip(ex["from"], ex["to"])]
ex["is_ar"] = ex["from"] == ex["to"]
ex = ex.sort_values(["is_ar", "P"]).reset_index(drop=True)
tab = ex[["Effect", "weight", "SE", "P", "ran_SD"]].round(3)
tab["P"] = ex["P"].map(fmt_p).values
tab.columns = ["Effect (lag-1)", "Estimate", "SE", "$p$", "Random SD"]
write(
    "SUP_06_extended_model.tex",
    latex_table(
        tab,
        "Extended six-node model: temporal fixed effects.",
        "tab:sup-extended",
        colspec="lcccc",
        note=(
            "The model added momentary self-efficacy and intention. Core four-node edges "
            "correlated $r=.999$ with the primary model. Figure S8 also displays the "
            "corresponding seven-node extension that additionally includes rest-favouring "
            "outcome expectancy."
        ),
        size=r"\scriptsize",
    ),
)

# ---- SUP_07 pacing -----------------------------------------------------------
pd1 = pd.read_csv(T / "pacing_descriptives.csv").round(3)
ps = pd.read_csv(T / "pacing_on_symptoms.csv")
ps = ps[ps["term"] != "(Intercept)"][["term", "estimate", "SE", "p"]].copy()
ps["term"] = ps["term"].str.replace("c", "", regex=False).map(lambda x: NICE.get(x.upper(), x))
ps["p"] = ps["p"].map(fmt_p)
ps[["estimate", "SE"]] = ps[["estimate", "SE"]].round(3)
ps.columns = ["Predictor (within-person)", "Estimate", "SE", "$p$"]
write(
    "SUP_07_pacing.tex",
    latex_two_panel_table(
        pd1,
        ps,
        "Momentary pacing behaviour.",
        "tab:sup-pacing",
        "lrrrrrr",
        "lccc",
        "Descriptives for momentary pacing items rated when participants had been active.",
        "Within-person symptoms predicting concurrent pacing.",
        "Pacing items were slowing down, breaking tasks into parts, and adding extra "
        "breaks. Estimates come from the multilevel model of symptom deviations on "
        "momentary pacing.",
    ),
)

# ---- SUP_08 cantmove ---------------------------------------------------------
cm = pd.read_csv(N / "cantmove_edge_comparison.csv")
cm["Effect"] = [edge_name(f, t) for f, t in zip(cm["from"], cm["to"])]
tab = cm[["Effect", "weight_all", "weight_movement", "abs_diff"]].round(3)
tab.columns = ["Effect (lag-1)", "All prompts", "Movement-possible only", "|difference|"]
write(
    "SUP_08_cantmove_sensitivity.tex",
    latex_table(
        tab,
        "Could-not-move sensitivity.",
        "tab:sup-cantmove",
        colspec="lccc",
        note=(
            "Primary temporal coefficients were re-estimated after excluding prompts "
            "where movement was reported as impossible. Edge weights correlated $r=.982$ "
            "with the full model and no sign changes occurred."
        ),
    ),
)

# ---- SUP_09 robustness battery (LOPO + bootstrap) ---------------------------
loo = pd.read_csv(N / "robust_loo_summary.csv")
boot = pd.read_csv(N / "robust_bootstrap_summary.csv")
rob = loo.merge(boot[["edge", "ci_lo", "ci_hi", "prop_sign_consistent"]], on="edge")
rob = rob[rob["from"] != rob["to"]].copy().sort_values("mean")
rob["Effect"] = [edge_name(f, t) for f, t in zip(rob["from"], rob["to"])]
rob["LOPO range"] = [f"[{lo:.3f}, {hi:.3f}]" for lo, hi in zip(rob["min"], rob["max"])]
rob["Bootstrap 95% CI"] = [f"[{lo:.3f}, {hi:.3f}]" for lo, hi in zip(rob["ci_lo"], rob["ci_hi"])]
tab = rob[["Effect", "mean", "LOPO range", "Bootstrap 95% CI", "prop_sign_consistent"]].copy()
tab["mean"] = tab["mean"].round(3)
tab["prop_sign_consistent"] = tab["prop_sign_consistent"].round(3)
tab.columns = [
    "Cross-lagged effect",
    "Mean",
    "LOPO range",
    "Bootstrap 95% CI",
    "Bootstrap sign-consistency",
]
write(
    "SUP_09_robustness_stability.tex",
    latex_table(
        tab,
        "Stability of cross-lagged temporal edges: leave-one-participant-out and person cluster-bootstrap.",
        "tab:robust",
        colspec="lcccc",
        note=(
            "LOPO = 34 refits; bootstrap = 500 resamples. All cross-lagged edges retained "
            "their sign in 100\\% of leave-one-out refits."
        ),
    ),
)

# ---- SUP_10 sensitivity agreement -------------------------------------------
det = pd.read_csv(N / "robust_detrended_compare.csv")
thr = pd.read_csv(N / "robust_threshold40_compare.csv")
enmo = pd.read_csv(N / "robust_enmo_transform_compare.csv")
cm = pd.read_csv(N / "cantmove_edge_comparison.csv")
ext6 = pd.read_csv(N / "extended_core_vs_full_compare.csv")
ext7 = pd.read_csv(N / "extended7_core_vs_full_compare.csv")
agree = pd.DataFrame(
    {
        "Sensitivity analysis": [
            "Within-person detrended",
            "Stricter compliance ($\\geq 40$)",
            "ENMO raw scale",
            "ENMO square-root scale",
            "Movement-possible only",
            "Extended six-node model",
            "Extended seven-node model",
        ],
        "$r$ with primary": [
            round(np.corrcoef(det["weight_ref"], det["weight_detrended"])[0, 1], 3),
            round(np.corrcoef(thr["weight_ref"], thr["weight_thr40"])[0, 1], 3),
            float(enmo.loc[enmo["transform"] == "raw", "r_vs_log"].iloc[0]),
            float(enmo.loc[enmo["transform"] == "sqrt", "r_vs_log"].iloc[0]),
            round(np.corrcoef(cm["weight_all"], cm["weight_movement"])[0, 1], 3),
            round(np.corrcoef(ext6["weight_core4"], ext6["weight_extended"])[0, 1], 3),
            round(np.corrcoef(ext7["weight_core4"], ext7["weight_extended"])[0, 1], 3),
        ],
        "Sign flips": [0, 0, 0, 0, 0, 0, 0],
    }
)
write(
    "SUP_10_sensitivity_agreement.tex",
    latex_table(
        agree,
        "Agreement of each sensitivity analysis with the primary temporal network.",
        "tab:agreement",
        colspec="lcc",
        note="$r$ = correlation of the 16 temporal coefficients with the primary model.",
    ),
)

# ---- SUP_11 permutation link ------------------------------------------------
kw = pd.read_csv(T / "robust_permutation_kruskal.csv")
kw_t = kw[["coupling", "statistic", "p_asymptotic", "p_permutation", "n"]].copy()
for c in ["p_asymptotic", "p_permutation"]:
    kw_t[c] = kw_t[c].map(fmt_p)
kw_t.columns = ["Coupling", "KW $H$", "Asymp. $p$", "Perm. $p$", "$n$"]
write(
    "SUP_11_permutation_link.tex",
    latex_table(
        kw_t,
        "Permutation inference for the network-POAM-P link.",
        "tab:permutation",
        colspec="lcccc",
        note=(
            "Permutation tests used 10,000 label shuffles. The table reports "
            "Kruskal-Wallis tests of each coupling across POAM-P dominant patterns."
        ),
    ),
)

# ---- SUP_12 activity context ------------------------------------------------
loc = pd.read_csv(T / "02_context_by_location.csv")
soc = pd.read_csv(T / "02_context_by_social.csv")
ema = pd.read_csv(paths.EMA_LONG)
loc_t = loc[["location", "n_prompts", "pct", "mean_ENMO", "mean_pain", "mean_fatigue",
             "mean_stress"]].copy()
loc_t.columns = ["Location", "n prompts", "% prompts", "Mean ENMO (g)", "Mean pain",
                 "Mean fatigue", "Mean stress"]
for c in ["% prompts", "Mean ENMO (g)", "Mean pain", "Mean fatigue", "Mean stress"]:
    loc_t[c] = loc_t[c].round(2)
soc_t = soc[["social", "n", "mean_ENMO", "mean_pain", "mean_fatigue", "mean_stress"]].copy()
soc_t.columns = ["Social context", "n prompts", "Mean ENMO (g)", "Mean pain", "Mean fatigue", "Mean stress"]
for c in ["Mean ENMO (g)", "Mean pain", "Mean fatigue", "Mean stress"]:
    soc_t[c] = soc_t[c].round(2)
move_t = (
    ema.groupby("beep")
    .agg(
        can_move=("MOGELIJKHEID_BEW", lambda s: 100 * (s == 1).mean()),
        active_since_last=("ACTIVITEITEN", lambda s: 100 * (s == 1).mean()),
        planned_movement=("TOEK_ACT", lambda s: 100 * (s == 1).mean()),
    )
    .round(1)
    .reset_index()
)
move_t.columns = [
    "Prompt of day", "Able to move (%)", "Active since last prompt (%)",
    "Planned movement (%)",
]
write(
    "SUP_12_context.tex",
    latex_three_panel_table(
        loc_t,
        soc_t,
        move_t,
        "Activity and affect by everyday context.",
        "tab:sup-context",
        "lcccccc",
        "lccccc",
        "lccc",
        "Location-level summaries.",
        "Social-context summaries.",
        "Movement opportunity, recent activity, and plans by prompt of day.",
        note=(
            "Context variables are descriptive. Able to move is based on the recoded "
            "movement-opportunity item, where 1 indicates that movement was possible."
        ),
    ),
)

# ---- SUP_13 duplicate full temporal table -----------------------------------
te2 = pd.read_csv(N / "05_mlvar_core_temporal_edges.csv")
te2["Effect"] = [edge_name(f, t) for f, t in zip(te2["from"], te2["to"])]
te2["95% CI"] = [
    f"[{w - 1.96 * s:.2f}, {w + 1.96 * s:.2f}]"
    for w, s in zip(te2["weight"], te2["SE"])
]
te2["is_ar"] = te2["from"] == te2["to"]
te2 = te2.sort_values(["is_ar", "P"]).reset_index(drop=True)
tab2 = te2[["Effect", "weight", "SE", "95% CI", "P", "ran_SD"]].copy()
tab2["weight"] = tab2["weight"].round(3)
tab2["SE"] = tab2["SE"].round(3)
tab2["ran_SD"] = tab2["ran_SD"].round(3)
tab2["P"] = tab2["P"].map(fmt_p)
tab2.columns = ["Effect (lag-1)", "Estimate", "SE", "95% CI", "$p$", "Random SD"]
write(
    "SUP_13_mlvar_temporal_effects.tex",
    latex_table(
        tab2,
        "Primary four-node multilevel VAR temporal fixed effects.",
        "tab:sup-temporal",
        colspec="lccccc",
        note=(
            "This table repeats the primary temporal fixed-effect estimates for reference "
            "in the supplement. Standardized within-person coefficients are shown."
        ),
    ),
)

print("\nLaTeX tables written to", paths.TABLES_PAPER)
