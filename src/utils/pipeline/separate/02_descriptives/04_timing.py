"""Stage 02d - EMA protocol timing audit.

Reads the raw trigger-level export and summarizes the practical timing features of the
EMA protocol: trigger availability, scheduled clock times, adjacent-prompt spacing,
response latency, questionnaire duration, and weekday/weekend completion. Outputs feed the
timing supplementary figure.
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


def _clock_hour(s: pd.Series) -> pd.Series:
    return s.dt.hour + s.dt.minute / 60 + s.dt.second / 3600


def _clean_latency_minutes(started: pd.Series, scheduled: pd.Series) -> pd.Series:
    latency = (started - scheduled).dt.total_seconds() / 60
    # One row is -1 min, consistent with minute-level timestamp rounding or clock sync.
    # Latency cannot be negative, so truncate at zero for descriptive summaries.
    return latency.clip(lower=0)


def _gee_term_p(formula: str, data: pd.DataFrame, term: str, family) -> float:
    try:
        fit = smf.gee(
            formula,
            groups="pid",
            data=data,
            cov_struct=sm.cov_struct.Exchangeable(),
            family=family,
        ).fit()
        table = fit.wald_test_terms(skip_single=False).table
        return float(table.loc[term, "pvalue"])
    except Exception:
        return np.nan


def _gee_coef(formula: str, data: pd.DataFrame, coef: str, family) -> dict:
    try:
        fit = smf.gee(
            formula,
            groups="pid",
            data=data,
            cov_struct=sm.cov_struct.Exchangeable(),
            family=family,
        ).fit()
        return {
            "estimate": float(fit.params[coef]),
            "se": float(fit.bse[coef]),
            "p": float(fit.pvalues[coef]),
        }
    except Exception:
        return {"estimate": np.nan, "se": np.nan, "p": np.nan}


def _summary_row(metric: str, values: pd.Series) -> dict:
    s = pd.to_numeric(values, errors="coerce").dropna()
    return {
        "metric": metric,
        "n": int(s.size),
        "mean": round(float(s.mean()), 3) if s.size else np.nan,
        "sd": round(float(s.std(ddof=1)), 3) if s.size > 1 else np.nan,
        "median": round(float(s.median()), 3) if s.size else np.nan,
        "q1": round(float(s.quantile(.25)), 3) if s.size else np.nan,
        "q3": round(float(s.quantile(.75)), 3) if s.size else np.nan,
        "min": round(float(s.min()), 3) if s.size else np.nan,
        "max": round(float(s.max()), 3) if s.size else np.nan,
    }


def main() -> None:
    token_map = pd.read_csv(paths.DATA_PROCESSED / "analytic_tokens.csv")
    raw = pd.read_excel(paths.RAW_EMA_XLSX, sheet_name=0)
    raw["token"] = raw["token"].astype(str).str.strip()
    raw = raw[raw["token"].isin(token_map["token"])].copy()
    raw = raw.merge(token_map, on="token", how="left")

    for col in ["SCHEDULED_TS", "STARTED_TS", "COMPLETED_TS", "EXPIRED_TS"]:
        raw[col] = pd.to_datetime(raw[col], errors="coerce")

    raw["day"] = pd.to_numeric(raw["Day"], errors="coerce")
    raw["beep"] = pd.to_numeric(raw["Trigger_EMA"], errors="coerce")
    raw = raw.dropna(subset=["day", "beep"]).copy()
    raw["day"] = raw["day"].astype(int)
    raw["beep"] = raw["beep"].astype(int)
    raw = raw.sort_values(["pid", "day", "beep"]).reset_index(drop=True)

    raw["completed"] = raw["COMPLETED_TS"].notna().astype(int)
    raw["scheduled_hour"] = _clock_hour(raw["SCHEDULED_TS"])
    raw["weekday"] = raw["SCHEDULED_TS"].dt.dayofweek.astype("Int64")
    raw["is_weekend"] = (raw["weekday"] >= 5).astype(int)
    raw["start_latency_min"] = _clean_latency_minutes(raw["STARTED_TS"], raw["SCHEDULED_TS"])
    raw["completion_duration_min"] = (
        raw["COMPLETED_TS"] - raw["STARTED_TS"]
    ).dt.total_seconds() / 60
    raw["completion_after_scheduled_min"] = (
        raw["COMPLETED_TS"] - raw["SCHEDULED_TS"]
    ).dt.total_seconds() / 60
    raw["scheduled_interval_min"] = (
        raw.groupby(["pid", "day"])["SCHEDULED_TS"].diff().dt.total_seconds() / 60
    )
    raw["interval_label"] = (raw["beep"] - 1).astype(str) + "-" + raw["beep"].astype(str)

    expected_lo = {1: 10.0, 2: 12.5, 3: 15.0, 4: 17.5}
    expected_hi = {1: 10.5, 2: 13.0, 3: 15.5, 4: 18.0}
    raw["expected_lo"] = raw["beep"].map(expected_lo)
    raw["expected_hi"] = raw["beep"].map(expected_hi)
    raw["within_beep_window"] = (
        raw["scheduled_hour"].ge(raw["expected_lo"])
        & raw["scheduled_hour"].le(raw["expected_hi"])
    )
    raw["within_10_18"] = raw["scheduled_hour"].between(10, 18, inclusive="both")

    long_cols = [
        "pid", "day", "beep", "completed", "scheduled_hour", "weekday", "is_weekend",
        "start_latency_min", "completion_duration_min", "completion_after_scheduled_min",
        "scheduled_interval_min", "interval_label", "within_beep_window", "within_10_18",
    ]
    raw[long_cols].to_csv(paths.RESULTS_TABLES / "02_timing_long.csv", index=False)

    n_pid = raw["pid"].nunique()
    summary = pd.DataFrame([
        _summary_row("Scheduled clock time (hours after midnight)", raw["scheduled_hour"]),
        _summary_row("Adjacent-prompt interval (minutes)", raw["scheduled_interval_min"]),
        _summary_row("Response latency, scheduled to started (minutes)", raw["start_latency_min"]),
        _summary_row("Questionnaire duration, started to completed (minutes)", raw["completion_duration_min"]),
        _summary_row("Completion latency, scheduled to completed (minutes)", raw["completion_after_scheduled_min"]),
    ])
    extra = pd.DataFrame([
        {"metric": "Analytic participants", "n": n_pid, "mean": np.nan, "sd": np.nan,
         "median": np.nan, "q1": np.nan, "q3": np.nan, "min": np.nan, "max": np.nan},
        {"metric": "Expected trigger rows", "n": int(n_pid * 14 * 4), "mean": np.nan,
         "sd": np.nan, "median": np.nan, "q1": np.nan, "q3": np.nan, "min": np.nan,
         "max": np.nan},
        {"metric": "Observed trigger rows", "n": int(len(raw)), "mean": np.nan,
         "sd": np.nan, "median": np.nan, "q1": np.nan, "q3": np.nan, "min": np.nan,
         "max": np.nan},
        {"metric": "Completed trigger rows", "n": int(raw["completed"].sum()), "mean": np.nan,
         "sd": np.nan, "median": np.nan, "q1": np.nan, "q3": np.nan, "min": np.nan,
         "max": np.nan},
        {"metric": "Rows outside scheduled beep window", "n": int((~raw["within_beep_window"]).sum()),
         "mean": round(float((~raw["within_beep_window"]).mean() * 100), 3), "sd": np.nan,
         "median": np.nan, "q1": np.nan, "q3": np.nan, "min": np.nan, "max": np.nan},
        {"metric": "Rows outside 10:00-18:00 scheduled range", "n": int((~raw["within_10_18"]).sum()),
         "mean": round(float((~raw["within_10_18"]).mean() * 100), 3), "sd": np.nan,
         "median": np.nan, "q1": np.nan, "q3": np.nan, "min": np.nan, "max": np.nan},
    ])
    pd.concat([extra, summary], ignore_index=True).to_csv(
        paths.RESULTS_TABLES / "02_timing_summary.csv", index=False
    )

    by_prompt = (
        raw.groupby("beep")
        .agg(
            n=("pid", "size"),
            completed=("completed", "sum"),
            completion_rate=("completed", "mean"),
            scheduled_hour_mean=("scheduled_hour", "mean"),
            scheduled_hour_sd=("scheduled_hour", "std"),
            scheduled_hour_min=("scheduled_hour", "min"),
            scheduled_hour_max=("scheduled_hour", "max"),
            median_latency_min=("start_latency_min", "median"),
            mean_latency_min=("start_latency_min", "mean"),
            median_duration_min=("completion_duration_min", "median"),
            mean_duration_min=("completion_duration_min", "mean"),
        )
        .reset_index()
    )
    by_prompt["completion_rate"] *= 100
    by_prompt.round(3).to_csv(paths.RESULTS_TABLES / "02_timing_by_prompt.csv", index=False)

    intervals = (
        raw.loc[raw["beep"].isin([2, 3, 4])]
        .dropna(subset=["scheduled_interval_min"])
        .groupby("interval_label")["scheduled_interval_min"]
        .agg(["count", "mean", "std", "median", "min", "max"])
        .reset_index()
    )
    intervals.round(3).to_csv(paths.RESULTS_TABLES / "02_timing_intervals.csv", index=False)

    daily = (
        raw.groupby("day")
        .agg(observed_triggers=("pid", "size"), completed=("completed", "sum"))
        .reset_index()
    )
    daily["expected_triggers"] = n_pid * 4
    daily["missing_trigger_rows"] = daily["expected_triggers"] - daily["observed_triggers"]
    daily.to_csv(paths.RESULTS_TABLES / "02_timing_daily_counts.csv", index=False)

    daytype = (
        raw.groupby(["pid", "is_weekend"])["completed"]
        .mean()
        .mul(100)
        .reset_index(name="completion_pct")
    )
    daytype["day_type"] = daytype["is_weekend"].map({0: "Weekday", 1: "Weekend"})
    daytype.to_csv(paths.RESULTS_TABLES / "02_timing_daytype_person.csv", index=False)
    wide = daytype.pivot(index="pid", columns="is_weekend", values="completion_pct").dropna()
    try:
        w_stat, w_p = stats.wilcoxon(wide[1], wide[0], zero_method="wilcox")
    except ValueError:
        w_stat, w_p = np.nan, np.nan

    tests = []
    tests.append({
        "test": "completion_by_prompt_global",
        "model": "Binomial GEE, completed ~ C(beep), participant clustered",
        "statistic": np.nan,
        "p": _gee_term_p("completed ~ C(beep)", raw, "C(beep)", sm.families.Binomial()),
    })
    tests.append({
        "test": "completion_by_weekend",
        "model": "Binomial GEE, completed ~ is_weekend, participant clustered",
        **_gee_coef("completed ~ is_weekend", raw, "is_weekend", sm.families.Binomial()),
    })
    tests.append({
        "test": "completion_weekend_paired",
        "model": "Paired Wilcoxon signed-rank on participant completion percentages",
        "statistic": round(float(w_stat), 3) if not pd.isna(w_stat) else np.nan,
        "p": round(float(w_p), 4) if not pd.isna(w_p) else np.nan,
    })
    for metric, formula, term in [
        ("response_latency_by_prompt", "start_latency_min ~ C(beep)", "C(beep)"),
        ("questionnaire_duration_by_prompt", "completion_duration_min ~ C(beep)", "C(beep)"),
    ]:
        d = raw.dropna(subset=[formula.split(" ~ ")[0]]).copy()
        groups = [g[formula.split(" ~ ")[0]].values for _, g in d.groupby("beep")]
        h, p = stats.kruskal(*groups)
        tests.append({
            "test": metric,
            "model": "Gaussian GEE global prompt effect plus Kruskal-Wallis check",
            "statistic": round(float(h), 3),
            "p": _gee_term_p(formula, d, term, sm.families.Gaussian()),
            "kruskal_p": round(float(p), 4),
        })
    d_int = raw.loc[raw["beep"].isin([2, 3, 4])].dropna(subset=["scheduled_interval_min"]).copy()
    int_groups = [g["scheduled_interval_min"].values for _, g in d_int.groupby("interval_label")]
    h_int, p_int = stats.kruskal(*int_groups)
    tests.append({
        "test": "adjacent_prompt_interval_by_pair",
        "model": "Gaussian GEE global interval-pair effect plus Kruskal-Wallis check",
        "statistic": round(float(h_int), 3),
        "p": _gee_term_p(
            "scheduled_interval_min ~ C(interval_label)",
            d_int,
            "C(interval_label)",
            sm.families.Gaussian(),
        ),
        "kruskal_p": round(float(p_int), 4),
    })
    person = (
        raw.groupby("pid")
        .agg(
            completion_pct=("completed", lambda s: 100 * s.mean()),
            mean_latency_min=("start_latency_min", "mean"),
            mean_duration_min=("completion_duration_min", "mean"),
        )
        .reset_index()
    )
    rho, rho_p = stats.spearmanr(person["completion_pct"], person["mean_latency_min"],
                                 nan_policy="omit")
    tests.append({
        "test": "person_completion_vs_latency",
        "model": "Spearman correlation across participants",
        "statistic": round(float(rho), 3),
        "p": round(float(rho_p), 4),
    })
    pd.DataFrame(tests).to_csv(paths.RESULTS_TABLES / "02_timing_tests.csv", index=False)

    print("EMA timing summary:")
    print(pd.read_csv(paths.RESULTS_TABLES / "02_timing_summary.csv").to_string(index=False))
    print("\nEMA timing tests:")
    print(pd.DataFrame(tests).to_string(index=False))
    print("\nStage 02d timing audit complete.")


if __name__ == "__main__":
    main()
