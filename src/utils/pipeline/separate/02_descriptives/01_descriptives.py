"""Stage 02 - Descriptive statistics (sample, EMA variables, compliance, correlations).

Produces the numeric tables that feed the main descriptive table (Table 1), the design /
compliance figure, and the within- vs between-person correlation panels. All outputs are
CSVs in src/results/tables; figures are rendered in the figures stage.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
import paths  # noqa: E402

paths.ensure_dirs()

ema = pd.read_csv(paths.EMA_LONG)
pl = pd.read_csv(paths.PERSON_LEVEL)
pl_an = pl[pl["in_analytic_sample"]].copy()

CORE = ["PIJN", "MOE", "STRESS", "ENMO", "ENMO_log",
        "EIGENEFF", "INTENTIE", "UITKOMSTVERW"]
LABELS = {"PIJN": "Pain (0-10)", "MOE": "Fatigue (0-10)", "STRESS": "Stress (0-10)",
          "ENMO": "Activity ENMO (g)", "ENMO_log": "Activity log-ENMO",
          "EIGENEFF": "Self-efficacy (1-5)", "INTENTIE": "Intention (1-5)",
          "UITKOMSTVERW": "Rest-expectancy (1-5)"}


# ---------------------------------------------------------------------------
# 1. EMA variable descriptives with within/between decomposition (descriptive).
# ---------------------------------------------------------------------------
def between_within(df, var):
    g = df.groupby("pid")[var]
    person_means = g.mean()
    sd_between = person_means.std(ddof=1)
    # within-person SD = sd of (x - person mean), pooled
    dev = df[var] - df["pid"].map(person_means)
    sd_within = dev.std(ddof=1)
    return sd_between, sd_within


rows = []
for v in CORE:
    s = ema[v]
    sb, sw = between_within(ema, v)
    rows.append({
        "variable": v, "label": LABELS[v],
        "n_obs": int(s.notna().sum()),
        "mean": round(s.mean(), 3), "sd": round(s.std(), 3),
        "median": round(s.median(), 3),
        "min": round(s.min(), 3), "max": round(s.max(), 3),
        "sd_between_person": round(sb, 3), "sd_within_person": round(sw, 3),
        "pct_missing": round(100 * s.isna().mean(), 1),
    })
ema_desc = pd.DataFrame(rows)
ema_desc.to_csv(paths.RESULTS_TABLES / "02_ema_descriptives.csv", index=False)
print("EMA descriptives:\n", ema_desc.to_string(index=False), "\n")

# ---------------------------------------------------------------------------
# 2. Compliance.
# ---------------------------------------------------------------------------
comp = ema.groupby("pid")["completed"].agg(["sum", "count"])
comp["rate"] = comp["sum"] / comp["count"]
compliance = {
    "n_participants": int(ema["pid"].nunique()),
    "n_triggers_total": int(len(ema)),
    "n_completed_total": int(ema["completed"].sum()),
    "completed_per_person_mean": round(comp["sum"].mean(), 1),
    "completed_per_person_median": float(comp["sum"].median()),
    "completed_per_person_min": int(comp["sum"].min()),
    "completed_per_person_max": int(comp["sum"].max()),
    "compliance_rate_mean": round(comp["rate"].mean(), 3),
    "enmo_available_pct": round(100 * ema["ENMO"].notna().mean(), 1),
    "could_not_move_pct": round(
        100 * ema["MOGELIJKHEID_BEW"].eq(0).sum()
        / ema["MOGELIJKHEID_BEW"].notna().sum(), 1),
}
pd.DataFrame([compliance]).T.rename(columns={0: "value"}).to_csv(
    paths.RESULTS_TABLES / "02_compliance_summary.csv")
comp.reset_index().to_csv(paths.RESULTS_TABLES / "02_compliance_per_person.csv", index=False)
print("Compliance:", compliance, "\n")

# ---------------------------------------------------------------------------
# 3. Person-level (baseline) descriptives -> Table 1.
# ---------------------------------------------------------------------------
def summ_num(s):
    s = pd.to_numeric(s, errors="coerce")
    return f"{s.mean():.1f} ({s.std():.1f})", f"{s.min():.0f}-{s.max():.0f}", int(s.notna().sum())


t1_rows = []
for var, label in [("age", "Age (years)"), ("BMI", "BMI (kg/m2)"),
                   ("POAMP_Avoidance", "POAM-P Avoidance (0-40)"),
                   ("POAMP_Overdoing", "POAM-P Overdoing (0-40)"),
                   ("POAMP_Pacing", "POAM-P Pacing (0-40)"),
                   ("TSK_sum", "Kinesiophobia TSK (17-68)"),
                   ("PainInterference_sum", "PROMIS pain interference (sum)"),
                   ("SelfEfficacy", "Self-efficacy (baseline, 1-5)"),
                   ("OutcomeExpectancy", "Outcome expectancy (1-5)"),
                   ("ActionPlanning", "Action planning (1-5)")]:
    if var in pl_an.columns:
        m_sd, rng, n = summ_num(pl_an[var])
        t1_rows.append({"variable": label, "mean_sd": m_sd, "range": rng, "n": n})
t1 = pd.DataFrame(t1_rows)
t1.to_csv(paths.RESULTS_TABLES / "02_person_level_table1.csv", index=False)
print("Table 1 (person-level):\n", t1.to_string(index=False), "\n")

# Education distribution.
edu = pl_an["education"].value_counts(dropna=False).rename_axis("education").reset_index(name="n")
edu.to_csv(paths.RESULTS_TABLES / "02_education_distribution.csv", index=False)

# ---------------------------------------------------------------------------
# 4. Within- and between-person correlations among core nodes.
# ---------------------------------------------------------------------------
nodes = ["PIJN", "MOE", "STRESS", "ENMO_log"]
# between-person: correlate person means
pmeans = ema.groupby("pid")[nodes].mean()
between_corr = pmeans.corr()
between_corr.to_csv(paths.RESULTS_TABLES / "02_between_person_corr.csv")
# within-person: correlate person-mean-centered values
centered = ema[nodes] - ema.groupby("pid")[nodes].transform("mean")
within_corr = centered.corr()
within_corr.to_csv(paths.RESULTS_TABLES / "02_within_person_corr.csv")
print("Within-person correlations:\n", within_corr.round(2).to_string())

print("\nStage 02 descriptives complete.")
