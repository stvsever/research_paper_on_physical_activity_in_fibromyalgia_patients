"""Stage 09 - Link individual network parameters to POAM-P patterns (exploratory RQ2).

Implements the two bridges Annick proposed between RQ1 and RQ2:
  (1) use each person's network parameters (subject-specific mlVAR lag-1 coefficients, e.g.
      Pain -> Activity, Activity -> Pain, and temporal density) as outcomes and relate them
      to the POAM-P subscales via Spearman correlations;
  (2) compare those parameters across the POAM-P dominant-pattern groups (Kruskal-Wallis).

Strong caveats, reported alongside the numbers:
  - N = 31 with both network and POAM-P data: this is severely underpowered for subgroup
    inference, so everything here is descriptive / hypothesis-generating.
  - The subject-specific mlVAR coefficients are empirical-Bayes (shrunken) estimates, so
    their between-person spread is conservative; null associations may reflect shrinkage as
    much as true absence of effect.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
import paths  # noqa: E402

paths.ensure_dirs()

# Individual coupling strengths come from the UNREGULARIZED per-person VAR (stage 07b),
# which - unlike the shrunken mlVAR BLUPs - genuinely vary across persons. Temporal density
# is taken from the mlVAR subject coefficients.
coefs = pd.read_csv(paths.RESULTS_NETWORKS / "07_perperson_var_ols_wide.csv")
dens = pd.read_csv(paths.RESULTS_NETWORKS / "05_mlvar_core_subject_temporal_coefs.csv")
coefs = coefs.merge(dens[["pid", "temporal_density"]], on="pid", how="left")
sub = pd.read_csv(paths.DATA_PROCESSED / "poamp_subgroups.csv")
gv = pd.read_csv(paths.RESULTS_TABLES / "07_graphicalvar_individual_summary.csv")

# Parameters of interest (per-person standardized lag-1 coefficients + density).
PARAMS = {
    "PIJN__to__ENMO_log": "Pain -> Activity",
    "MOE__to__ENMO_log": "Fatigue -> Activity",
    "STRESS__to__ENMO_log": "Stress -> Activity",
    "ENMO_log__to__PIJN": "Activity -> Pain",
    "ENMO_log__to__MOE": "Activity -> Fatigue",
    "temporal_density": "Temporal density",
}
SUBSCALES = ["POAMP_Avoidance", "POAMP_Overdoing", "POAMP_Pacing"]

m = coefs.merge(sub, on="pid", how="inner")
print(f"Participants with network + POAM-P: {len(m)}")

# --- (1) Spearman correlations: network params x POAM-P subscales -------------
rows = []
for p, plab in PARAMS.items():
    for s in SUBSCALES:
        x = m[p].astype(float)
        y = m[s].astype(float)
        ok = x.notna() & y.notna()
        rho, pv = stats.spearmanr(x[ok], y[ok])
        rows.append({"parameter": plab, "poamp_subscale": s.replace("POAMP_", ""),
                     "spearman_rho": round(rho, 3), "p_value": round(pv, 3),
                     "n": int(ok.sum())})
corr = pd.DataFrame(rows)
corr.to_csv(paths.RESULTS_TABLES / "09_param_poamp_correlations.csv", index=False)
print("\nNetwork-parameter x POAM-P correlations (Spearman):")
print(corr.pivot(index="parameter", columns="poamp_subscale",
                 values="spearman_rho").to_string())

# --- (2) group comparison across dominant pattern ----------------------------
rows = []
for p, plab in PARAMS.items():
    groups = [g[p].dropna().values for _, g in m.groupby("dominant_pattern")]
    if all(len(g) >= 2 for g in groups) and len(groups) >= 2:
        H, pv = stats.kruskal(*groups)
    else:
        H, pv = np.nan, np.nan
    gm = m.groupby("dominant_pattern")[p].mean().round(3)
    rows.append({"parameter": plab,
                 **{f"mean_{k}": v for k, v in gm.items()},
                 "kruskal_H": round(H, 3) if pd.notna(H) else np.nan,
                 "p_value": round(pv, 3) if pd.notna(pv) else np.nan})
grp = pd.DataFrame(rows)
grp.to_csv(paths.RESULTS_TABLES / "09_param_by_dominant_pattern.csv", index=False)
print("\nNetwork parameters by POAM-P dominant pattern (Kruskal-Wallis):")
print(grp.to_string(index=False))

# --- (3) joint multiple regression of Pain->Activity on POAM-P (approach A) ---
# Annick's approach A in one model: beta_{Pain->PA,i} = g0 + g1 Avoid + g2 Overdo + g3 Pace.
# Reported as explicitly exploratory: N=30 with 3 predictors and a noisy two-step outcome,
# so it is underpowered. The bivariate Spearman + permutation results above are primary.
import statsmodels.api as sm  # noqa: E402

reg = m.dropna(subset=["PIJN__to__ENMO_log", "z_Avoidance", "z_Overdoing", "z_Pacing"])
X = sm.add_constant(reg[["z_Avoidance", "z_Overdoing", "z_Pacing"]])
ols = sm.OLS(reg["PIJN__to__ENMO_log"].astype(float), X.astype(float)).fit()
jr = pd.DataFrame({
    "term": ["Intercept", "Avoidance", "Overdoing", "Pacing"],
    "beta": ols.params.round(3).values,
    "se": ols.bse.round(3).values,
    "p": ols.pvalues.round(3).values,
})
jr.to_csv(paths.RESULTS_TABLES / "09_joint_regression_pain_activity.csv", index=False)
print("\n(3) Joint regression Pain->Activity ~ POAM-P (exploratory, approach A):")
print(jr.to_string(index=False))
print(f"   N={reg.shape[0]}, R2={ols.rsquared:.3f}, adj R2={ols.rsquared_adj:.3f}, "
      f"overall F p={ols.f_pvalue:.3f}")

# --- merged analysis frame for the figure stage ------------------------------
m_keep = m[["pid"] + list(PARAMS) + SUBSCALES +
           ["z_Avoidance", "z_Overdoing", "z_Pacing", "dominant_pattern", "cluster"]]
m_keep = m_keep.merge(gv[["pid", "temporal_density"]].rename(
    columns={"temporal_density": "gvar_temporal_density"}), on="pid", how="left")
m_keep.to_csv(paths.DATA_PROCESSED / "link_analysis_frame.csv", index=False)
print(f"\nWrote link analysis frame: {m_keep.shape}")
print(f"\nNote: all RQ2 link results are exploratory (N={len(m_keep)}, uncorrected). "
      "Per-person VAR coefficients are unregularized OLS (noisy at T~44).")
