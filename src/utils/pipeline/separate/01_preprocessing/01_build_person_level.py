"""Stage 01.1 - Build the person-level (baseline) dataset.

Reads the baseline ``begin studie`` SPSS file and derives one row per participant with:
  - POAM-P subscales (Avoidance / Overdoing / Pacing) -> RQ2 subgroups,
  - demographics (age, sex, education, BMI, marital status, children, work),
  - clinical scores (GCPS grade, Tampa kinesiophobia, PROMIS pain interference, IPAQ),
  - social-cognitive determinants (self-efficacy, outcome expectancy, risk perception,
    action/coping planning, self-monitoring).

Scoring follows the original author's R merge script. POAM-P items are already coded 0-4
by pyreadstat, so no offset is applied (the R script's ``- 1`` only undid factor coding).

Output: src/data/processed/person_level.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
import paths  # noqa: E402

paths.ensure_dirs()

df, meta = pyreadstat.read_sav(str(paths.RAW_BASELINE_SAV))
df["token"] = df["token"].astype(str).str.strip()

# Non-starters excluded already in the author's merge script.
NON_STARTERS = ["wo0026569", "wo0067892"]
df = df[~df["token"].isin(NON_STARTERS)].copy()

out = pd.DataFrame({"token": df["token"].values})

# --- POAM-P subscales (items 0-4 each; 10 items per subscale; range 0-40) -----
AVOID = [1, 6, 8, 11, 13, 16, 19, 22, 25, 28]
OVER = [2, 4, 7, 10, 15, 18, 20, 23, 26, 30]
PACE = [3, 5, 9, 12, 14, 17, 21, 24, 27, 29]


def poamp_sum(items):
    cols = [f"POAMP_{i}" for i in items]
    return df[cols].sum(axis=1, min_count=len(cols))  # NA if any item missing


out["POAMP_Avoidance"] = poamp_sum(AVOID)
out["POAMP_Overdoing"] = poamp_sum(OVER)
out["POAMP_Pacing"] = poamp_sum(PACE)

# --- Demographics -------------------------------------------------------------
# Age from birthdate (Leeftijd) and submit date.
def to_dt(s):
    return pd.to_datetime(s, errors="coerce")


birth = to_dt(df.get("Leeftijd"))
submit = to_dt(df.get("submitdate"))
age = (submit - birth).dt.days / 365.25
age = age.where(age > 5)  # one stray 0/age artifact -> NA
out["age"] = np.floor(age)

out["sex"] = df["Geslacht"].map({1.0: "Female", 0.0: "Male"})
out["education"] = df["Opleiding"].astype(str).replace({"": np.nan, "nan": np.nan})

# BMI
weight = pd.to_numeric(df.get("Gewicht"), errors="coerce")
height = pd.to_numeric(df.get("Grootte"), errors="coerce")
out["BMI"] = weight / (height / 100.0) ** 2

# --- GCPS (Graded Chronic Pain Scale) ----------------------------------------
def numlabel(col):
    """Return numeric codes for a possibly string/labelled column."""
    return pd.to_numeric(df.get(col), errors="coerce")


for c in ["GCPS3_GCPS3", "GCPS4_GCPS4", "GCPS5_GCPS5"]:
    if c in df.columns:
        out_c = pd.to_numeric(df[c], errors="coerce")
        df[c + "_n"] = out_c
gcps_peg = df.get("GCPS3_GCPS3_n", pd.Series(np.nan, index=df.index)) \
    + df.get("GCPS4_GCPS4_n", 0) + df.get("GCPS5_GCPS5_n", 0)
out["GCPS_PEG"] = gcps_peg

# --- Tampa Scale of Kinesiophobia (17 items; 4,8,12,16 reverse-scored 1-4) ----
tsk_items = {i: pd.to_numeric(df.get(f"TSK_{i}"), errors="coerce") for i in range(1, 18)}
for r in (4, 8, 12, 16):
    tsk_items[r] = 5 - tsk_items[r]
tsk = sum(tsk_items.values())
out["TSK_sum"] = tsk

# --- PROMIS pain interference (sum -> T-score) --------------------------------
pi_cols = [f"pijninterferentie_{i}" for i in range(1, 9)]
if all(c in df.columns for c in pi_cols):
    pi_sum = df[pi_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1, min_count=8)
    out["PainInterference_sum"] = pi_sum

# --- Social-cognitive determinants (means) ------------------------------------
def mean_items(prefix, n, rev=None, rng=5):
    cols = [f"{prefix}{i}" for i in range(1, n + 1)]
    sub = df[[c for c in cols if c in df.columns]].apply(pd.to_numeric, errors="coerce")
    if rev:
        for r in rev:
            cc = f"{prefix}{r}"
            if cc in sub.columns:
                sub[cc] = (rng + 1) - sub[cc]
    return sub.mean(axis=1)


out["SelfEfficacy"] = mean_items("EigenEff_EE", 6)
out["OutcomeExpectancy"] = mean_items("OE_OE", 8, rev=[7, 8])
out["RiskPerception"] = mean_items("RP_RP", 5)
out["ActionPlanning"] = mean_items("ActiePlanning_AP", 3, rev=[3])
out["CopingPlanning"] = mean_items("CopingPlanning_CP", 2)
out["SelfMonitoring"] = mean_items("ZelfMonitoring_SM", 3)

# Motivation (extrinsic = items 1-2, intrinsic = items 3-5)
mot = {i: pd.to_numeric(df.get(f"Motivatie_MOT{i}"), errors="coerce") for i in range(1, 6)}
out["MotivationExtrinsic"] = (mot[1] + mot[2]) / 2
out["MotivationIntrinsic"] = (mot[3] + mot[4] + mot[5]) / 3

# Round numeric columns sensibly.
num = out.select_dtypes("number").columns
out[num] = out[num].round(3)

out = out.sort_values("token").reset_index(drop=True)
out.to_csv(paths.PERSON_LEVEL, index=False)

print(f"person_level.csv written: {out.shape[0]} participants x {out.shape[1]} cols")
print(out[["token", "POAMP_Avoidance", "POAMP_Overdoing", "POAMP_Pacing",
           "age", "BMI", "TSK_sum"]].describe(include="all").round(2).to_string())
