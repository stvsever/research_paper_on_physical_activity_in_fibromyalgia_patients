"""Stage 02b - Activity context descriptives (location and social setting).

Beyond the core network variables, each prompt recorded WHERE the participant was (WAAR)
and WHETHER they were alone (ALLEEN). These context fields are otherwise unused but are
informative: they show in which everyday situations momentary activity and affect arise,
and whether activity is concentrated away from home. This stage produces context
descriptives and a within-person comparison of objective activity at home vs away.

Outputs feed the context supplementary figure and table.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
import paths  # noqa: E402

paths.ensure_dirs()
ema = pd.read_csv(paths.EMA_LONG)

# WAAR location codes (from the EMA item "Where are you currently?").
LOC = {0: "Home", 1: "Outside", 2: "Commuting", 3: "Work", 4: "Physiotherapist",
       5: "Hospital", 6: "Shop", 7: "Other"}
ema["WAAR_num"] = pd.to_numeric(ema["WAAR"], errors="coerce")
ema["location"] = ema["WAAR_num"].map(LOC)
ema["away_from_home"] = np.where(ema["WAAR_num"].notna(), (ema["WAAR_num"] != 0).astype(float), np.nan)

# --- location distribution and activity by location --------------------------
loc_tab = (ema.groupby("location")
           .agg(n_prompts=("location", "size"),
                pct=("location", lambda s: 100 * len(s) / ema["location"].notna().sum()),
                mean_ENMO=("ENMO", "mean"),
                mean_pain=("PIJN", "mean"),
                mean_fatigue=("MOE", "mean"),
                mean_stress=("STRESS", "mean"))
           .reindex([v for v in LOC.values() if v in ema["location"].unique()])
           .round(3).reset_index())
loc_tab.to_csv(paths.RESULTS_TABLES / "02_context_by_location.csv", index=False)
print("Activity and affect by location:\n", loc_tab.to_string(index=False), "\n")

# --- social context: alone vs accompanied ------------------------------------
soc = (ema.assign(social=ema["ALLEEN"].map({1.0: "Alone", 0.0: "Accompanied"}))
       .groupby("social")
       .agg(n=("social", "size"), mean_ENMO=("ENMO", "mean"),
            mean_pain=("PIJN", "mean"), mean_fatigue=("MOE", "mean"),
            mean_stress=("STRESS", "mean")).round(3).reset_index())
soc.to_csv(paths.RESULTS_TABLES / "02_context_by_social.csv", index=False)
print("Affect/activity by social context:\n", soc.to_string(index=False), "\n")

# --- inferential comparison: alone vs accompanied ----------------------------
# The plotted observations are nested within participants, so the inferential comparison
# uses Gaussian GEE with participant clustering rather than an independent-samples test.
ema["alone_binary"] = pd.to_numeric(ema["ALLEEN"], errors="coerce")
tests = []
for v, lab in [("PIJN", "Pain"), ("MOE", "Fatigue"), ("STRESS", "Stress")]:
    d = ema.dropna(subset=[v, "alone_binary", "pid"]).copy()
    try:
        md = smf.gee(
            f"{v} ~ alone_binary",
            groups="pid",
            data=d,
            cov_struct=sm.cov_struct.Exchangeable(),
            family=sm.families.Gaussian(),
        ).fit()
        b = float(md.params["alone_binary"])
        se = float(md.bse["alone_binary"])
        p = float(md.pvalues["alone_binary"])
    except Exception:
        b = se = p = np.nan
    tests.append({
        "variable": v,
        "label": lab,
        "n": int(len(d)),
        "n_persons": int(d["pid"].nunique()),
        "accompanied_mean": round(d.loc[d["alone_binary"] == 0, v].mean(), 3),
        "alone_mean": round(d.loc[d["alone_binary"] == 1, v].mean(), 3),
        "b_alone": round(b, 3),
        "se": round(se, 3),
        "p": round(p, 4),
        "test": "Gaussian GEE, exchangeable participant correlation",
    })
social_tests = pd.DataFrame(tests)
social_tests.to_csv(paths.RESULTS_TABLES / "02_context_social_effects.csv", index=False)
print("Alone vs accompanied GEE tests:\n", social_tests.to_string(index=False), "\n")

# --- within-person: is activity higher away from home? -----------------------
# person-mean-center away_from_home and ENMO_log, correlate within person (pooled)
d = ema.dropna(subset=["away_from_home", "ENMO_log"]).copy()
d["awc"] = d["away_from_home"] - d.groupby("pid")["away_from_home"].transform("mean")
d["ec"] = d["ENMO_log"] - d.groupby("pid")["ENMO_log"].transform("mean")
within_r = np.corrcoef(d["awc"], d["ec"])[0, 1]
home = d.loc[d["away_from_home"] == 0, "ENMO"].mean()
away = d.loc[d["away_from_home"] == 1, "ENMO"].mean()
summary = pd.DataFrame([{
    "within_person_r_away_vs_logENMO": round(within_r, 3),
    "mean_ENMO_home": round(home, 4),
    "mean_ENMO_away": round(away, 4),
    "pct_prompts_at_home": round(100 * (ema["away_from_home"] == 0).sum()
                                 / ema["away_from_home"].notna().sum(), 1),
}])
summary.to_csv(paths.RESULTS_TABLES / "02_context_activity_summary.csv", index=False)
print("Context-activity summary:\n", summary.to_string(index=False))
print("\nStage 02b context descriptives complete.")
