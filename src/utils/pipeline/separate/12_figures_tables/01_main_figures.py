"""Stage 12.1 - Main publication figures (MAIN_01 .. MAIN_04).

Each figure is a multi-panel PNG saved at 300 dpi to paper/assets/figures/main. No global
suptitles are used; every panel carries its own title and a bold panel letter.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

LIB = Path(__file__).resolve().parents[3] / "lib"
sys.path.insert(0, str(LIB))
import paths  # noqa: E402
import vizstyle as vs  # noqa: E402
import netviz  # noqa: E402

vs.apply_style()
paths.ensure_dirs()
T = paths.RESULTS_TABLES
N = paths.RESULTS_NETWORKS

ema = pd.read_csv(paths.EMA_LONG)
NODES = ["PIJN", "MOE", "STRESS", "ENMO_log"]


# ===========================================================================
# MAIN_01 - Variance decomposition (idiographic justification)
# ===========================================================================
def main_02():
    vd = pd.read_csv(T / "03_variance_decomposition.csv")
    order = ["PIJN", "MOE", "STRESS", "ENMO_log", "EIGENEFF", "INTENTIE", "UITKOMSTVERW"]
    vd = vd.set_index("variable").loc[[v for v in order if v in vd["variable"].values]
                                      ].reset_index()

    fig = plt.figure(figsize=(14, 5.7))
    gs = GridSpec(1, 2, figure=fig, width_ratios=[1.45, 1.0], wspace=0.30)

    ax = fig.add_subplot(gs[0, 0])
    y = np.arange(len(vd))
    bp = vd["var_between_person"] * 100
    bd = vd["var_between_day"] * 100
    wd = vd["var_within_day"] * 100
    ax.barh(y, bp, color=vs.MUTED, label="between persons")
    ax.barh(y, bd, left=bp, color=vs.NODE_COLORS["MOE"], label="between days (within person)")
    ax.barh(y, wd, left=bp + bd, color=vs.NODE_COLORS["ENMO"],
            label="within day (moment-to-moment)")
    for i in range(len(vd)):
        ax.text(bp[i] + bd[i] + wd[i] / 2, i, f"{wd[i]:.0f}%", va="center", ha="center",
                color="white", fontweight="bold", fontsize=9)
    ax.set_yticks(y)
    ax.set_yticklabels([vs.node_label(v) for v in vd["variable"]])
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("share of total variance (%)")
    ax.set_title("Variance partition from null multilevel models")
    ax.legend(loc="lower right", ncol=1)
    ax.grid(axis="y", visible=False)
    vs.bar_axes(ax, "horizontal")
    vs.panel_label(ax, "A")

    ax = fig.add_subplot(gs[0, 1])
    ratio = vd["var_within_day"] / vd["var_between_person"]
    cols = [vs.NODE_COLORS["ENMO"] if r >= 1 else vs.MUTED for r in ratio]
    ax.barh(y, ratio, color=cols, alpha=0.9)
    ax.axvline(1, color=vs.INK, lw=1.0, ls="--")
    for i, r in enumerate(ratio):
        ax.text(r + 0.05, i, f"{r:.2f}", va="center", fontsize=9, color=vs.INK)
    ax.set_yticks(y)
    ax.set_yticklabels([vs.node_label(v) for v in vd["variable"]])
    ax.invert_yaxis()
    ax.set_xlabel("within-day variance / between-person variance")
    ax.set_title("Amount of network-relevant within-person signal")
    ax.set_xlim(0, max(2.5, float(ratio.max()) + 0.35))
    ax.grid(axis="y", visible=False)
    vs.bar_axes(ax, "horizontal")
    vs.panel_label(ax, "B")

    vs.savefig(fig, paths.FIG_MAIN / "MAIN_01_variance_decomposition.png")


# ===========================================================================
# MAIN_02 - The three mlVAR networks (RQ1 centrepiece)
# ===========================================================================
def _edges_from(df, a="from", b="to"):
    return [{"from": r[a], "to": r[b], "weight": r["weight"] if "weight" in r else r["pcor"],
             "P": r.get("P", 0.0)} for _, r in df.iterrows()]


def main_03():
    temp = pd.read_csv(N / "05_mlvar_core_temporal_edges.csv")
    con = pd.read_csv(N / "05_mlvar_core_contemporaneous_edges.csv")
    btw = pd.read_csv(N / "05_mlvar_core_between_edges.csv")

    temp_e = [{"from": r["from"], "to": r["to"], "weight": r["weight"], "P": r["P"]}
              for _, r in temp.iterrows()]
    con_e = [{"node1": r["node1"], "node2": r["node2"], "weight": r["pcor"], "P": r["P"]}
             for _, r in con.iterrows()]
    btw_e = [{"node1": r["node1"], "node2": r["node2"], "weight": r["pcor"], "P": r["P"]}
             for _, r in btw.iterrows()]

    # common width reference across temporal/contemp for comparability of the two within-person
    wref = max(max(abs(temp["weight"])), max(abs(con["pcor"])))

    fig = plt.figure(figsize=(15, 6.0))
    gs = GridSpec(1, 3, figure=fig, wspace=0.05)

    ax = fig.add_subplot(gs[0, 0])
    netviz.draw_network(ax, NODES, temp_e, directed=True, weight_ref=wref,
                        title="Temporal (lag-1, within-person)")
    vs.panel_label(ax, "A", dx=0.02, dy=1.02)

    ax = fig.add_subplot(gs[0, 1])
    netviz.draw_network(ax, NODES, con_e, directed=False, weight_ref=wref,
                        title="Contemporaneous (same beep)")
    vs.panel_label(ax, "B", dx=0.02, dy=1.02)

    ax = fig.add_subplot(gs[0, 2])
    netviz.draw_network(ax, NODES, btw_e, directed=False,
                        weight_ref=max(abs(btw["pcor"])),
                        title="Between-person (trait level)")
    vs.panel_label(ax, "C", dx=0.02, dy=1.02)

    vs.savefig(fig, paths.FIG_MAIN / "MAIN_02_mlvar_networks.png")


# ===========================================================================
# MAIN_03 - Fixed temporal effects + individual heterogeneity
# ===========================================================================
def main_04():
    temp = pd.read_csv(N / "05_mlvar_core_temporal_edges.csv")
    ols = pd.read_csv(N / "07_perperson_var_ols_wide.csv")
    edges = pd.read_csv(N / "07_perperson_var_ols_edges.csv")
    fixed = {(r["from"], r["to"]): r["weight"] for _, r in temp.iterrows()}

    temp["ci_lo"] = temp["weight"] - 1.96 * temp["SE"]
    temp["ci_hi"] = temp["weight"] + 1.96 * temp["SE"]
    temp["label"] = [f"{vs.node_label(f)} -> {vs.node_label(t)}"
                     for f, t in zip(temp["from"], temp["to"])]
    temp["is_ar"] = temp["from"] == temp["to"]
    temp = temp.sort_values(["is_ar", "weight"]).reset_index(drop=True)

    fig = plt.figure(figsize=(14, 11.5))
    gs = GridSpec(2, 2, figure=fig, height_ratios=[1.0, 1.0], hspace=0.28, wspace=0.14)
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 0])
    ax_d = fig.add_subplot(gs[1, 1])

    # A: forest plot of fixed effects
    ax = ax_a
    y = np.arange(len(temp))
    for i, r in temp.iterrows():
        sig = r["P"] < 0.05
        col = vs.EDGE_POS if r["weight"] >= 0 else vs.EDGE_NEG
        ax.plot([r["ci_lo"], r["ci_hi"]], [i, i], color=col,
                lw=2.4 if sig else 1.4, alpha=0.95 if sig else 0.4, solid_capstyle="round")
        ax.plot(r["weight"], i, "o", color=col, ms=8 if sig else 5,
                alpha=0.95 if sig else 0.4,
                markeredgecolor="white", markeredgewidth=1)
    ax.axvline(0, color=vs.INK, lw=0.9)
    ax.set_yticks(y)
    ax.set_yticklabels(temp["label"], fontsize=8.5)
    ax.set_xlabel("standardized lag-1 coefficient (95% CI)")
    ax.set_title("Group-level temporal effects (mlVAR fixed effects)")
    n_cross = (~temp["is_ar"]).sum()
    ax.axhline(n_cross - 0.5, color=vs.GRID, lw=1)
    vs.panel_label(ax, "A")

    # B: individual heterogeneity in key couplings (per-person OLS VAR), with the
    # group fixed effect marked so the small group mean and the wide spread are comparable
    ax = ax_b
    keys = ["PIJN__to__ENMO_log", "MOE__to__ENMO_log", "STRESS__to__ENMO_log",
            "ENMO_log__to__PIJN", "ENMO_log__to__MOE", "STRESS__to__PIJN"]
    fkeys = [("PIJN", "ENMO_log"), ("MOE", "ENMO_log"), ("STRESS", "ENMO_log"),
             ("ENMO_log", "PIJN"), ("ENMO_log", "MOE"), ("STRESS", "PIJN")]
    keylab = ["Pain ->\nActivity", "Fatigue ->\nActivity", "Stress ->\nActivity",
              "Activity ->\nPain", "Activity ->\nFatigue", "Stress ->\nPain"]
    data = [ols[k].dropna().values for k in keys]
    positions = np.arange(len(keys))
    parts = ax.violinplot(data, positions=positions, showextrema=False, widths=0.8)
    for pc in parts["bodies"]:
        pc.set_facecolor(vs.NODE_COLORS["ENMO"])
        pc.set_alpha(0.25)
    rng = np.random.default_rng(7)
    for i, d in enumerate(data):
        jit = rng.uniform(-0.12, 0.12, len(d))
        ax.scatter(positions[i] + jit, d, s=22, color=vs.NODE_COLORS["STRESS"],
                   alpha=0.7, edgecolor="white", linewidth=0.4, zorder=3)
        ax.plot([i - 0.28, i + 0.28], [np.mean(d)] * 2, color=vs.INK, lw=2.2, zorder=4)
        fe = fixed[fkeys[i]]
        ax.plot(i, fe, "D", color=vs.EDGE_NEG, ms=7, markeredgecolor="white",
                markeredgewidth=0.8, zorder=5)
    ax.axhline(0, color=vs.MUTED, lw=0.9, ls="--")
    ax.set_xticks(positions)
    ax.set_xticklabels(keylab, fontsize=8.5)
    ax.set_ylabel("per-person standardized coefficient")
    ax.set_title("Individuals diverge widely around the group mean")
    ax.plot([], [], color=vs.INK, lw=2.2, label="per-person mean")
    ax.plot([], [], "D", color=vs.EDGE_NEG, ms=7, label="mlVAR fixed effect")
    ax.legend(fontsize=8, loc="upper left")
    vs.panel_label(ax, "B")

    # C: idiographic feasibility - per-person Pain->Activity estimate with 95% CI
    ax = ax_c
    pa = edges[edges["edge"] == "PIJN__to__ENMO_log"].copy()
    pa["lo"] = pa["coef"] - 1.96 * pa["se"]
    pa["hi"] = pa["coef"] + 1.96 * pa["se"]
    pa = pa.sort_values("coef").reset_index(drop=True)
    excl = (pa["lo"] > 0) | (pa["hi"] < 0)
    for i, r in pa.iterrows():
        col = vs.EDGE_NEG if r["coef"] < 0 else vs.EDGE_POS
        e = excl.iloc[i]
        ax.plot([r["lo"], r["hi"]], [i, i], color=col, lw=1.8 if e else 1.0,
                alpha=0.95 if e else 0.4, solid_capstyle="round")
        ax.plot(r["coef"], i, "o", color=col, ms=5 if e else 3.5,
                alpha=0.95 if e else 0.5, markeredgecolor="white", markeredgewidth=0.5)
    ax.axvline(0, color=vs.INK, lw=0.9)
    ax.set_yticks(np.arange(len(pa)))
    ax.set_yticklabels(pa["pid"], fontsize=5.4)
    ax.tick_params(axis="y", length=0, pad=1)
    ax.set_ylabel("participant", labelpad=2)
    ax.set_xlabel("per-person Pain -> Activity coefficient (95% CI)")
    ax.set_title(f"Imprecise individual estimates ({int(excl.sum())}/{len(pa)} CIs exclude 0)")
    vs.panel_label(ax, "C")

    # D: between-person heterogeneity network. Edge width and colour intensity both scale
    # with the SD of the per-person OLS coefficient (the mlVAR random-effect SD is shrunk to
    # zero for the symptom-to-activity paths, which would hide their true heterogeneity).
    ax = ax_d
    from matplotlib.colors import LinearSegmentedColormap, Normalize
    from matplotlib.cm import ScalarMappable
    hetcmap = LinearSegmentedColormap.from_list("het", ["#d9d2e8", "#9b8bbf", "#4a3a6b"])
    het_edges = []
    for frm in NODES:
        for to in NODES:
            k = f"{frm}__to__{to}"
            if k in ols.columns:
                het_edges.append({"from": frm, "to": to,
                                  "weight": float(ols[k].std(ddof=1))})
    wref = max(e["weight"] for e in het_edges)
    netviz.draw_network(ax, NODES, het_edges, directed=True, weight_ref=wref,
                        edge_cmap=hetcmap, max_lw=5.6,
                        title="Between-person heterogeneity network")
    ax.set_anchor("W")  # left-align so network's left edge matches panel B's left edge
    sm = ScalarMappable(norm=Normalize(0, wref), cmap=hetcmap)
    sm.set_array([])
    # Cell is square (3.884 × 3.884 in), so network fills the full bounding box.
    # Activity self-loop right edge = 0.910 of cell; place colorbar at 0.935 (0.12 in gap).
    cax_d = ax_d.inset_axes([0.952, 0.06, 0.04, 0.86])
    cb = fig.colorbar(sm, cax=cax_d)
    cb.set_label("SD of per-person\nlag-1 coefficient", fontsize=8)
    cb.ax.tick_params(labelsize=8)
    vs.panel_label(ax, "D", dx=0.02, dy=1.02)

    vs.savefig(fig, paths.FIG_MAIN / "MAIN_03_temporal_effects_heterogeneity.png")


# ===========================================================================
# MAIN_04 - POAM-P subgroups and the RQ1<->RQ2 bridge
# ===========================================================================
def _ci95(vals):
    """Mean and half-width of a 95% t confidence interval."""
    vals = np.asarray(vals, float)
    vals = vals[~np.isnan(vals)]
    n = len(vals)
    if n < 2:
        return (vals.mean() if n else np.nan), 0.0
    se = vals.std(ddof=1) / np.sqrt(n)
    return vals.mean(), stats.t.ppf(0.975, n - 1) * se


def _coupling_vs_score(ax, d, score_col, score_label, order, letter, show_legend=False):
    """Per-person Pain to Activity coupling against one POAM-P subscale, with
    per-subgroup OLS fits, CI bands, and an overall reference trend."""
    import statsmodels.api as sm
    for g in order:
        dg = d[d["dominant_pattern"] == g]
        ax.scatter(dg[score_col], dg["PIJN__to__ENMO_log"], s=42,
                   color=vs.POAMP_COLORS[g], label=g, edgecolor="white",
                   linewidth=0.5, zorder=3)
        if len(dg) >= 4 and dg[score_col].nunique() >= 3:
            X = sm.add_constant(dg[score_col].values)
            mod = sm.OLS(dg["PIJN__to__ENMO_log"].values, X).fit()
            xs = np.linspace(dg[score_col].min(), dg[score_col].max(), 40)
            pr = mod.get_prediction(sm.add_constant(xs)).summary_frame(alpha=0.05)
            ax.plot(xs, pr["mean"], color=vs.POAMP_COLORS[g], lw=2, zorder=2)
            ax.fill_between(xs, pr["mean_ci_lower"], pr["mean_ci_upper"],
                            color=vs.POAMP_COLORS[g], alpha=0.13, zorder=1)
    Xall = sm.add_constant(d[score_col].values)
    modall = sm.OLS(d["PIJN__to__ENMO_log"].values, Xall).fit()
    xs = np.linspace(d[score_col].min(), d[score_col].max(), 40)
    rho = d[[score_col, "PIJN__to__ENMO_log"]].corr(method="spearman").iloc[0, 1]
    ax.plot(xs, modall.predict(sm.add_constant(xs)), color=vs.INK, lw=1.3, ls="--", zorder=2)
    ax.axhline(0, color=vs.MUTED, ls=":", lw=0.9)
    ax.set_xlabel(f"POAM-P {score_label} score")
    ax.set_ylabel("per-person Pain -> Activity coefficient")
    ax.set_title(f"Coupling vs {score_label.lower()} ($\\rho$ = {rho:.2f})")
    if show_legend:
        ax.legend(fontsize=8, title="dominant pattern", title_fontsize=8)
    vs.panel_label(ax, letter)


def main_05():
    sub = pd.read_csv(paths.DATA_PROCESSED / "poamp_subgroups.csv")
    link = pd.read_csv(paths.DATA_PROCESSED / "link_analysis_frame.csv")
    corr = pd.read_csv(T / "09_param_poamp_correlations.csv")
    order = ["Avoidance", "Overdoing", "Pacing"]

    fig = plt.figure(figsize=(15.5, 10.2))
    gs = GridSpec(2, 3, figure=fig, hspace=0.40, wspace=0.34)

    # A: dominant-pattern profiles with 95% CI error bars (computed from raw scores)
    ax = fig.add_subplot(gs[0, 0])
    subs = ["POAMP_Avoidance", "POAMP_Overdoing", "POAMP_Pacing"]
    sublab = ["Avoidance", "Overdoing", "Pacing"]
    x = np.arange(len(subs))
    w = 0.26
    for i, g in enumerate(order):
        gdat = sub[sub["dominant_pattern"] == g]
        means = [_ci95(gdat[s])[0] for s in subs]
        errs = [_ci95(gdat[s])[1] for s in subs]
        ax.bar(x + (i - 1) * w, means, w, yerr=errs, capsize=2.5,
               error_kw=dict(lw=1, ecolor=vs.INK),
               label=f"{g} (n={len(gdat)})", color=vs.POAMP_COLORS[g], alpha=0.9)
    ax.set_xticks(x); ax.set_xticklabels(sublab)
    ax.set_ylabel("POAM-P subscale score (0-40)")
    ax.set_title("Three activity-pattern subgroups (POAM-P)")
    ax.legend(fontsize=8, title="dominant pattern", title_fontsize=8)
    vs.bar_axes(ax, "vertical")
    vs.panel_label(ax, "A")

    # B: Pain->Activity coupling by subgroup - raw points + group mean with 95% CI
    ax = fig.add_subplot(gs[0, 1])
    positions = np.arange(len(order))
    rng = np.random.default_rng(3)
    for i, g in enumerate(order):
        d = link.loc[link["dominant_pattern"] == g, "PIJN__to__ENMO_log"].dropna().values
        ax.scatter(positions[i] + rng.uniform(-0.16, 0.16, len(d)), d, s=34,
                   color=vs.POAMP_COLORS[g], edgecolor="white", linewidth=0.5,
                   alpha=0.75, zorder=2)
        m, h = _ci95(d)
        ax.errorbar(positions[i], m, yerr=h, fmt="o", ms=9, color=vs.INK,
                    capsize=5, lw=2, zorder=4)
        ax.plot([positions[i] - 0.28, positions[i] + 0.28], [m, m], color=vs.INK,
                lw=2, zorder=4)
    ax.axhline(0, color=vs.MUTED, ls="--", lw=0.9)
    ax.set_xticks(positions); ax.set_xticklabels(order)
    ax.set_xlim(-0.5, 2.5)
    ax.set_ylabel("per-person Pain -> Activity coefficient")
    ax.set_title("Pain -> Activity coupling by subgroup\n(points + group mean, 95% CI)")
    vs.panel_label(ax, "B")

    # C, D, E: per-person Pain->Activity coupling vs each POAM-P subscale
    _coupling_vs_score(fig.add_subplot(gs[0, 2]),
                       link.dropna(subset=["PIJN__to__ENMO_log", "POAMP_Avoidance"]),
                       "POAMP_Avoidance", "Avoidance", order, "C", show_legend=True)
    _coupling_vs_score(fig.add_subplot(gs[1, 0]),
                       link.dropna(subset=["PIJN__to__ENMO_log", "POAMP_Overdoing"]),
                       "POAMP_Overdoing", "Overdoing", order, "D")
    _coupling_vs_score(fig.add_subplot(gs[1, 1]),
                       link.dropna(subset=["PIJN__to__ENMO_log", "POAMP_Pacing"]),
                       "POAMP_Pacing", "Pacing", order, "E")

    # F: coupling-by-POAM-P correlation heatmap (which dynamics relate to which pattern)
    ax = fig.add_subplot(gs[1, 2])
    rows = ["Pain -> Activity", "Fatigue -> Activity", "Stress -> Activity",
            "Activity -> Pain", "Activity -> Fatigue", "Temporal density"]
    cols = ["Avoidance", "Overdoing", "Pacing"]
    rho = corr.pivot(index="parameter", columns="poamp_subscale",
                     values="spearman_rho").reindex(index=rows, columns=cols)
    pmat = corr.pivot(index="parameter", columns="poamp_subscale",
                      values="p_value").reindex(index=rows, columns=cols)
    im = ax.imshow(rho.values, cmap="RdBu_r", vmin=-0.6, vmax=0.6, aspect="auto")
    ax.set_xticks(range(len(cols))); ax.set_xticklabels(cols, rotation=20, ha="right")
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r.replace(" -> ", " to ") for r in rows], fontsize=8)
    for i in range(len(rows)):
        for j in range(len(cols)):
            star = "*" if pmat.values[i, j] < 0.05 else ""
            ax.text(j, i, f"{rho.values[i, j]:.2f}{star}", ha="center", va="center",
                    fontsize=8, color=vs.INK if abs(rho.values[i, j]) < 0.4 else "white")
    ax.set_title("Coupling-by-POAM-P correlations (Spearman)")
    vs.matrix_axes(ax)
    vs.add_cbar(fig, ax, im)
    vs.panel_label(ax, "F")

    vs.savefig(fig, paths.FIG_MAIN / "MAIN_04_poamp_subgroups_link.png")


if __name__ == "__main__":
    main_02()
    main_03()
    main_04()
    main_05()
    print("\nMain figures written to", paths.FIG_MAIN)
