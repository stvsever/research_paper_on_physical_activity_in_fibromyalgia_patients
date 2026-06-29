"""Stage 01.2 - Build the analysis-ready long-format EMA dataset.

Reads the trigger-level export, cleans the missingness markers, coerces variable types,
applies the documented participant exclusions, derives the time structure required by the
multilevel VAR (beep within day, day within person), and transforms the right-skewed ENMO
activity measure.

Outputs:
  - src/data/processed/ema_long.csv      (one row per trigger, analytic sample)
  - src/data/processed/exclusion_log.csv (audit trail of excluded participants)
  - src/data/processed/analytic_tokens.csv
and adds an ``in_analytic_sample`` flag to person_level.csv.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
import paths  # noqa: E402

paths.ensure_dirs()

MISSING_TOKENS = {"<no-response>", "<not-shown>", "<NA>", "", "nan", "NaN", "NA"}

# Documented exclusions (reasons taken from Annick De Paepe's original analysis script).
EXCLUSIONS = {
    "wo0382925": "No Axivity (objective PA) data available",
    "wo0058851": "Only partial recording (data until 12 Dec only)",
    "wo0087912": "Only one completed EMA prompt",
    "wo0162331": "Did not participate (COVID-19)",
    "wo0327640": "Responded to <1/3 of prompts",
    "wo0193167": "Responded to <1/3 of prompts",
}

CONTINUOUS = ["PIJN", "MOE", "STRESS", "EIGENEFF", "INTENTIE", "UITKOMSTVERW",
              "SPEED", "PIECES", "BREAKS", "ACT_STOP_SCHA"]
BINARY = ["MOGELIJKHEID_BEW", "ACTIVITEITEN", "TOEK_ACT", "ACT_STOP", "ALLEEN"]


def clean_numeric(s: pd.Series) -> pd.Series:
    s = s.astype(str).str.strip()
    s = s.where(~s.isin(MISSING_TOKENS), np.nan)
    return pd.to_numeric(s, errors="coerce")


def main() -> None:
    df = pd.read_excel(paths.RAW_EMA_XLSX, sheet_name=0)
    df["token"] = df["token"].astype(str).str.strip()

    n_tokens_raw = df["token"].nunique()

    # --- type coercion --------------------------------------------------------
    for c in CONTINUOUS + BINARY:
        if c in df.columns:
            df[c] = clean_numeric(df[c])

    df["ENMO"] = pd.to_numeric(df["trigger_120_ENMO"], errors="coerce")
    df["nonwear_min"] = pd.to_numeric(df["trigger_120_nonwear_detected"], errors="coerce")

    df["completed"] = df["COMPLETED_TS"].notna()

    # --- time structure -------------------------------------------------------
    df["day"] = pd.to_numeric(df["Day"], errors="coerce").astype("Int64")
    df["beep"] = pd.to_numeric(df["Trigger_EMA"], errors="coerce").astype("Int64")
    df = df.sort_values(["token", "day", "beep"]).reset_index(drop=True)
    # Sequential observation index per person (1..n).
    df["obs"] = df.groupby("token").cumcount() + 1

    # Calendar day type from the trigger date (0 = Monday .. 6 = Sunday).
    trig_dt = pd.to_datetime(df.get("trigger_TS_date"), errors="coerce")
    df["weekday"] = trig_dt.dt.dayofweek.astype("Int64")
    df["is_weekend"] = (trig_dt.dt.dayofweek >= 5).astype("Int64")

    # --- ENMO transformations (right-skewed; strictly positive) ---------------
    df["ENMO_log"] = np.log(df["ENMO"])
    df["ENMO_sqrt"] = np.sqrt(df["ENMO"])

    # --- exclusions -----------------------------------------------------------
    present = set(df["token"].unique())
    rows = []
    for tok, reason in EXCLUSIONS.items():
        rows.append({
            "token": tok,
            "reason": reason,
            "present_in_trigger_file": tok in present,
            "n_completed": int(df.loc[df["token"] == tok, "completed"].sum())
            if tok in present else 0,
        })
    excl_log = pd.DataFrame(rows)
    excl_log.to_csv(paths.EXCLUSION_LOG, index=False)

    excluded_present = [t for t in EXCLUSIONS if t in present]
    analytic = df[~df["token"].isin(EXCLUSIONS.keys())].copy()
    analytic_tokens = sorted(analytic["token"].unique())

    # Anonymous sequential participant id (P01 ...), stable by token order.
    id_map = {t: f"P{idx + 1:02d}" for idx, t in enumerate(analytic_tokens)}
    analytic["pid"] = analytic["token"].map(id_map)

    # --- select and order analytic columns ------------------------------------
    keep = ["pid", "token", "day", "beep", "obs", "weekday", "is_weekend", "completed",
            "PIJN", "MOE", "STRESS",
            "ENMO", "ENMO_log", "ENMO_sqrt", "nonwear_min",
            "MOGELIJKHEID_BEW", "ACTIVITEITEN",
            "EIGENEFF", "INTENTIE", "UITKOMSTVERW", "TOEK_ACT",
            "SPEED", "PIECES", "BREAKS", "ACT_STOP", "ACT_STOP_SCHA",
            "WAAR", "ALLEEN"]
    keep = [c for c in keep if c in analytic.columns]
    ema = analytic[keep].copy()
    ema = ema.sort_values(["pid", "day", "beep"]).reset_index(drop=True)
    ema.to_csv(paths.EMA_LONG, index=False)

    pd.DataFrame({"token": analytic_tokens,
                  "pid": [id_map[t] for t in analytic_tokens]}).to_csv(
        paths.DATA_PROCESSED / "analytic_tokens.csv", index=False)

    # --- flag analytic sample in person_level.csv -----------------------------
    if paths.PERSON_LEVEL.exists():
        pl = pd.read_csv(paths.PERSON_LEVEL)
        pl["in_analytic_sample"] = pl["token"].isin(analytic_tokens)
        pl["pid"] = pl["token"].map(id_map)
        pl.to_csv(paths.PERSON_LEVEL, index=False)

    # --- report ---------------------------------------------------------------
    comp = ema.groupby("pid")["completed"].sum()
    print("=" * 66)
    print("EMA preprocessing summary")
    print("=" * 66)
    print(f"tokens in raw trigger file : {n_tokens_raw}")
    print(f"excluded (present)         : {len(excluded_present)} -> {excluded_present}")
    print(f"analytic participants      : {len(analytic_tokens)}")
    print(f"analytic trigger rows      : {len(ema)}")
    print(f"completed prompts          : total {int(ema['completed'].sum())}, "
          f"per person median {comp.median():.0f} "
          f"(mean {comp.mean():.1f}, range {comp.min()}-{comp.max()})")
    print(f"ENMO available (rows)      : {ema['ENMO'].notna().sum()} "
          f"({100 * ema['ENMO'].notna().mean():.1f}%)")
    cant = ema["MOGELIJKHEID_BEW"].eq(0)
    able_known = ema["MOGELIJKHEID_BEW"].notna()
    print(f"'could not move' prompts   : {int(cant.sum())} "
          f"({100 * cant.sum() / able_known.sum():.1f}% of answered)")
    print("\nexclusion_log.csv:")
    print(excl_log.to_string(index=False))


if __name__ == "__main__":
    main()
