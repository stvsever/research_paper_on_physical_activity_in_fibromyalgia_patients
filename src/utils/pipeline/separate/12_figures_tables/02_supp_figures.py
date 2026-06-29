"""Stage 12.2 - Supplementary figures (SUP_01 .. SUP_15).

Multi-panel PNGs saved to paper/assets/figures/supplementary. Panels carry their own
titles and bold letters; no global suptitles.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf

LIB = Path(__file__).resolve().parents[3] / "lib"
sys.path.insert(0, str(LIB))
import paths  # noqa: E402
import vizstyle as vs  # noqa: E402
import netviz  # noqa: E402

vs.apply_style()
paths.ensure_dirs()
T = paths.RESULTS_TABLES
N = paths.RESULTS_NETWORKS
S = paths.FIG_SUPP
NODES = ["PIJN", "MOE", "STRESS", "ENMO_log"]
ema = pd.read_csv(paths.EMA_LONG)


def _p_label(p: float) -> str:
    if pd.isna(p):
        return "ns"
    if p < .001:
        return "***"
    if p < .01:
        return "**"
    if p < .05:
        return "*"
    return "ns"


def _sig_bar(ax, x1, x2, y, p, h=0.08, fontsize=9):
    ax.plot([x1, x1, x2, x2], [y, y + h, y + h, y], color=vs.INK, lw=1.0, clip_on=False)
    ax.text((x1 + x2) / 2, y + h * 1.15, _p_label(p), ha="center", va="bottom",
            fontsize=fontsize, color=vs.INK)


def _fmt_p(p: float) -> str:
    if pd.isna(p):
        return "p = NA"
    if p < .001:
        return "p < .001"
    return f"p = {p:.3f}".replace("0.", ".")


def _hour_label(x: float) -> str:
    h = int(np.floor(x))
    m = int(round((x - h) * 60))
    if m == 60:
        h += 1
        m = 0
    return f"{h:02d}:{m:02d}"


def _violin_scatter_pair(ax, values, positions, colors, rng, width=0.72, point_size=12,
                         alpha=0.18, median_color=None):
    """Draw raw violin/scatter distributions with explicit mean and median markers."""
    clean = [pd.Series(v).dropna().astype(float).to_numpy() for v in values]
    parts = ax.violinplot(clean, positions=positions, showextrema=False, widths=width)
    for pc, col in zip(parts["bodies"], colors):
        pc.set_facecolor(col)
        pc.set_alpha(0.24)
        pc.set_edgecolor(col)
        pc.set_linewidth(0.8)
    for pos, d, col in zip(positions, clean, colors):
        jit = rng.uniform(-width * 0.20, width * 0.20, len(d))
        ax.scatter(pos + jit, d, s=point_size, color=col, alpha=alpha,
                   edgecolor="white", linewidth=0.2, zorder=3)
        if len(d):
            mean = float(np.mean(d))
            med = float(np.median(d))
            ax.plot([pos - width * 0.24, pos + width * 0.24], [mean, mean],
                    color=vs.INK, lw=2.0, zorder=5)
            ax.plot(pos, med, marker="D", ms=5.2, color=median_color or "white",
                    markeredgecolor=vs.INK, markeredgewidth=0.8, zorder=6)


# SUP_01 - Design, compliance, and data quality --------------------------------
def sup_design():
    comp = pd.read_csv(T / "02_compliance_per_person.csv")
    byday = pd.read_csv(T / "04_compliance_by_day.csv")
    desc = pd.read_csv(T / "02_ema_descriptives.csv")

    fig = plt.figure(figsize=(13, 9))
    gs = GridSpec(2, 2, figure=fig, hspace=0.34, wspace=0.24)

    ax = fig.add_subplot(gs[0, 0])
    c = comp.sort_values("sum").reset_index(drop=True)
    ax.bar(range(len(c)), c["sum"], color=vs.NODE_COLORS["ENMO"], alpha=0.85)
    med = c["sum"].median()
    ax.axhline(med, color=vs.INK, ls="--", lw=1)
    ax.text(0.5, med + 1.2, f"median = {med:.0f}", color=vs.INK, fontsize=9)
    ax.axhline(56, color=vs.MUTED, ls=":", lw=1)
    ax.text(len(c) - 0.5, 56.5, "max 56", ha="right", color=vs.MUTED, fontsize=8)
    ax.set_xlabel("participant (sorted)")
    ax.set_ylabel("completed prompts")
    ax.set_title("Completed EMA prompts per participant")
    ax.grid(axis="y", visible=True)
    ax.grid(axis="x", visible=False)
    vs.panel_label(ax, "A")

    ax = fig.add_subplot(gs[0, 1])
    ax.plot(byday["day"], 100 * byday["responded"], "-o", color=vs.NODE_COLORS["PIJN"],
            lw=2, ms=5)
    ax.set_ylim(40, 100)
    ax.set_xlabel("study day")
    ax.set_ylabel("prompts answered (%)")
    ax.set_title("Compliance across the 14-day protocol")
    vs.panel_label(ax, "B")

    ax = fig.add_subplot(gs[1, 0])
    raw = ema["ENMO"].dropna()
    ax.hist(raw, bins=35, color=vs.NODE_COLORS["ENMO"], alpha=0.85)
    ax.set_xlabel("ENMO (g) - raw scale")
    ax.set_ylabel("count")
    ax.set_title("Objective activity is right-skewed (modelled as log)")
    axin = ax.inset_axes([0.50, 0.50, 0.46, 0.44])
    axin.hist(ema["ENMO_log"].dropna(), bins=35, color=vs.NODE_COLORS["EIGENEFF"],
              alpha=0.85)
    axin.set_title("log ENMO", fontsize=8)
    axin.tick_params(labelsize=7)
    vs.panel_label(ax, "C")

    ax = fig.add_subplot(gs[1, 1])
    dd = desc[desc["variable"].isin(["PIJN", "MOE", "STRESS", "ENMO_log",
                                     "EIGENEFF", "INTENTIE", "UITKOMSTVERW"])].copy()
    order = ["PIJN", "MOE", "STRESS", "ENMO_log", "EIGENEFF", "INTENTIE", "UITKOMSTVERW"]
    dd = dd.set_index("variable").loc[order].reset_index()
    y = np.arange(len(dd))
    ax.barh(y - 0.2, dd["sd_within_person"], height=0.38,
            color=vs.NODE_COLORS["PIJN"], label="within-person")
    ax.barh(y + 0.2, dd["sd_between_person"], height=0.38,
            color=vs.MUTED, label="between-person")
    ax.set_yticks(y)
    ax.set_yticklabels([vs.node_label(v) for v in dd["variable"]])
    ax.invert_yaxis()
    ax.set_xlabel("standard deviation")
    ax.set_title("Substantial within-person variability in every measure")
    ax.legend(loc="lower right")
    vs.bar_axes(ax, "horizontal")
    vs.panel_label(ax, "D")

    vs.savefig(fig, S / "SUP_01_design_compliance.png")


# SUP_02 - EMA protocol timing audit ------------------------------------------
def sup_timing():
    from matplotlib.patches import Rectangle

    timing = pd.read_csv(T / "02_timing_long.csv")
    daily = pd.read_csv(T / "02_timing_daily_counts.csv")
    daytype = pd.read_csv(T / "02_timing_daytype_person.csv")
    tests = pd.read_csv(T / "02_timing_tests.csv")
    summ = pd.read_csv(T / "02_timing_summary.csv").set_index("metric")
    rng = np.random.default_rng(2606)

    def p_for(name):
        vals = tests.loc[tests["test"] == name, "p"]
        return float(vals.iloc[0]) if len(vals) else np.nan

    fig = plt.figure(figsize=(15.6, 10.2))
    gs = GridSpec(2, 3, figure=fig, hspace=0.44, wspace=0.32)

    # A: trigger rows by study day
    ax = fig.add_subplot(gs[0, 0])
    day = daily["day"].to_numpy()
    completed = daily["completed"].to_numpy()
    observed = daily["observed_triggers"].to_numpy()
    missed = observed - completed
    missing_rows = daily["missing_trigger_rows"].to_numpy()
    ax.bar(day, completed, color=vs.NODE_COLORS["ENMO"], alpha=0.88, label="completed")
    ax.bar(day, missed, bottom=completed, color=vs.MUTED, alpha=0.36, label="not completed")
    ax.bar(day, missing_rows, bottom=observed, facecolor="none", edgecolor=vs.NODE_COLORS["PIJN"],
           hatch="///", linewidth=0.8, label="missing trigger row")
    ax.axhline(daily["expected_triggers"].iloc[0], color=vs.INK, lw=1.0, ls="--")
    ax.set_xticks(range(1, 15))
    ax.set_xlabel("study day")
    ax.set_ylabel("trigger rows")
    ax.set_ylim(0, daily["expected_triggers"].iloc[0] + 9)
    expected = int(summ.loc["Expected trigger rows", "n"])
    observed_total = int(summ.loc["Observed trigger rows", "n"])
    completed_total = int(summ.loc["Completed trigger rows", "n"])
    ax.set_title(f"Observed trigger rows: {observed_total}/{expected}")
    ax.text(0.03, 0.94, f"{completed_total} completed prompts", transform=ax.transAxes,
            ha="left", va="top", fontsize=8.5,
            bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor=vs.GRID))
    ax.legend(fontsize=7, loc="lower right")
    vs.bar_axes(ax, "vertical")
    vs.panel_label(ax, "A")

    # B: scheduled clock time by daily prompt
    ax = fig.add_subplot(gs[0, 1])
    windows = {1: (10.0, 10.5), 2: (12.5, 13.0), 3: (15.0, 15.5), 4: (17.5, 18.0)}
    for beep, (lo, hi) in windows.items():
        ax.add_patch(Rectangle((beep - 0.42, lo), 0.84, hi - lo,
                               facecolor=vs.GRID, edgecolor="none", alpha=0.45, zorder=0))
    t = timing.dropna(subset=["scheduled_hour", "beep"]).copy()
    outside = ~t["within_beep_window"].astype(bool)
    x = t["beep"].to_numpy() + rng.uniform(-0.18, 0.18, len(t))
    ax.scatter(x[~outside], t.loc[~outside, "scheduled_hour"], s=10,
               color=vs.NODE_COLORS["ENMO"], alpha=0.18, edgecolor="none")
    ax.scatter(x[outside], t.loc[outside, "scheduled_hour"], s=18,
               color=vs.NODE_COLORS["PIJN"], alpha=0.65, edgecolor="white", linewidth=0.2)
    ax.set_xticks([1, 2, 3, 4])
    ax.set_xlabel("prompt of day")
    yticks = [10, 10.5, 12.5, 13, 15, 15.5, 17.5, 18, 19]
    ax.set_yticks(yticks)
    ax.set_yticklabels([_hour_label(v) for v in yticks], fontsize=8)
    ax.set_ylim(9.8, 19.15)
    out_window = int((~timing["within_beep_window"].astype(bool)).sum())
    out_10_18 = int((~timing["within_10_18"].astype(bool)).sum())
    ax.set_title(f"Scheduled clock times ({out_window} outside target windows)")
    ax.text(0.03, 0.06, f"{out_10_18} rows after 18:00", transform=ax.transAxes,
            ha="left", va="bottom", fontsize=8.5,
            bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor=vs.GRID))
    vs.panel_label(ax, "B")

    # C: adjacent-prompt intervals
    ax = fig.add_subplot(gs[0, 2])
    d_int = timing[timing["beep"].isin([2, 3, 4])].dropna(subset=["scheduled_interval_min"])
    labels = ["1-2", "2-3", "3-4"]
    vals = [d_int.loc[d_int["interval_label"] == lab, "scheduled_interval_min"] for lab in labels]
    _violin_scatter_pair(ax, vals, [0, 1, 2],
                         [vs.CLUSTER_COLORS[0], vs.CLUSTER_COLORS[2], vs.CLUSTER_COLORS[3]],
                         rng, width=0.70, point_size=8, alpha=0.11)
    for y, style in [(120, ":"), (150, "--"), (180, ":")]:
        ax.axhline(y, color=vs.INK if y == 150 else vs.MUTED, lw=0.9, ls=style)
    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(labels)
    ax.set_xlabel("adjacent prompt pair")
    ax.set_ylabel("scheduled interval (min)")
    ax.set_ylim(112, 188)
    ax.set_title(f"Adjacent-prompt spacing (GEE {_fmt_p(p_for('adjacent_prompt_interval_by_pair'))})")
    vs.panel_label(ax, "C")

    # D: weekday versus weekend completion
    ax = fig.add_subplot(gs[1, 0])
    wide = daytype.pivot(index="pid", columns="is_weekend", values="completion_pct").dropna()
    for _, row in wide.iterrows():
        ax.plot([0, 1], [row[0], row[1]], color=vs.GRID, lw=0.7, alpha=0.75, zorder=1)
    _violin_scatter_pair(ax, [wide[0], wide[1]], [0, 1],
                         [vs.MUTED, vs.NODE_COLORS["STRESS"]], rng,
                         width=0.68, point_size=20, alpha=0.62)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Weekday", "Weekend"])
    ax.set_ylabel("completed prompts per participant (%)")
    ax.set_ylim(0, 107)
    p_weekend = p_for("completion_by_weekend")
    _sig_bar(ax, 0, 1, 99, p_weekend, h=2.0)
    ax.set_title(f"Weekend completion lower (GEE {_fmt_p(p_weekend)})")
    ax.text(0.02, 0.06, "paired Wilcoxon p = .056", transform=ax.transAxes,
            ha="left", va="bottom", fontsize=8,
            bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor=vs.GRID))
    vs.panel_label(ax, "D")

    # E: response latency by prompt
    ax = fig.add_subplot(gs[1, 1])
    d_lat = timing.dropna(subset=["start_latency_min", "beep"])
    vals = [d_lat.loc[d_lat["beep"] == b, "start_latency_min"] for b in [1, 2, 3, 4]]
    _violin_scatter_pair(ax, vals, [1, 2, 3, 4],
                         [vs.NODE_COLORS["ENMO"], vs.NODE_COLORS["EIGENEFF"],
                          vs.NODE_COLORS["MOE"], vs.NODE_COLORS["PIJN"]],
                         rng, width=0.72, point_size=7, alpha=0.10)
    ax.axhline(20, color=vs.MUTED, lw=0.9, ls=":", label="expiry")
    ax.set_xticks([1, 2, 3, 4])
    ax.set_xlabel("prompt of day")
    ax.set_ylabel("minutes from scheduled prompt to start")
    ax.set_ylim(-1, 21.5)
    latency_med = summ.loc["Response latency, scheduled to started (minutes)", "median"]
    latency_max = summ.loc["Response latency, scheduled to started (minutes)", "max"]
    ax.set_title(f"Response latency: median {latency_med:.0f} min, max {latency_max:.0f}")
    ax.text(0.03, 0.94, f"prompt effect GEE {_fmt_p(p_for('response_latency_by_prompt'))}",
            transform=ax.transAxes, ha="left", va="top", fontsize=8.5,
            bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor=vs.GRID))
    vs.panel_label(ax, "E")

    # F: questionnaire duration by prompt
    ax = fig.add_subplot(gs[1, 2])
    d_dur = timing.dropna(subset=["completion_duration_min", "beep"])
    vals = [d_dur.loc[d_dur["beep"] == b, "completion_duration_min"] for b in [1, 2, 3, 4]]
    _violin_scatter_pair(ax, vals, [1, 2, 3, 4],
                         [vs.NODE_COLORS["ENMO"], vs.NODE_COLORS["EIGENEFF"],
                          vs.NODE_COLORS["MOE"], vs.NODE_COLORS["PIJN"]],
                         rng, width=0.72, point_size=7, alpha=0.10)
    ax.set_xticks([1, 2, 3, 4])
    ax.set_xlabel("prompt of day")
    ax.set_ylabel("completion duration (min)")
    ax.set_ylim(-0.5, 8.8)
    dur_med = summ.loc["Questionnaire duration, started to completed (minutes)", "median"]
    dur_max = summ.loc["Questionnaire duration, started to completed (minutes)", "max"]
    ax.set_title(f"Questionnaire duration: median {dur_med:.0f} min, max {dur_max:.0f}")
    ax.text(0.03, 0.94, f"prompt effect GEE {_fmt_p(p_for('questionnaire_duration_by_prompt'))}",
            transform=ax.transAxes, ha="left", va="top", fontsize=8.5,
            bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor=vs.GRID))
    vs.panel_label(ax, "F")

    vs.savefig(fig, S / "SUP_02_ema_timing.png")


# SUP_03 - ENMO transformation + stationarity ---------------------------------
def sup_01():
    from scipy.stats import skew as _skew
    skew = pd.read_csv(T / "04_enmo_skewness.csv")
    stat = pd.read_csv(T / "04_stationarity_summary.csv")
    fig = plt.figure(figsize=(13, 12))
    gs = GridSpec(3, 2, figure=fig, hspace=0.40, wspace=0.26)

    # A: pooled skewness by transformation
    ax = fig.add_subplot(gs[0, 0])
    ax.bar(skew["measure"], skew["skewness"], color=vs.NODE_COLORS["ENMO"], alpha=0.85)
    ax.axhline(0, color=vs.INK, lw=0.9)
    for i, v in enumerate(skew["skewness"]):
        ax.text(i, v + (0.05 if v >= 0 else -0.12), f"{v:.2f}", ha="center", fontsize=9)
    ax.set_ylabel("skewness")
    ax.set_title("ENMO skewness by transformation (log near-symmetric)")
    vs.bar_axes(ax, "vertical")
    vs.panel_label(ax, "A")

    # B: share of individual series flagged non-stationary
    ax = fig.add_subplot(gs[0, 1])
    y = np.arange(len(stat))
    ax.barh(y - 0.2, 100 * stat["prop_sig_linear_trend"], 0.38,
            color=vs.NODE_COLORS["PIJN"], label="significant linear trend")
    ax.barh(y + 0.2, 100 * stat["prop_kpss_nonstationary"], 0.38,
            color=vs.MUTED, label="KPSS non-stationary")
    ax.set_yticks(y); ax.set_yticklabels([vs.node_label(v) for v in stat["variable"]])
    ax.set_xlabel("% of individual series")
    ax.set_title("Most individual series are stationary")
    ax.legend(fontsize=8)
    vs.bar_axes(ax, "horizontal")
    vs.panel_label(ax, "B")

    # D: per-person skewness, raw vs log (transformation at the individual level)
    ax = fig.add_subplot(gs[2, 0])
    per = []
    for pid, gg in ema.groupby("pid"):
        raw = gg["ENMO"].dropna()
        lg = gg["ENMO_log"].dropna()
        if len(raw) >= 10 and len(lg) >= 10:
            per.append((float(_skew(raw)), float(_skew(lg))))
    per = np.array(per)
    ax.scatter(per[:, 0], per[:, 1], s=42, color=vs.NODE_COLORS["ENMO"],
               edgecolor="white", linewidth=0.5, alpha=0.8, zorder=3)
    lim = [min(per.min(), -0.5) - 0.2, per.max() + 0.2]
    ax.plot(lim, lim, color=vs.MUTED, ls="--", lw=1, zorder=1)
    ax.axhline(0, color=vs.GRID, lw=0.9); ax.axvline(0, color=vs.GRID, lw=0.9)
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("per-person skewness (raw ENMO)")
    ax.set_ylabel("per-person skewness (log ENMO)")
    ax.set_title(f"Log reduces skew for {int((per[:,1] < per[:,0]).mean()*100)}% of persons")
    vs.panel_label(ax, "D")

    # E: within-day lag-k autocorrelation of activity, averaged over persons
    ax = fig.add_subplot(gs[2, 1])
    d = ema.dropna(subset=["ENMO_log"]).copy()
    d["z"] = d.groupby("pid")["ENMO_log"].transform(
        lambda s: (s - s.mean()) / s.std(ddof=0) if s.std(ddof=0) > 0 else s * 0)
    d = d.sort_values(["pid", "day", "beep"])
    lags = [1, 2, 3]
    means, errs = [], []
    for k in lags:
        d["z_lag"] = d.groupby(["pid", "day"])["z"].shift(k)
        sub = d.dropna(subset=["z", "z_lag"])
        rs = (sub.groupby("pid")
              .apply(lambda g: np.corrcoef(g["z"], g["z_lag"])[0, 1]
                     if len(g) > 3 else np.nan)
              .dropna())
        means.append(rs.mean())
        errs.append(1.96 * rs.std(ddof=1) / np.sqrt(len(rs)))
    ax.bar(lags, means, yerr=errs, capsize=4, color=vs.NODE_COLORS["ENMO"], alpha=0.85,
           error_kw=dict(lw=1, ecolor=vs.INK))
    ax.axhline(0, color=vs.INK, lw=0.9)
    for k, m in zip(lags, means):
        ax.text(k, m / 2, f"{m:.2f}", ha="center", va="center", color="white",
                fontweight="bold", fontsize=9)
    ax.set_xticks(lags)
    ax.set_xlabel("within-day lag (prompts)")
    ax.set_ylabel("mean within-person autocorrelation")
    ax.set_title("Activity autocorrelation decays quickly (short memory)")
    vs.bar_axes(ax, "vertical")
    vs.panel_label(ax, "E")

    # C: example individual activity series (spans the middle row)
    ax = fig.add_subplot(gs[1, :])
    ids = ema["pid"].unique()[:6]
    for i, pid in enumerate(ids):
        s = ema[ema["pid"] == pid]
        ax.plot(s["obs"], s["ENMO_log"] + i * 2.2, lw=1, alpha=0.85,
                color=plt.cm.viridis(i / 6))
        ax.text(s["obs"].max() + 0.5, (s["ENMO_log"] + i * 2.2).mean(), pid,
                fontsize=7, va="center", color=vs.MUTED)
    ax.set_xlabel("observation (prompt index within person)")
    ax.set_ylabel("log ENMO (stacked, offset per person)")
    ax.set_title("Example within-person activity time series (6 participants)")
    ax.set_yticks([])
    vs.panel_label(ax, "C", dx=-0.03)
    vs.savefig(fig, S / "SUP_03_stationarity_transform.png")


# SUP_04 - Missingness / compliance -------------------------------------------
def sup_02():
    mnar = pd.read_csv(T / "04_enmo_missingness_mnar_probe.csv")
    fig = plt.figure(figsize=(13, 7.5))
    gs = GridSpec(2, 2, figure=fig, hspace=0.36, wspace=0.26,
                  height_ratios=[1.3, 1.0])

    # A: missingness matrix person x prompt index
    ax = fig.add_subplot(gs[0, :])
    piv = ema.pivot_table(index="pid", columns="obs", values="completed",
                          aggfunc="first")
    piv = piv.reindex(sorted(piv.index, key=lambda p: int(p[1:])))
    ax.imshow(piv.values.astype(float), aspect="auto", cmap="Greys_r",
              interpolation="nearest", vmin=0, vmax=1)
    ax.set_xlabel("prompt index within person")
    ax.set_ylabel("participant")
    ax.set_yticks(range(len(piv.index)))
    ax.set_yticklabels(
        [piv.index[i] if i % 3 == 0 else '' for i in range(len(piv.index))],
        fontsize=7)
    ax.tick_params(axis='y', which='major', length=0)
    ax.set_title("Response matrix (white = completed, black = missed)")
    ax.grid(True, color=vs.GRID, linewidth=0.4)
    vs.panel_label(ax, "A", dx=-0.02)

    # B: completion by beep-of-day
    ax = fig.add_subplot(gs[1, 0])
    bb = ema.groupby("beep")["completed"].mean() * 100
    ax.bar(bb.index, bb.values, color=vs.NODE_COLORS["STRESS"], alpha=0.85)
    ax.set_ylim(50, 90)
    ax.set_xlabel("prompt of the day (1-4)")
    ax.set_ylabel("answered (%)")
    ax.set_title("Compliance by time of day")
    vs.bar_axes(ax, "vertical")
    vs.panel_label(ax, "B")

    # C: MNAR probe
    ax = fig.add_subplot(gs[1, 1])
    mn = mnar[mnar["term"] != "(Intercept)"].copy()
    mn["term"] = mn["term"].str.replace("scale\\(|\\)", "", regex=True)
    mn["lo"] = mn["estimate_logit"] - 1.96 * mn["SE"]
    mn["hi"] = mn["estimate_logit"] + 1.96 * mn["SE"]
    y = np.arange(len(mn))
    for i, r in mn.reset_index().iterrows():
        ax.plot([r["lo"], r["hi"]], [i, i], color=vs.MUTED, lw=2)
        ax.plot(r["estimate_logit"], i, "o", color=vs.NODE_COLORS["PIJN"], ms=7)
    ax.axvline(0, color=vs.INK, lw=0.9)
    ax.set_yticks(y); ax.set_yticklabels([vs.node_label(t) for t in mn["term"]])
    ax.set_xlabel("logit coefficient (95% CI)")
    ax.set_title("ENMO-missingness vs symptoms (all n.s.)")
    vs.panel_label(ax, "C")
    vs.savefig(fig, S / "SUP_04_missingness.png")


# SUP_05 - Missing-data imputation benchmark ---------------------------------
def sup_imputation():
    from matplotlib.patches import Patch
    comp = pd.read_csv(T / "04_imputation_comparison.csv")
    byvar = pd.read_csv(T / "04_imputation_by_variable.csv")
    ex = pd.read_csv(T / "04_imputation_example.csv")
    runs = pd.read_csv(T / "04_gap_runlengths.csv")
    fam_col = {"Univariate": vs.NODE_COLORS["ENMO"], "Multivariate": "#6f5b9e"}
    methods = comp["Method"].tolist()
    mcol = [fam_col[t] for t in comp["Type"]]
    yy = np.arange(len(methods))

    fig = plt.figure(figsize=(15.5, 9.6))
    gs = GridSpec(2, 3, figure=fig, hspace=0.55, wspace=0.40)

    # A: held-out reconstruction RMSE
    ax = fig.add_subplot(gs[0, 0])
    ax.barh(yy, comp["Std. RMSE"], color=mcol, alpha=0.9)
    ax.set_yticks(yy); ax.set_yticklabels(methods, fontsize=8); ax.invert_yaxis()
    ax.set_xlabel("held-out reconstruction RMSE (SD units)")
    ax.set_title("Reconstruction error (lower is better)")
    vs.bar_axes(ax, "horizontal")
    vs.add_cbar(fig, ax)
    vs.panel_label(ax, "A")

    # B: held-out within-person correlation
    ax = fig.add_subplot(gs[0, 1])
    ax.barh(yy, comp["r (held-out)"], color=mcol, alpha=0.9)
    ax.axvline(0, color=vs.INK, lw=0.9)
    ax.set_yticks(yy); ax.set_yticklabels(methods, fontsize=8); ax.invert_yaxis()
    ax.set_xlabel("held-out within-person correlation")
    ax.set_title("Momentary fidelity (higher is better)")
    ax.legend(handles=[Patch(color=fam_col["Univariate"], label="univariate (imputeTS)"),
                       Patch(color=fam_col["Multivariate"], label="multivariate")],
              fontsize=8, loc="lower right")
    vs.bar_axes(ax, "horizontal")
    vs.add_cbar(fig, ax)
    vs.panel_label(ax, "B")

    # C: reconstruction RMSE heatmap (method x measure)
    ax = fig.add_subplot(gs[0, 2])
    measures = ["Pain", "Fatigue", "Stress", "Activity"]
    mat = byvar.pivot(index="Method", columns="Measure", values="rmse").reindex(
        index=methods, columns=measures)
    im = ax.imshow(mat.values, cmap="PuBu", aspect="auto")
    ax.set_xticks(range(4)); ax.set_xticklabels(measures, rotation=20, ha="right")
    ax.set_yticks(yy); ax.set_yticklabels(methods, fontsize=8)
    thr = np.nanmean(mat.values)
    for i in range(len(methods)):
        for j in range(4):
            ax.text(j, i, f"{mat.values[i, j]:.2f}", ha="center", va="center", fontsize=7,
                    color=vs.INK if mat.values[i, j] < thr else "white")
    ax.set_title("Reconstruction RMSE by measure")
    vs.matrix_axes(ax)
    vs.add_cbar(fig, ax, im)
    vs.panel_label(ax, "C")

    # D: illustrative reconstruction of an induced gap in one activity series
    ax = fig.add_subplot(gs[1, 0])
    obs = ex["obs"].to_numpy(); yt = ex["y_true"].to_numpy()
    mask = ex["is_masked"].to_numpy().astype(bool)
    valid = (~mask) & np.isfinite(yt)
    ax.axvspan(obs[mask].min() - 0.5, obs[mask].max() + 0.5, color=vs.GRID, alpha=0.5, zorder=0)
    ax.plot(obs[valid], yt[valid], "-o", color=vs.MUTED, ms=3, lw=1, label="observed")
    ax.scatter(obs[mask], yt[mask], color=vs.INK, s=34, zorder=6, label="held-out truth")
    show = {"mean": ("Mean", vs.NODE_COLORS["MOE"]),
            "linear": ("Linear", vs.NODE_COLORS["EIGENEFF"]),
            "kalman": ("Kalman", vs.NODE_COLORS["ENMO"]),
            "mice": ("MICE", "#6f5b9e")}
    for k, (lab, c) in show.items():
        ax.plot(obs[mask], ex[k].to_numpy()[mask], "D--", color=c, ms=5, lw=1, label=lab)
    ax.set_xlim(obs[mask].min() - 8, obs[mask].max() + 8)
    ax.set_xlabel("observation (prompt index)"); ax.set_ylabel("log activity")
    ax.set_title("Reconstruction of an induced gap (one series)")
    ax.legend(fontsize=7, ncol=2)
    vs.add_cbar(fig, ax)
    vs.panel_label(ax, "D")

    # E: moment stability
    ax = fig.add_subplot(gs[1, 1])
    w = 0.38; xx = np.arange(len(methods))
    ax.bar(xx - w / 2, comp["Mean shift (SD)"] * 100, w, color=vs.MUTED, alpha=0.9,
           label="mean shift (% of SD)")
    ax.bar(xx + w / 2, comp["SD change (%)"], w, color=vs.NODE_COLORS["PIJN"], alpha=0.8,
           label="SD change (%)")
    ax.set_xticks(xx); ax.set_xticklabels(methods, rotation=40, ha="right", fontsize=7)
    ax.set_ylabel("% change vs available-case")
    ax.set_title("Imputing every gap barely moves the moments")
    ax.legend(fontsize=8)
    vs.bar_axes(ax, "vertical")
    vs.add_cbar(fig, ax)
    vs.panel_label(ax, "E")

    # F: gap run-length structure by measure
    ax = fig.add_subplot(gs[1, 2])
    def bucket(rl):
        return "1" if rl == 1 else ("2" if rl == 2 else ("3-4" if rl <= 4 else "5+"))
    runs["bucket"] = runs["run_length"].map(bucket)
    order_b = ["1", "2", "3-4", "5+"]
    palette = [vs.NODE_COLORS["ENMO"], vs.NODE_COLORS["EIGENEFF"],
               vs.NODE_COLORS["MOE"], vs.NODE_COLORS["PIJN"]]
    bottom = np.zeros(len(measures))
    for bi, bk in enumerate(order_b):
        vals = []
        for m in measures:
            tot = runs[runs["Measure"] == m]["count"].sum()
            c = runs[(runs["Measure"] == m) & (runs["bucket"] == bk)]["count"].sum()
            vals.append(100 * c / tot if tot else 0)
        ax.bar(measures, vals, bottom=bottom, color=palette[bi], label=f"run {bk}")
        bottom += np.array(vals)
    ax.set_ylabel("% of missing runs"); ax.set_ylim(0, 100)
    ax.set_title("Most missing runs are short")
    ax.legend(fontsize=8, ncol=2)
    vs.bar_axes(ax, "vertical")
    vs.add_cbar(fig, ax)
    vs.panel_label(ax, "F")

    vs.savefig(fig, S / "SUP_05_imputation.png")


# SUP_06 - Idiographic feasibility (graphicalVAR + per-person OLS) -------------
def sup_03():
    summ = pd.read_csv(T / "07_graphicalvar_individual_summary.csv")
    freq = pd.read_csv(N / "07_graphicalvar_edge_selection_freq.csv")
    edges = pd.read_csv(N / "07_perperson_var_ols_edges.csv")
    fitted = summ[summ["fitted"]].copy()

    fig = plt.figure(figsize=(15, 9))
    gs = GridSpec(2, 3, figure=fig, hspace=0.42, wspace=0.34)

    # A: histogram of #temporal edges selected per person
    ax = fig.add_subplot(gs[0, 0])
    ax.hist(fitted["n_temporal_edges"], bins=np.arange(-0.5, 11, 1),
            color=vs.NODE_COLORS["ENMO"], alpha=0.85)
    ax.axvline(fitted["n_temporal_edges"].median(), color=vs.INK, ls="--", lw=1.2)
    ax.set_xlabel("temporal edges selected (of 16 possible)")
    ax.set_ylabel("participants")
    ax.set_title(f"graphicalVAR selects few edges\n(median {fitted['n_temporal_edges'].median():.0f})")
    vs.bar_axes(ax, "none")
    vs.add_cbar(fig, ax)
    vs.panel_label(ax, "A")

    # B: edge-selection frequency heatmap
    ax = fig.add_subplot(gs[0, 1])
    mat = freq.pivot(index="from", columns="to", values="pct_selected").reindex(
        index=NODES, columns=NODES)
    im = ax.imshow(mat.values, cmap="PuBu", vmin=0, vmax=max(40, mat.values.max()))
    ax.set_xticks(range(4)); ax.set_xticklabels([vs.node_label(n) for n in NODES],
                                                rotation=30, ha="right", fontsize=8)
    ax.set_yticks(range(4)); ax.set_yticklabels([vs.node_label(n) for n in NODES],
                                                fontsize=8)
    for i in range(4):
        for j in range(4):
            ax.text(j, i, f"{mat.values[i,j]:.0f}", ha="center", va="center",
                    fontsize=8, color=vs.INK)
    ax.set_xlabel("to"); ax.set_ylabel("from")
    ax.set_title("% of persons with each\ntemporal edge selected")
    vs.matrix_axes(ax)
    vs.add_cbar(fig, ax, im)
    vs.panel_label(ax, "B")

    # C: per-person Pain->Activity OLS coefficient sorted
    ax = fig.add_subplot(gs[0, 2])
    pa = edges[edges["edge"] == "PIJN__to__ENMO_log"].sort_values("coef").reset_index()
    cols = [vs.EDGE_NEG if c < 0 else vs.EDGE_POS for c in pa["coef"]]
    ax.bar(range(len(pa)), pa["coef"], color=cols, alpha=0.5)
    sigmask = pa["p"] < 0.05
    ax.bar(np.arange(len(pa))[sigmask], pa["coef"][sigmask],
           color=[vs.EDGE_NEG if c < 0 else vs.EDGE_POS for c in pa["coef"][sigmask]],
           alpha=1.0)
    ax.axhline(0, color=vs.INK, lw=0.9)
    ax.set_xlabel("participant (sorted)")
    ax.set_ylabel("Pain -> Activity coefficient")
    ax.set_title(f"Heterogeneous Pain -> Activity\n({int(sigmask.sum())} of {len(pa)} individually p<.05)")
    vs.bar_axes(ax, "none")
    vs.add_cbar(fig, ax)
    vs.panel_label(ax, "C")

    # D: edges recovered vs series length (feasibility scales with T)
    ax = fig.add_subplot(gs[1, 0])
    ax.scatter(fitted["n_complete"], fitted["n_temporal_edges"], s=46,
               color=vs.NODE_COLORS["ENMO"], edgecolor="white", linewidth=0.5,
               alpha=0.8, zorder=3)
    ax.axvspan(100, 125, color=vs.NODE_COLORS["PIJN"], alpha=0.08, zorder=0)
    ax.axvline(100, color=vs.NODE_COLORS["PIJN"], ls="--", lw=1, zorder=1)
    ax.text(99, fitted["n_temporal_edges"].max(), "recommended\nseries length",
            ha="right", va="top", fontsize=8, color=vs.NODE_COLORS["PIJN"])
    ax.set_xlim(20, 125)
    ax.set_xlabel("complete prompts per person")
    ax.set_ylabel("temporal edges selected")
    ax.set_title("Recoverable structure scales with series length")
    vs.add_cbar(fig, ax)
    vs.panel_label(ax, "D")

    # E: contemporaneous vs temporal edges per person (contemporaneous easier)
    ax = fig.add_subplot(gs[1, 1])
    rng = np.random.default_rng(11)
    jx = rng.uniform(-0.12, 0.12, len(fitted))
    jy = rng.uniform(-0.12, 0.12, len(fitted))
    ax.scatter(fitted["n_temporal_edges"] + jx, fitted["n_contemp_edges"] + jy, s=46,
               color=vs.NODE_COLORS["STRESS"], edgecolor="white", linewidth=0.5,
               alpha=0.8, zorder=3)
    mx = float(max(fitted["n_temporal_edges"].max(), fitted["n_contemp_edges"].max())) + 0.5
    ax.plot([0, mx], [0, mx], color=vs.MUTED, ls="--", lw=1, zorder=1)
    ax.set_xlim(-0.5, mx); ax.set_ylim(-0.5, mx)
    ax.set_xlabel("temporal edges selected")
    ax.set_ylabel("contemporaneous edges selected")
    ax.set_title("Contemporaneous structure is easier to recover")
    vs.add_cbar(fig, ax)
    vs.panel_label(ax, "E")

    # F: individually significant unregularized cross-lagged edges per person
    ax = fig.add_subplot(gs[1, 2])
    cross = edges[edges["from"] != edges["to"]]
    sig = cross[cross["p"] < 0.05].groupby("pid").size()
    counts = pd.Series(0, index=sorted(edges["pid"].unique()))
    counts.update(sig)
    ax.hist(counts.values, bins=np.arange(-0.5, counts.max() + 1.5, 1),
            color=vs.NODE_COLORS["MOE"], alpha=0.85)
    ax.axvline(counts.mean(), color=vs.INK, ls="--", lw=1.2)
    ax.set_xlabel("significant cross-lagged edges (of 12)")
    ax.set_ylabel("participants")
    ax.set_title(f"Few individual edges reach significance\n(mean {counts.mean():.1f} per person)")
    vs.bar_axes(ax, "none")
    vs.add_cbar(fig, ax)
    vs.panel_label(ax, "F")
    vs.savefig(fig, S / "SUP_06_idiographic_feasibility.png")


# SUP_07 - S-GIMME ------------------------------------------------------------
def sup_04():
    from matplotlib.patches import Patch

    memb = pd.read_csv(T / "06_sgimme_subgroup_membership.csv")
    incl = pd.read_csv(T / "06_sgimme_inclusion.csv")
    spc = pd.read_csv(N / "06_sgimme_summary_path_counts.csv")
    ind = pd.read_csv(N / "06_sgimme_individual_path_estimates.csv")
    subgroups = sorted(memb["subgroup"].dropna().astype(int).unique())
    cmap = plt.get_cmap("tab20", max(len(subgroups), 1))
    subgroup_colors = {sg: cmap(i) for i, sg in enumerate(subgroups)}
    fig = plt.figure(figsize=(14.5, 12.2))
    gs = GridSpec(3, 2, figure=fig, hspace=0.46, wspace=0.32,
                  width_ratios=[1.0, 1.35])

    def _sgimme_path_label(lhs, rhs):
        lab = {"PIJN": "Pain", "MOE": "Fatigue", "STRESS": "Stress",
               "ENMO_log": "Activity"}
        lag = str(rhs).endswith("lag")
        source = str(rhs)[:-3] if lag else str(rhs)
        suffix = " (t-1)" if lag else ""
        return f"{lab.get(source, source)}{suffix} -> {lab.get(lhs, lhs)}"

    def _path_string_label(path):
        lhs, rhs = path.split(" ~ ")
        return _sgimme_path_label(lhs, rhs)

    ax = fig.add_subplot(gs[0, 0])
    sizes = memb["subgroup"].value_counts().sort_index()
    colors = [subgroup_colors[int(s)] for s in sizes.index]
    ax.bar(sizes.index.astype(str), sizes.values, color=colors, alpha=0.9)
    ax.set_xlabel("S-GIMME subgroup")
    ax.set_ylabel("participants")
    ax.set_title(f"Data-driven subgroups: 2 small groups + {int((sizes==1).sum())} singletons")
    vs.bar_axes(ax, "vertical")
    vs.panel_label(ax, "A")

    ax = fig.add_subplot(gs[0, 1])
    q = incl.merge(memb[["pid", "subgroup"]], on="pid", how="left")
    q = q.sort_values(["included", "subgroup", "n_complete"],
                      ascending=[False, True, True]).reset_index(drop=True)
    bar_cols = [
        subgroup_colors.get(int(s), vs.MUTED) if inc else vs.MUTED
        for s, inc in zip(q["subgroup"].fillna(0), q["included"])
    ]
    ax.bar(np.arange(len(q)), q["n_complete"], color=bar_cols, alpha=0.88)
    ax.axhline(30, color=vs.INK, lw=1, ls="--")
    ax.text(len(q) - 0.5, 31, "gimme threshold", ha="right", fontsize=8, color=vs.INK)
    ax.set_xticks(np.arange(len(q)))
    ax.set_xticklabels(q["pid"], rotation=90, fontsize=7)
    ax.set_ylabel("complete prompts")
    ax.set_title("Included series meet the minimum length but remain short")
    vs.bar_axes(ax, "vertical")
    vs.panel_label(ax, "B")

    ax = fig.add_subplot(gs[1, 0])
    cross = spc[spc["count.group"] == 0].copy()
    cross = cross.sort_values("count.ind", ascending=True).tail(10)
    lab = [_sgimme_path_label(r["lhs"], r["rhs"]) for _, r in cross.iterrows()]
    y = np.arange(len(cross))
    ax.barh(y, cross["count.ind"], color=vs.NODE_COLORS["MOE"], alpha=0.9)
    ax.set_yticks(y); ax.set_yticklabels(lab, fontsize=8)
    ax.set_xlabel("number of individuals with this path")
    ax.set_title("Individual-level paths (no path reached the group threshold)")
    vs.bar_axes(ax, "horizontal")
    vs.panel_label(ax, "C")

    ax = fig.add_subplot(gs[1, 1])
    ind["path"] = ind["lhs"] + " ~ " + ind["rhs"]
    keep_paths = (
        ind[ind["level"].isin(["ind", "sub"])]
        .groupby("path")["file"].nunique()
        .sort_values(ascending=False)
        .head(12)
        .index.tolist()
    )
    hm = (
        ind[ind["path"].isin(keep_paths)]
        .assign(present=1)
        .pivot_table(index="file", columns="path", values="present", aggfunc="max", fill_value=0)
    )
    order = memb.sort_values(["subgroup", "pid"])["pid"].tolist()
    hm = hm.reindex(index=[p for p in order if p in hm.index], columns=keep_paths).fillna(0)
    im = ax.imshow(hm.values, aspect="auto", interpolation="nearest",
                   cmap="PuBu", vmin=0, vmax=1)
    xlab = [_path_string_label(p) for p in hm.columns]
    ax.set_xticks(np.arange(len(xlab)))
    ax.set_xticklabels(xlab, rotation=45, ha="right", fontsize=7)
    ax.set_yticks(np.arange(len(hm.index)))
    ax.set_yticklabels([])  # gridline per participant row, no labels
    ax.set_title("Individual and subgroup path presence")
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(axis='both', which='both', length=0)
    ax.grid(True, color=vs.GRID, linewidth=0.4)
    fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02, ticks=[0, 1])
    vs.panel_label(ax, "D")

    ind = ind.copy()
    ind["path"] = ind["lhs"] + " ~ " + ind["rhs"]

    def _plot_subgroup_paths(ax, sg, letter):
        members = memb.loc[memb["subgroup"] == sg, "pid"].tolist()
        d = ind[ind["file"].isin(members) & ind["level"].isin(["sub", "ind"])].copy()
        rows = []
        for level, label in [("sub", "shared subgroup"), ("ind", "individual-only")]:
            g = (
                d[d["level"] == level]
                .groupby(["lhs", "rhs", "path"], as_index=False)
                .agg(n=("file", "nunique"), mean_beta=("beta.std", "mean"))
            )
            for _, r in g.iterrows():
                rows.append({
                    "path": r["path"],
                    "label": _sgimme_path_label(r["lhs"], r["rhs"]),
                    "n": int(r["n"]),
                    "pct": 100 * float(r["n"]) / len(members),
                    "mean_beta": float(r["mean_beta"]),
                    "level": label,
                    "shared": level == "sub",
                })
        if not rows:
            ax.text(0.5, 0.5, "no subgroup or individual paths selected",
                    transform=ax.transAxes, ha="center", va="center", fontsize=9)
            ax.set_axis_off()
            vs.panel_label(ax, letter)
            return
        prev = pd.DataFrame(rows)
        shared = prev[prev["shared"]]
        indiv = prev[~prev["shared"]].sort_values(["n", "pct"], ascending=False).head(7)
        plot = pd.concat([shared, indiv], ignore_index=True)
        plot = plot.sort_values(["shared", "pct"], ascending=[True, True]).reset_index(drop=True)
        y = np.arange(len(plot))
        colors = [
            subgroup_colors[sg] if r["shared"]
            else (vs.EDGE_POS if r["mean_beta"] >= 0 else vs.EDGE_NEG)
            for _, r in plot.iterrows()
        ]
        alpha = [0.95 if r["shared"] else 0.58 for _, r in plot.iterrows()]
        bars = ax.barh(y, plot["pct"], color=colors)
        for bar, a in zip(bars, alpha):
            bar.set_alpha(a)
        labels = [f"{r['label']} ({r['n']}/{len(members)})" for _, r in plot.iterrows()]
        ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=7.5)
        ax.set_xlim(0, 100)
        ax.set_xlabel("% subgroup members")
        ax.set_title(f"Subgroup {sg} path prevalence (n={len(members)})")
        if not bool(shared.shape[0]):
            ax.text(0.98, 0.92, "no shared subgroup path", transform=ax.transAxes,
                    ha="right", va="top", fontsize=8, color=vs.MUTED)
        ax.legend(
            handles=[
                Patch(facecolor=subgroup_colors[sg], label="shared subgroup"),
                Patch(facecolor=vs.EDGE_POS, alpha=0.58, label="individual-only, positive"),
                Patch(facecolor=vs.EDGE_NEG, alpha=0.58, label="individual-only, negative"),
            ],
            fontsize=7, loc="lower right"
        )
        vs.bar_axes(ax, "horizontal")
        vs.panel_label(ax, letter)

    multiperson = sizes[sizes > 1].sort_index().index.astype(int).tolist()
    for ax, sg, letter in zip([fig.add_subplot(gs[2, 0]), fig.add_subplot(gs[2, 1])],
                              multiperson[:2], ["E", "F"]):
        _plot_subgroup_paths(ax, sg, letter)
    vs.savefig(fig, S / "SUP_07_sgimme.png")


# SUP_08 - Extended 6-node and 7-node networks --------------------------------
def sup_05():
    temp = pd.read_csv(N / "extended_mlvar_temporal_edges.csv")
    con = pd.read_csv(N / "extended_mlvar_contemporaneous_edges.csv")
    temp7 = pd.read_csv(N / "extended7_mlvar_temporal_edges.csv")
    con7 = pd.read_csv(N / "extended7_mlvar_contemporaneous_edges.csv")
    nodes6 = ["PIJN", "MOE", "STRESS", "ENMO_log", "EIGENEFF", "INTENTIE"]
    nodes7 = ["PIJN", "MOE", "STRESS", "ENMO_log", "EIGENEFF", "INTENTIE", "UITKOMSTVERW"]

    def temp_edges(df):
        return [{"from": r["from"], "to": r["to"], "weight": r["weight"], "P": r["P"]}
                for _, r in df.iterrows()]

    def con_edges(df):
        return [{"node1": r["node1"], "node2": r["node2"], "weight": r["pcor"], "P": r["P"]}
                for _, r in df.iterrows()]

    wref6 = max(max(abs(temp["weight"])), max(abs(con["pcor"])))
    wref7 = max(max(abs(temp7["weight"])), max(abs(con7["pcor"])))
    fig = plt.figure(figsize=(12.6, 11))
    gs = GridSpec(2, 2, figure=fig, hspace=0.10, wspace=0.00)
    ax = fig.add_subplot(gs[0, 0])
    netviz.draw_network(ax, nodes6, temp_edges(temp), directed=True, weight_ref=wref6,
                        title="Six-node temporal (lag-1)", node_radius=0.27,
                        label_fontsize=8)
    ax.set_xlim(-1.66, 1.66); ax.set_ylim(-1.66, 1.66)
    vs.panel_label(ax, "A", dx=0.02, dy=1.02)
    ax = fig.add_subplot(gs[0, 1])
    netviz.draw_network(ax, nodes6, con_edges(con), directed=False, weight_ref=wref6,
                        title="Six-node contemporaneous", node_radius=0.27,
                        label_fontsize=8)
    ax.set_xlim(-1.30, 1.30); ax.set_ylim(-1.30, 1.30)
    vs.panel_label(ax, "B", dx=0.02, dy=1.02)
    ax = fig.add_subplot(gs[1, 0])
    netviz.draw_network(ax, nodes7, temp_edges(temp7), directed=True, weight_ref=wref7,
                        title="Seven-node temporal (lag-1)", node_radius=0.24,
                        label_fontsize=7)
    ax.set_xlim(-1.58, 1.58); ax.set_ylim(-1.58, 1.58)
    vs.panel_label(ax, "C", dx=0.02, dy=1.02)
    ax = fig.add_subplot(gs[1, 1])
    netviz.draw_network(ax, nodes7, con_edges(con7), directed=False, weight_ref=wref7,
                        title="Seven-node contemporaneous", node_radius=0.24,
                        label_fontsize=7)
    ax.set_xlim(-1.28, 1.28); ax.set_ylim(-1.28, 1.28)
    vs.panel_label(ax, "D", dx=0.02, dy=1.02)
    vs.savefig(fig, S / "SUP_08_extended_network.png")


# SUP_09 - Could-not-move sensitivity -----------------------------------------
def sup_06():
    cmp = pd.read_csv(N / "cantmove_edge_comparison.csv")

    fig = plt.figure(figsize=(13.4, 8.4))
    gs = GridSpec(2, 2, figure=fig, hspace=0.30, wspace=0.20)

    ax = fig.add_subplot(gs[0, 0])
    mv = (
        ema.dropna(subset=["MOGELIJKHEID_BEW"])
        .groupby("pid")
        .agg(n=("MOGELIJKHEID_BEW", "size"),
             pct_impossible=("MOGELIJKHEID_BEW", lambda s: 100 * (s == 0).mean()))
        .sort_values("pct_impossible")
        .reset_index()
    )
    ax.bar(np.arange(len(mv)), mv["pct_impossible"], color=vs.MUTED, alpha=0.85)
    ax.axhline(mv["pct_impossible"].mean(), color=vs.INK, ls="--", lw=1)
    ax.set_xticks(np.arange(0, len(mv), 3))
    ax.set_xticklabels(mv["pid"].iloc[::3], rotation=90, fontsize=7)
    ax.set_ylabel("movement-impossible prompts (%)")
    ax.set_xlabel("participant (sorted)")
    ax.set_title("Movement opportunity varies across participants")
    vs.bar_axes(ax, "vertical")
    vs.add_cbar(fig, ax, pad=0.06)
    vs.panel_label(ax, "A")

    ax = fig.add_subplot(gs[0, 1])
    cols = [vs.EDGE_POS if w >= 0 else vs.EDGE_NEG for w in cmp["weight_all"]]
    ax.scatter(cmp["weight_all"], cmp["weight_movement"], s=60, color=cols,
               edgecolor="white", linewidth=0.6, zorder=3)
    lim = [min(cmp[["weight_all", "weight_movement"]].min()) - 0.05,
           max(cmp[["weight_all", "weight_movement"]].max()) + 0.05]
    ax.plot(lim, lim, color=vs.MUTED, ls="--", lw=1)
    ax.set_xlim(lim); ax.set_ylim(lim)
    r = np.corrcoef(cmp["weight_all"], cmp["weight_movement"])[0, 1]
    ax.set_xlabel("temporal coefficient - all prompts")
    ax.set_ylabel("temporal coefficient - movement-possible only")
    ax.set_title(f"Primary vs movement-possible network (r = {r:.3f})")
    vs.add_cbar(fig, ax, pad=0.06)
    vs.panel_label(ax, "B")

    ax = fig.add_subplot(gs[1, 0])
    top = cmp.sort_values("abs_diff", ascending=True).tail(10).copy()
    lab = [
        _nice_edge(f"{f}__to__{t}")
        for f, t in zip(top["from"], top["to"])
    ]
    y = np.arange(len(top))
    ax.barh(y, top["abs_diff"], color=vs.NODE_COLORS["ENMO"], alpha=0.9)
    ax.set_yticks(y); ax.set_yticklabels(lab, fontsize=8)
    ax.set_xlabel("absolute coefficient difference")
    ax.set_title("Largest coefficient changes after exclusion")
    vs.bar_axes(ax, "horizontal")
    vs.add_cbar(fig, ax, pad=0.06)
    vs.panel_label(ax, "C")

    ax = fig.add_subplot(gs[1, 1])
    diff = cmp.assign(delta=cmp["weight_movement"] - cmp["weight_all"]).pivot(
        index="from", columns="to", values="delta"
    ).reindex(index=NODES, columns=NODES)
    vmax = max(abs(diff.min().min()), abs(diff.max().max()))
    im = ax.imshow(diff.values, cmap="RdBu_r", vmin=-vmax, vmax=vmax)
    ax.set_xticks(range(4)); ax.set_xticklabels([vs.node_label(n) for n in NODES],
                                                rotation=30, ha="right")
    ax.set_yticks(range(4)); ax.set_yticklabels([vs.node_label(n) for n in NODES])
    for i in range(4):
        for j in range(4):
            val = diff.values[i, j]
            ax.text(j, i, f"{val:+.2f}", ha="center", va="center",
                    fontsize=8, color=vs.INK if abs(val) < vmax * 0.65 else "white")
    ax.set_xlabel("to"); ax.set_ylabel("from")
    ax.set_title("Coefficient differences by directed path")
    ax.set_anchor("W")
    vs.matrix_axes(ax)
    vs.add_cbar(fig, ax, im, pad=0.06)
    vs.panel_label(ax, "D")

    vs.savefig(fig, S / "SUP_09_cantmove_sensitivity.png")


# SUP_10 - Pacing -------------------------------------------------------------
def sup_07():
    onsym = pd.read_csv(T / "pacing_on_symptoms.csv")
    rng = np.random.default_rng(1209)
    pac_items = ["SPEED", "PIECES", "BREAKS"]
    paclab = ["Slowing", "Chunking", "Extra breaks"]
    sym_items = ["PIJN", "MOE", "STRESS"]
    symlab = [vs.node_label(v) for v in sym_items]

    dat = ema.copy()
    dat["PACING"] = dat[pac_items].mean(axis=1, skipna=True)
    dat.loc[dat[pac_items].isna().all(axis=1), "PACING"] = np.nan
    for v in sym_items + ["PACING"]:
        dat[f"c{v}"] = dat[v] - dat.groupby("pid")[v].transform("mean")

    def _gee_gaussian(formula, data):
        return smf.gee(
            formula,
            groups="pid",
            data=data,
            family=sm.families.Gaussian(),
            cov_struct=sm.cov_struct.Exchangeable(),
        ).fit()

    def _fmt_num(x):
        return f"{x:.3f}".replace("0.", ".").replace("-0.", "-.")

    def _fmt_p(p):
        if pd.isna(p):
            return "p = NA"
        if p < .001:
            return "p < .001"
        return f"p = {_fmt_num(p)}"

    fig = plt.figure(figsize=(15, 12))
    gs = GridSpec(3, 2, figure=fig, hspace=0.50, wspace=0.28)

    ax = fig.add_subplot(gs[0, 0])
    for i, v in enumerate(pac_items):
        vals = ema[v].dropna()
        h, _ = np.histogram(vals, bins=np.arange(-0.5, 11.5, 1), density=True)
        ax.plot(np.arange(0, 11), h, "-o", lw=1.8, ms=4, label=paclab[i],
                color=vs.CLUSTER_COLORS[i])
    ax.set_xlabel("momentary pacing rating (0-10)")
    ax.set_ylabel("density")
    ax.set_title("Distribution of momentary pacing behaviours")
    ax.legend(fontsize=8)
    vs.panel_label(ax, "A")

    ax = fig.add_subplot(gs[0, 1])
    mn = onsym[onsym["term"] != "(Intercept)"].copy()
    mn["term_raw"] = mn["term"]
    mn["term"] = mn["term"].str.replace("c", "", regex=False)
    mn = mn.set_index("term").loc[sym_items].reset_index()
    mn["lo"] = mn["estimate"] - 1.96 * mn["SE"]
    mn["hi"] = mn["estimate"] + 1.96 * mn["SE"]
    y = np.arange(len(mn))
    for i, r in mn.reset_index().iterrows():
        sig = r["p"] < 0.05
        col = vs.EDGE_POS if r["estimate"] >= 0 else vs.EDGE_NEG
        ax.plot([r["lo"], r["hi"]], [i, i], color=col, lw=2.4 if sig else 1.3,
                alpha=0.95 if sig else 0.5)
        ax.plot(r["estimate"], i, "o", color=col, ms=8 if sig else 5)
    ax.axvline(0, color=vs.INK, lw=0.9)
    ax.set_yticks(y)
    ax.set_yticklabels([vs.node_label(t.upper()) if t.upper() in vs.NODE_LABELS else t
                        for t in mn["term"]])
    ax.set_xlabel("within-person effect on pacing (95% CI)")
    ax.set_title("Composite pacing: symptom associations")
    vs.panel_label(ax, "B")

    ax = fig.add_subplot(gs[1, 0])
    item_rows = []
    for outcome in pac_items:
        fitdat = dat[["pid", outcome, "cPIJN", "cMOE", "cSTRESS"]].dropna()
        fit = _gee_gaussian(f"{outcome} ~ cPIJN + cMOE + cSTRESS", fitdat)
        for pred in ["cPIJN", "cMOE", "cSTRESS"]:
            item_rows.append({
                "outcome": outcome,
                "predictor": pred,
                "estimate": fit.params[pred],
                "p": fit.pvalues[pred],
            })
    item = pd.DataFrame(item_rows)
    est = item.pivot(index="outcome", columns="predictor", values="estimate").loc[
        pac_items, ["cPIJN", "cMOE", "cSTRESS"]
    ]
    pmat = item.pivot(index="outcome", columns="predictor", values="p").loc[
        pac_items, ["cPIJN", "cMOE", "cSTRESS"]
    ]
    vmax = float(np.nanmax(np.abs(est.values)))
    im = ax.imshow(est.values, cmap="RdBu_r", vmin=-vmax, vmax=vmax)
    ax.set_xticks(range(3)); ax.set_xticklabels(symlab)
    ax.set_yticks(range(3)); ax.set_yticklabels(paclab)
    for i in range(3):
        for j in range(3):
            val = est.values[i, j]
            p = pmat.values[i, j]
            ax.text(j, i, f"{val:+.2f}{_p_label(p)}", ha="center", va="center",
                    fontsize=8, color=vs.INK if abs(val) < vmax * 0.62 else "white")
    ax.set_title("Item-specific symptom associations")
    vs.matrix_axes(ax)
    vs.add_cbar(fig, ax, im, pad=0.06, label="GEE coefficient")
    vs.panel_label(ax, "C")

    ax = fig.add_subplot(gs[1, 1])
    move = dat[["pid", "MOGELIJKHEID_BEW", "PIJN", "MOE", "STRESS",
                "cPIJN", "cMOE", "cSTRESS"]].dropna(subset=["MOGELIJKHEID_BEW"]).copy()
    move["MOVE_IMPOSSIBLE"] = 1 - move["MOGELIJKHEID_BEW"].astype(float)
    move_fit = smf.gee(
        "MOVE_IMPOSSIBLE ~ cPIJN + cMOE + cSTRESS",
        groups="pid",
        data=move.dropna(subset=["cPIJN", "cMOE", "cSTRESS"]),
        family=sm.families.Binomial(),
        cov_struct=sm.cov_struct.Exchangeable(),
    ).fit()
    tertile_labels = ["low", "middle", "high"]
    xs = np.arange(3)
    for i, (sym, lab) in enumerate(zip(sym_items, symlab)):
        d = move.dropna(subset=[sym]).copy()
        d["symptom_tertile"] = pd.qcut(
            d[sym].rank(method="first"), 3, labels=tertile_labels
        )
        rates = d.groupby("symptom_tertile", observed=True)["MOVE_IMPOSSIBLE"].mean()
        rates = rates.reindex(tertile_labels) * 100
        p = move_fit.pvalues.get(f"c{sym}", np.nan)
        ax.plot(xs, rates.values, "-o", lw=2, ms=5, color=vs.NODE_COLORS[sym],
                label=f"{lab} ({_fmt_p(p)})")
    ax.set_xticks(xs); ax.set_xticklabels(["low", "middle", "high"])
    ax.set_ylabel("movement-impossible prompts (%)")
    ax.set_xlabel("symptom tertile")
    ax.set_title("Movement opportunity across symptom levels")
    ax.legend(fontsize=8, loc="upper left")
    vs.panel_label(ax, "D")

    ax = fig.add_subplot(gs[2, 0])
    cmpdat = dat[["pid", "PACING", "MOGELIJKHEID_BEW"]].dropna()
    move_pacing_fit = _gee_gaussian("PACING ~ MOGELIJKHEID_BEW", cmpdat)
    pos = [0, 1]
    values = [
        cmpdat.loc[cmpdat["MOGELIJKHEID_BEW"] == 0, "PACING"],
        cmpdat.loc[cmpdat["MOGELIJKHEID_BEW"] == 1, "PACING"],
    ]
    _violin_scatter_pair(
        ax, values, pos, [vs.CLUSTER_COLORS[1], vs.CLUSTER_COLORS[0]], rng,
        width=0.70, point_size=9, alpha=0.12
    )
    ax.set_xticks(pos); ax.set_xticklabels(["Unable", "Able"])
    ax.set_ylabel("composite pacing (0-10)")
    ax.set_title("Pacing by movement opportunity")
    ymax = max([pd.Series(v).max() for v in values if len(v)]) + 0.7
    _sig_bar(ax, 0, 1, ymax, move_pacing_fit.pvalues.get("MOGELIJKHEID_BEW", np.nan),
             h=0.25)
    ax.set_ylim(-0.4, ymax + 0.65)
    vs.panel_label(ax, "E")

    ax = fig.add_subplot(gs[2, 1])
    act = dat[["pid", "PACING", "cPACING", "ENMO_log"]].dropna().copy()
    act["pacing_tertile"] = pd.qcut(
        act["PACING"].rank(method="first"), 3, labels=tertile_labels
    )
    act_fit = _gee_gaussian("ENMO_log ~ cPACING", act)
    act_vals = [
        act.loc[act["pacing_tertile"] == lab, "ENMO_log"] for lab in tertile_labels
    ]
    _violin_scatter_pair(
        ax, act_vals, xs, [vs.CLUSTER_COLORS[0], vs.CLUSTER_COLORS[3], vs.CLUSTER_COLORS[2]],
        rng, width=0.70, point_size=8, alpha=0.10
    )
    ax.set_xticks(xs); ax.set_xticklabels(["low", "middle", "high"])
    ax.set_xlabel("composite pacing tertile")
    ax.set_ylabel("log activity")
    ax.set_title("Objective activity across pacing tertiles")
    b = act_fit.params.get("cPACING", np.nan)
    p = act_fit.pvalues.get("cPACING", np.nan)
    ax.text(0.02, 0.96, f"within-person slope b = {_fmt_num(b)}, {_fmt_p(p)}",
            transform=ax.transAxes, ha="left", va="top", fontsize=8,
            bbox=dict(boxstyle="round,pad=0.25", facecolor="white",
                      edgecolor=vs.GRID, alpha=0.92))
    vs.panel_label(ax, "F")
    vs.savefig(fig, S / "SUP_10_pacing.png")


# SUP_11 - within vs between correlations -------------------------------------
def sup_08():
    wi = pd.read_csv(T / "02_within_person_corr.csv", index_col=0)
    bw = pd.read_csv(T / "02_between_person_corr.csv", index_col=0)
    fig = plt.figure(figsize=(13.4, 9))
    gs = GridSpec(2, 2, figure=fig, hspace=0.32, wspace=0.18)
    axes = [fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])]
    for ax, mat, ttl, lett in [(axes[0], wi, "Within-person correlations", "A"),
                               (axes[1], bw, "Between-person correlations", "B")]:
        m = mat.reindex(index=NODES, columns=NODES)
        im = ax.imshow(m.values, cmap="RdBu_r", vmin=-1, vmax=1)
        ax.set_xticks(range(4)); ax.set_xticklabels([vs.node_label(n) for n in NODES],
                                                    rotation=30, ha="right")
        ax.set_yticks(range(4)); ax.set_yticklabels([vs.node_label(n) for n in NODES])
        for i in range(4):
            for j in range(4):
                ax.text(j, i, f"{m.values[i,j]:.2f}", ha="center", va="center",
                        fontsize=9, color=vs.INK if abs(m.values[i, j]) < 0.6 else "white")
        ax.set_title(ttl)
        vs.matrix_axes(ax)
        vs.add_cbar(fig, ax, im, pad=0.06)
        vs.panel_label(ax, lett)

    ax_diff = fig.add_subplot(gs[1, 0])
    wm = wi.reindex(index=NODES, columns=NODES)
    bm = bw.reindex(index=NODES, columns=NODES)
    dm = bm - wm
    im2 = ax_diff.imshow(dm.values, cmap="RdBu_r", vmin=-1, vmax=1)
    ax_diff.set_xticks(range(4)); ax_diff.set_xticklabels([vs.node_label(n) for n in NODES],
                                                          rotation=30, ha="right")
    ax_diff.set_yticks(range(4)); ax_diff.set_yticklabels([vs.node_label(n) for n in NODES])
    for i in range(4):
        for j in range(4):
            ax_diff.text(j, i, f"{dm.values[i,j]:+.2f}", ha="center", va="center",
                         fontsize=9, color=vs.INK if abs(dm.values[i, j]) < 0.6 else "white")
    ax_diff.set_title("Between minus within-person correlations")
    vs.matrix_axes(ax_diff)
    vs.add_cbar(fig, ax_diff, im2, pad=0.06)
    vs.panel_label(ax_diff, "C")

    ax = fig.add_subplot(gs[1, 1])
    vals = []
    labels = []
    for i, a in enumerate(NODES):
        for j, b in enumerate(NODES):
            if j <= i:
                continue
            vals.append((wm.loc[a, b], bm.loc[a, b]))
            labels.append(f"{vs.node_label(a)}-{vs.node_label(b)}")
    xs = np.array([v[0] for v in vals])
    ys = np.array([v[1] for v in vals])
    ax.scatter(xs, ys, s=90, color=vs.NODE_COLORS["ENMO"], edgecolor="white",
               linewidth=0.7, zorder=3)
    offsets = {
        "Pain-Stress": (-18, 10),
        "Fatigue-Stress": (10, -8),
        "Pain-Activity": (9, 3),
        "Fatigue-Activity": (8, -8),
        "Stress-Activity": (8, -3),
        "Pain-Fatigue": (8, 2),
    }
    for x, yv, lab in zip(xs, ys, labels):
        ax.annotate(lab, (x, yv), xytext=offsets.get(lab, (8, 4)),
                    textcoords="offset points", fontsize=7)
    ax.axhline(0, color=vs.GRID, lw=0.9)
    ax.axvline(0, color=vs.GRID, lw=0.9)
    lim = [-0.35, 0.85]
    ax.plot(lim, lim, color=vs.MUTED, ls="--", lw=1)
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("within-person correlation")
    ax.set_ylabel("between-person correlation")
    ax.set_title("Same pair, different level of analysis")
    vs.add_cbar(fig, ax, pad=0.06)
    vs.panel_label(ax, "D")

    vs.savefig(fig, S / "SUP_11_within_between_correlations.png")


def _nice_edge(e):
    lab = {"PIJN": "Pain", "MOE": "Fatigue", "STRESS": "Stress", "ENMO_log": "Activity"}
    a, b = e.split("__to__")
    return f"{lab.get(a, a)} -> {lab.get(b, b)}"


# SUP_12 - Robustness of the temporal network --------------------------------
def sup_09():
    det = pd.read_csv(N / "robust_detrended_compare.csv")
    loo = pd.read_csv(N / "robust_loo_summary.csv")
    boot = pd.read_csv(N / "robust_bootstrap_summary.csv")
    enmo = pd.read_csv(N / "robust_enmo_transform_compare.csv")
    thr = pd.read_csv(N / "robust_threshold40_compare.csv")
    cant = pd.read_csv(N / "cantmove_edge_comparison.csv")
    ext6 = pd.read_csv(N / "extended_core_vs_full_compare.csv")
    ext7 = pd.read_csv(N / "extended7_core_vs_full_compare.csv")

    fig = plt.figure(figsize=(14, 9))
    gs = GridSpec(2, 2, figure=fig, hspace=0.33, wspace=0.28)

    # A: bootstrap percentile CIs for every temporal edge (forest)
    ax = fig.add_subplot(gs[0, 0])
    b = boot.copy()
    b["is_ar"] = [e.split("__to__")[0] == e.split("__to__")[1] for e in b["edge"]]
    b = b.sort_values(["is_ar", "primary_weight"]).reset_index(drop=True)
    y = np.arange(len(b))
    for i, r in b.iterrows():
        col = vs.EDGE_POS if r["primary_weight"] >= 0 else vs.EDGE_NEG
        consistent = r["prop_sign_consistent"] >= 0.95
        ax.plot([r["ci_lo"], r["ci_hi"]], [i, i], color=col,
                lw=2.4 if consistent else 1.3, alpha=0.95 if consistent else 0.45,
                solid_capstyle="round")
        ax.plot(r["primary_weight"], i, "o", color=col, ms=6,
                markeredgecolor="white", markeredgewidth=0.8)
    ax.axvline(0, color=vs.INK, lw=0.9)
    ax.set_yticks(y); ax.set_yticklabels([_nice_edge(e) for e in b["edge"]], fontsize=7.5)
    ax.set_xlabel("temporal coefficient (person cluster-bootstrap 95% CI)")
    ax.set_title("Bootstrap stability of every edge")
    vs.panel_label(ax, "A")

    # B: LOPO ranges for the cross-lagged edges
    ax = fig.add_subplot(gs[0, 1])
    cl = loo[loo["from"] != loo["to"]].sort_values("mean").reset_index(drop=True)
    y = np.arange(len(cl))
    for i, r in cl.iterrows():
        col = vs.EDGE_POS if r["mean"] >= 0 else vs.EDGE_NEG
        ax.plot([r["min"], r["max"]], [i, i], color=col, lw=3, alpha=0.5,
                solid_capstyle="round")
        ax.plot(r["mean"], i, "o", color=col, ms=6, markeredgecolor="white")
    ax.axvline(0, color=vs.INK, lw=0.9)
    ax.set_yticks(y); ax.set_yticklabels([_nice_edge(e) for e in cl["edge"]], fontsize=7.5)
    ax.set_xlabel("range across 34 leave-one-out refits")
    ax.set_title("Leave-one-participant-out stability (cross-lagged edges)")
    vs.panel_label(ax, "B")

    # C: detrended vs primary scatter
    ax = fig.add_subplot(gs[1, 0])
    cols = [vs.EDGE_POS if w >= 0 else vs.EDGE_NEG for w in det["weight_ref"]]
    ax.scatter(det["weight_ref"], det["weight_detrended"], s=55, color=cols,
               edgecolor="white", linewidth=0.6, zorder=3)
    lim = [min(det[["weight_ref", "weight_detrended"]].min()) - 0.04,
           max(det[["weight_ref", "weight_detrended"]].max()) + 0.04]
    ax.plot(lim, lim, color=vs.MUTED, ls="--", lw=1)
    ax.set_xlim(lim); ax.set_ylim(lim)
    r = np.corrcoef(det["weight_ref"], det["weight_detrended"])[0, 1]
    ax.set_xlabel("primary model")
    ax.set_ylabel("within-person detrended")
    ax.set_title(f"Stationarity check: detrended vs primary (r = {r:.3f})")
    vs.panel_label(ax, "C")

    # D: agreement of all sensitivity refits with the primary network
    ax = fig.add_subplot(gs[1, 1])
    rows = [
        ("Detrended", np.corrcoef(det["weight_ref"], det["weight_detrended"])[0, 1]),
        ("Threshold >=40", np.corrcoef(thr["weight_ref"], thr["weight_thr40"])[0, 1]),
        ("ENMO raw", float(enmo.loc[enmo["transform"] == "raw", "r_vs_log"].iloc[0])),
        ("ENMO sqrt", float(enmo.loc[enmo["transform"] == "sqrt", "r_vs_log"].iloc[0])),
        ("Movement-only", np.corrcoef(cant["weight_all"], cant["weight_movement"])[0, 1]),
        ("6-node HAPA", np.corrcoef(ext6["weight_core4"], ext6["weight_extended"])[0, 1]),
        ("7-node HAPA", np.corrcoef(ext7["weight_core4"], ext7["weight_extended"])[0, 1]),
    ]
    labels = [r[0] for r in rows]; rs = [r[1] for r in rows]
    yb = np.arange(len(rows))
    ax.barh(yb, rs, color=vs.NODE_COLORS["ENMO"], alpha=0.9)
    for i, v in enumerate(rs):
        ax.text(v - 0.01, i, f"{v:.3f}", va="center", ha="right", color="white",
                fontweight="bold", fontsize=9)
    ax.set_yticks(yb); ax.set_yticklabels(labels)
    ax.set_xlim(0.9, 1.0)
    ax.set_xlabel("edge-weight correlation with primary network")
    ax.set_title("All sensitivity analyses agree with the primary model")
    vs.bar_axes(ax, "horizontal")
    vs.panel_label(ax, "D")
    vs.savefig(fig, S / "SUP_12_robustness.png")


# SUP_13 - mlVAR model diagnostics -------------------------------------------
def sup_10():
    res = pd.read_csv(N / "05_mlvar_residuals_long.csv")
    diag = pd.read_csv(T / "05_mlvar_residual_diagnostics.csv")
    nodes = ["PIJN", "MOE", "STRESS", "ENMO_log"]
    fig = plt.figure(figsize=(14, 8.5))
    gs = GridSpec(2, 2, figure=fig, hspace=0.34, wspace=0.26)

    # A: QQ plots per node (overlaid)
    ax = fig.add_subplot(gs[0, 0])
    from scipy import stats as st
    for nd in nodes:
        r = res.loc[res["node"] == nd, "residual"].dropna().values
        r = (r - r.mean()) / r.std()
        osm, osr = st.probplot(r, dist="norm")[0]
        ax.plot(osm, osr, ".", ms=2.5, alpha=0.5, color=vs.node_color(nd),
                label=vs.node_label(nd))
    lim = [-4, 4]
    ax.plot(lim, lim, color=vs.INK, lw=1)
    ax.set_xlim(lim); ax.set_ylim(-5, 5)
    ax.set_xlabel("theoretical quantiles"); ax.set_ylabel("standardized residual")
    ax.set_title("Normal QQ plots of residuals (by node)")
    ax.legend(fontsize=8, markerscale=3)
    vs.panel_label(ax, "A")

    # B: residual vs fitted (homoscedasticity)
    ax = fig.add_subplot(gs[0, 1])
    for nd in nodes:
        sub = res[res["node"] == nd]
        ax.scatter(sub["fitted"], sub["residual"], s=5, alpha=0.25,
                   color=vs.node_color(nd))
    ax.axhline(0, color=vs.INK, lw=0.9)
    ax.set_xlabel("fitted value"); ax.set_ylabel("residual")
    ax.set_title("Residuals vs fitted (homoscedasticity)")
    vs.panel_label(ax, "B")

    # C: within-person lag-1 residual autocorrelation summary (independence)
    ax = fig.add_subplot(gs[1, 0])
    yb = np.arange(len(diag))
    ax.barh(yb, diag["mean_within_acf1"], color=vs.NODE_COLORS["STRESS"], alpha=0.9)
    ax.axvline(0, color=vs.INK, lw=0.9)
    ax.set_yticks(yb); ax.set_yticklabels([vs.node_label(n) for n in diag["node"]])
    ax.set_xlim(-0.2, 0.2)
    ax.set_xlabel("mean within-person lag-1 residual autocorrelation")
    ax.set_title("Residual independence (near 0 = good)")
    vs.bar_axes(ax, "horizontal")
    vs.panel_label(ax, "C")

    # D: residual histogram (pooled) with normal overlay
    ax = fig.add_subplot(gs[1, 1])
    allr = res["residual"].dropna().values
    allr = (allr - allr.mean()) / allr.std()
    ax.hist(allr, bins=40, density=True, color=vs.NODE_COLORS["ENMO"], alpha=0.8)
    xs = np.linspace(-4, 4, 200)
    ax.plot(xs, st.norm.pdf(xs), color=vs.INK, lw=1.6)
    ax.set_xlabel("standardized residual"); ax.set_ylabel("density")
    ax.set_title("Pooled residual distribution vs normal")
    vs.panel_label(ax, "D")
    vs.savefig(fig, S / "SUP_13_model_diagnostics.png")


# SUP_14 - Activity context (location and social setting) --------------------
def sup_11():
    loc = pd.read_csv(T / "02_context_by_location.csv")
    soc = pd.read_csv(T / "02_context_by_social.csv")
    soc_eff = pd.read_csv(T / "02_context_social_effects.csv")
    fig = plt.figure(figsize=(14, 10))
    gs = GridSpec(3, 2, figure=fig, hspace=0.42, wspace=0.30)

    # A: where prompts occur
    ax = fig.add_subplot(gs[0, 0])
    lo = loc.sort_values("n_prompts", ascending=True)
    ax.barh(lo["location"], lo["pct"], color=vs.NODE_COLORS["MOE"], alpha=0.9)
    ax.set_xlabel("% of prompts")
    ax.set_title("Where momentary reports occur")
    vs.bar_axes(ax, "horizontal")
    vs.panel_label(ax, "A")

    # B: objective activity by location
    ax = fig.add_subplot(gs[0, 1])
    lo2 = loc.sort_values("mean_ENMO", ascending=True)
    ax.barh(lo2["location"], lo2["mean_ENMO"], color=vs.NODE_COLORS["ENMO"], alpha=0.9)
    ax.set_xlabel("mean ENMO (g)")
    ax.set_title("Objective activity by location")
    vs.bar_axes(ax, "horizontal")
    vs.panel_label(ax, "B")

    # C: affect by location (pain, fatigue, and stress)
    ax = fig.add_subplot(gs[1, 0])
    long = loc[["location", "mean_pain", "mean_fatigue", "mean_stress"]].copy()
    long = long.set_index("location").loc[lo2["location"]]
    y = np.arange(len(long))
    ax.plot(long["mean_pain"], y, "o-", color=vs.NODE_COLORS["PIJN"], label="Pain")
    ax.plot(long["mean_fatigue"], y, "o-", color=vs.NODE_COLORS["MOE"], label="Fatigue")
    ax.plot(long["mean_stress"], y, "o-", color=vs.NODE_COLORS["STRESS"], label="Stress")
    ax.set_yticks(y); ax.set_yticklabels(long.index)
    ax.set_xlabel("mean rating (0-10)")
    ax.set_title("Pain, fatigue, and stress across locations")
    ax.legend(fontsize=8)
    vs.panel_label(ax, "C")

    # D: affect by social context
    ax = fig.add_subplot(gs[1, 1])
    dctx = ema.copy()
    dctx["alone_binary"] = pd.to_numeric(dctx["ALLEEN"], errors="coerce")
    metrics = [("PIJN", "Pain", vs.NODE_COLORS["PIJN"]),
               ("MOE", "Fatigue", vs.NODE_COLORS["MOE"]),
               ("STRESS", "Stress", vs.NODE_COLORS["STRESS"])]
    rng = np.random.default_rng(31)
    xticks, xticklabels = [], []
    ymax = 0
    for i, (var, lab, col) in enumerate(metrics):
        base = i * 3.0
        accompanied = dctx.loc[dctx["alone_binary"] == 0, var].dropna()
        alone = dctx.loc[dctx["alone_binary"] == 1, var].dropna()
        _violin_scatter_pair(ax, [accompanied, alone], [base, base + 1.0],
                             [vs.MUTED, col], rng, point_size=8, alpha=0.12)
        xticks.extend([base, base + 1.0])
        xticklabels.extend([f"{lab}\nAccomp.", f"{lab}\nAlone"])
        p = float(soc_eff.loc[soc_eff["variable"] == var, "p"].iloc[0])
        local_max = max(accompanied.max(), alone.max()) if len(accompanied) and len(alone) else 10
        y = min(10.45, local_max + 0.45)
        _sig_bar(ax, base, base + 1.0, y, p, h=0.12)
        ymax = max(ymax, y + 0.32)
    ax.set_xticks(xticks); ax.set_xticklabels(xticklabels, fontsize=7)
    ax.set_ylim(-0.4, max(10.8, ymax))
    ax.set_ylabel("rating (0-10)")
    ax.set_title("Momentary affect: alone vs accompanied")
    ax.plot([], [], color=vs.INK, lw=2.0, label="mean")
    ax.plot([], [], marker="D", ms=5, color="white", markeredgecolor=vs.INK,
            lw=0, label="median")
    ax.legend(fontsize=7, loc="upper left")
    vs.panel_label(ax, "D")

    # E: planned movement by symptom tertile
    ax = fig.add_subplot(gs[2, 0])
    d = ema.dropna(subset=["TOEK_ACT", "PIJN", "MOE", "STRESS"]).copy()
    metrics = [("PIJN", "Pain"), ("MOE", "Fatigue"), ("STRESS", "Stress")]
    bins = ["low", "middle", "high"]
    x = np.arange(3); w = 0.24
    for i, (var, lab) in enumerate(metrics):
        q = pd.qcut(d[var], 3, labels=bins, duplicates="drop")
        pct = d.assign(bin=q).groupby("bin", observed=False)["TOEK_ACT"].mean() * 100
        pct = pct.reindex(bins)
        ax.bar(x + (i - 1) * w, pct.values, width=w, label=lab,
               color=vs.node_color(var), alpha=0.88)
    ax.set_xticks(x); ax.set_xticklabels(bins)
    ax.set_ylabel("planned movement in next 2 h (%)")
    ax.set_title("Future movement plans across symptom levels")
    ax.legend(fontsize=8)
    vs.bar_axes(ax, "vertical")
    vs.panel_label(ax, "E")

    # F: opportunity, recent activity, and plans by prompt of day
    ax = fig.add_subplot(gs[2, 1])
    byb = (
        ema.groupby("beep")
        .agg(
            can_move=("MOGELIJKHEID_BEW", lambda s: 100 * (s == 1).mean()),
            active_since_last=("ACTIVITEITEN", lambda s: 100 * (s == 1).mean()),
            planned_movement=("TOEK_ACT", lambda s: 100 * (s == 1).mean()),
        )
        .reset_index()
    )
    ax.plot(byb["beep"], byb["can_move"], "-o", lw=2, color=vs.NODE_COLORS["EIGENEFF"],
            label="able to move")
    ax.plot(byb["beep"], byb["active_since_last"], "-o", lw=2, color=vs.NODE_COLORS["ENMO"],
            label="active since last prompt")
    ax.plot(byb["beep"], byb["planned_movement"], "-o", lw=2, color=vs.NODE_COLORS["INTENTIE"],
            label="planned movement")
    ax.set_xticks([1, 2, 3, 4])
    ax.set_xlabel("prompt of day")
    ax.set_ylabel("% of answered prompts")
    ax.set_ylim(0, 100)
    ax.set_title("Movement opportunity and plans across the day")
    ax.legend(fontsize=8)
    vs.panel_label(ax, "F")

    vs.savefig(fig, S / "SUP_14_context.png")


# SUP_15 - Weekday vs weekend day-type effects --------------------------------
def sup_daytype():
    eff = pd.read_csv(T / "02_daytype_effects.csv")
    ctx_person = pd.read_csv(T / "02_daytype_context_person.csv")
    ctx_eff = pd.read_csv(T / "02_daytype_context_effects.csv")
    dow = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    e = ema.dropna(subset=["weekday"]).copy()
    e["weekday"] = e["weekday"].astype(int)
    fig = plt.figure(figsize=(15, 9.4))
    gs = GridSpec(2, 3, figure=fig, hspace=0.5, wspace=0.34)

    # A: group-level weekend effect (standardized) with 95% CI
    ax = fig.add_subplot(gs[0, 0])
    eff = eff.iloc[::-1].reset_index(drop=True)
    yy = np.arange(len(eff))
    for i, r in eff.iterrows():
        sig = r["p"] < 0.05
        col = vs.EDGE_POS if r["std_delta"] >= 0 else vs.EDGE_NEG
        ax.plot([r["ci_lo"], r["ci_hi"]], [i, i], color=col, lw=2.4 if sig else 1.3,
                alpha=0.95 if sig else 0.45, solid_capstyle="round")
        ax.plot(r["std_delta"], i, "o", color=col, ms=8 if sig else 5,
                markeredgecolor="white", markeredgewidth=1, alpha=0.95 if sig else 0.5)
    ax.axvline(0, color=vs.INK, lw=0.9)
    ax.set_yticks(yy); ax.set_yticklabels(eff["label"], fontsize=9)
    ax.set_xlabel("weekend minus weekday (SD units, 95% CI)")
    ax.set_title("Group-level weekend effects (GEE)")
    vs.add_cbar(fig, ax)
    vs.panel_label(ax, "A")

    # B: weekly rhythm - mean z-scored measure by day of week
    ax = fig.add_subplot(gs[0, 1])
    for v in ["PIJN", "MOE", "STRESS", "ENMO_log"]:
        z = (e[v] - e[v].mean()) / e[v].std(ddof=0)
        m = z.groupby(e["weekday"]).mean().reindex(range(7))
        ax.plot(range(7), m.values, "-o", lw=1.8, ms=4, color=vs.node_color(v),
                label=vs.node_label(v))
    ax.axvspan(4.5, 6.5, color=vs.GRID, alpha=0.5, zorder=0)
    ax.axhline(0, color=vs.INK, lw=0.8)
    ax.set_xticks(range(7)); ax.set_xticklabels(dow, fontsize=8)
    ax.set_ylabel("mean (within-measure z)")
    ax.set_title("Weekly rhythm of momentary measures")
    ax.legend(fontsize=8, ncol=2)
    vs.add_cbar(fig, ax)
    vs.panel_label(ax, "B")

    # C: stress weekday vs weekend (the one significant contrast)
    ax = fig.add_subplot(gs[0, 2])
    rng = np.random.default_rng(43)
    stress_weekday = e.loc[e["is_weekend"] == 0, "STRESS"].dropna()
    stress_weekend = e.loc[e["is_weekend"] == 1, "STRESS"].dropna()
    _violin_scatter_pair(ax, [stress_weekday, stress_weekend], [0, 1],
                         [vs.MUTED, vs.NODE_COLORS["STRESS"]], rng,
                         point_size=8, alpha=0.12)
    pstr = float(eff.loc[eff["variable"] == "STRESS", "p"].iloc[0])
    _sig_bar(ax, 0, 1, min(10.45, max(stress_weekday.max(), stress_weekend.max()) + 0.45),
             pstr, h=0.12)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["Weekday", "Weekend"])
    ax.set_ylabel("momentary stress (0-10)")
    ax.set_ylim(-0.4, 10.9)
    ax.set_title(f"Stress by day type (GEE p = {pstr:.3f})")
    ax.plot([], [], color=vs.INK, lw=2.0, label="mean")
    ax.plot([], [], marker="D", ms=5, color="white", markeredgecolor=vs.INK,
            lw=0, label="median")
    vs.add_cbar(fig, ax)
    vs.panel_label(ax, "C")

    # D: response rate by day of week
    ax = fig.add_subplot(gs[1, 0])
    rr = e.groupby("weekday")["completed"].apply(lambda s: 100 * (s == True).mean()).reindex(range(7))
    cols = [vs.NODE_COLORS["PIJN"] if d >= 5 else vs.NODE_COLORS["ENMO"] for d in range(7)]
    ax.bar(range(7), rr.values, color=cols, alpha=0.85)
    ax.set_xticks(range(7)); ax.set_xticklabels(dow, fontsize=8)
    ax.set_ylim(50, 90); ax.set_ylabel("prompts answered (%)")
    ax.set_title("Compliance by day of week")
    vs.bar_axes(ax, "vertical")
    vs.add_cbar(fig, ax)
    vs.panel_label(ax, "D")

    # E: objective activity by day of week
    ax = fig.add_subplot(gs[1, 1])
    me = e.groupby("weekday")["ENMO"].mean().reindex(range(7))
    ax.plot(range(7), me.values, "-o", lw=2, ms=5, color=vs.NODE_COLORS["ENMO"])
    ax.axvspan(4.5, 6.5, color=vs.GRID, alpha=0.5, zorder=0)
    ax.set_xticks(range(7)); ax.set_xticklabels(dow, fontsize=8)
    ax.set_ylabel("mean ENMO (g)")
    ax.set_title("Objective activity by day of week")
    vs.add_cbar(fig, ax)
    vs.panel_label(ax, "E")

    # F: everyday context (at home, alone) by day type
    ax = fig.add_subplot(gs[1, 2])
    rng = np.random.default_rng(44)
    positions = {"at_home": (0, 1), "alone": (3, 4)}
    colors = {"at_home": vs.NODE_COLORS["MOE"], "alone": vs.NODE_COLORS["STRESS"]}
    labels = {"at_home": "At home", "alone": "Alone"}
    xticks, xticklabels = [], []
    for metric in ["at_home", "alone"]:
        p0, p1 = positions[metric]
        d0 = ctx_person[(ctx_person["metric"] == metric) &
                        (ctx_person["day_type"] == "Weekday")]["pct"]
        d1 = ctx_person[(ctx_person["metric"] == metric) &
                        (ctx_person["day_type"] == "Weekend")]["pct"]
        _violin_scatter_pair(ax, [d0, d1], [p0, p1], [vs.MUTED, colors[metric]], rng,
                             point_size=18, alpha=0.55)
        p = float(ctx_eff.loc[ctx_eff["metric"] == metric, "p_wilcoxon"].iloc[0])
        _sig_bar(ax, p0, p1, 103, p, h=2.0)
        xticks.extend([p0, p1])
        xticklabels.extend([f"{labels[metric]}\nWeekday", f"{labels[metric]}\nWeekend"])
    ax.set_xticks(xticks); ax.set_xticklabels(xticklabels, fontsize=7)
    ax.set_ylabel("% of prompts per participant")
    ax.set_ylim(-5, 110)
    ax.set_title("Everyday context by day type")
    ax.plot([], [], color=vs.INK, lw=2.0, label="mean")
    ax.plot([], [], marker="D", ms=5, color="white", markeredgecolor=vs.INK,
            lw=0, label="median")
    vs.add_cbar(fig, ax)
    vs.panel_label(ax, "F")

    vs.savefig(fig, S / "SUP_15_daytype.png")


if __name__ == "__main__":
    # Execution follows the supplementary display order (S1..S15); the imputation
    # benchmark (S5) sits with the other preprocessing/missing-data figures.
    for fn in [sup_design, sup_timing, sup_01, sup_02, sup_imputation, sup_03,
               sup_04, sup_05, sup_06, sup_07, sup_08, sup_09, sup_10, sup_11,
               sup_daytype]:
        fn()
    print("\nSupplementary figures written to", S)
