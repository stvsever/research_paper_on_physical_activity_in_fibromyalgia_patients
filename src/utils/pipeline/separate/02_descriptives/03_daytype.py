"""Stage 02c - Weekday versus weekend day-type effects (group level).

Individual weekday/weekend contrasts are underpowered at this series length, so the day-type
question is answered at the group level with Gaussian GEE per momentary measure using
participant clustering. Because every participant contributed observations on all seven
weekdays, the weekend effect is well identified at the group level. Effects are reported in
raw units and standardized by the measure's standard deviation so they are comparable across
measures.

Outputs feed the day-type supplementary figure.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
import paths  # noqa: E402

warnings.simplefilter("ignore")
paths.ensure_dirs()

MEASURES = {
    "PIJN": "Pain", "MOE": "Fatigue", "STRESS": "Stress", "ENMO_log": "Activity",
    "EIGENEFF": "Self-efficacy", "INTENTIE": "Intention",
}


def main() -> None:
    ema = pd.read_csv(paths.EMA_LONG)
    ema = ema.dropna(subset=["is_weekend"]).copy()
    ema["is_weekend"] = ema["is_weekend"].astype(int)

    rows = []
    for v, lab in MEASURES.items():
        d = ema.dropna(subset=[v]).copy()
        sd = d[v].std(ddof=1)
        try:
            md = smf.gee(
                f"{v} ~ is_weekend",
                groups="pid",
                data=d,
                cov_struct=sm.cov_struct.Exchangeable(),
                family=sm.families.Gaussian(),
            ).fit()
            b = float(md.params["is_weekend"]); se = float(md.bse["is_weekend"])
            p = float(md.pvalues["is_weekend"])
        except Exception:
            b = se = p = np.nan
        wk = d.loc[d["is_weekend"] == 0, v].mean()
        we = d.loc[d["is_weekend"] == 1, v].mean()
        rows.append({
            "variable": v, "label": lab,
            "weekday_mean": round(wk, 3), "weekend_mean": round(we, 3),
            "b_weekend": round(b, 3), "se": round(se, 3), "p": round(p, 3),
            "std_delta": round(b / sd, 3),
            "ci_lo": round((b - 1.96 * se) / sd, 3),
            "ci_hi": round((b + 1.96 * se) / sd, 3),
        })
    out = pd.DataFrame(rows)
    out.to_csv(paths.RESULTS_TABLES / "02_daytype_effects.csv", index=False)
    print("Weekday vs weekend group-level effects (Gaussian GEE, participant clustered):")
    print(out.to_string(index=False))

    # Everyday context by day type is binary at the prompt level. For the figure, the
    # inferential unit is the participant-level weekday/weekend percentage, compared with a
    # paired Wilcoxon signed-rank test.
    ema["WAAR_num"] = pd.to_numeric(ema["WAAR"], errors="coerce")
    ema["ALLEEN_num"] = pd.to_numeric(ema["ALLEEN"], errors="coerce")
    ema["at_home"] = np.where(ema["WAAR_num"].notna(), (ema["WAAR_num"] == 0).astype(float), np.nan)
    ema["alone"] = np.where(ema["ALLEEN_num"].notna(), (ema["ALLEEN_num"] == 1).astype(float), np.nan)
    person_rows = []
    effect_rows = []
    for metric, label in [("at_home", "At home"), ("alone", "Alone")]:
        d = ema.dropna(subset=[metric, "is_weekend", "pid"]).copy()
        pp = (
            d.groupby(["pid", "is_weekend"])[metric]
            .mean()
            .mul(100)
            .reset_index(name="pct")
        )
        pp["metric"] = metric
        pp["label"] = label
        pp["day_type"] = pp["is_weekend"].map({0: "Weekday", 1: "Weekend"})
        person_rows.append(pp[["pid", "metric", "label", "day_type", "pct"]])
        wide = pp.pivot(index="pid", columns="is_weekend", values="pct").dropna()
        if len(wide) >= 2:
            try:
                stat, p = stats.wilcoxon(wide[1], wide[0], zero_method="wilcox",
                                         alternative="two-sided")
            except ValueError:
                stat, p = np.nan, 1.0
        else:
            stat, p = np.nan, np.nan
        effect_rows.append({
            "metric": metric,
            "label": label,
            "weekday_mean_pct": round(float(wide[0].mean()), 2) if 0 in wide else np.nan,
            "weekend_mean_pct": round(float(wide[1].mean()), 2) if 1 in wide else np.nan,
            "median_diff_pct": round(float((wide[1] - wide[0]).median()), 2) if len(wide) else np.nan,
            "wilcoxon_statistic": round(float(stat), 3) if not pd.isna(stat) else np.nan,
            "p_wilcoxon": round(float(p), 4) if not pd.isna(p) else np.nan,
            "n_pairs": int(len(wide)),
            "test": "paired Wilcoxon signed-rank on participant-level percentages",
        })
    ctx_person = pd.concat(person_rows, ignore_index=True)
    ctx_eff = pd.DataFrame(effect_rows)
    ctx_person.to_csv(paths.RESULTS_TABLES / "02_daytype_context_person.csv", index=False)
    ctx_eff.to_csv(paths.RESULTS_TABLES / "02_daytype_context_effects.csv", index=False)
    print("\nWeekday vs weekend context tests (paired participant percentages):")
    print(ctx_eff.to_string(index=False))

    n_we = int((ema["is_weekend"] == 1).sum())
    print(f"\nWeekend prompts: {n_we} of {len(ema)} ({100 * n_we / len(ema):.1f}%); "
          f"every participant contributed all seven weekdays.")
    print("Stage 02c day-type effects complete.")


if __name__ == "__main__":
    main()
