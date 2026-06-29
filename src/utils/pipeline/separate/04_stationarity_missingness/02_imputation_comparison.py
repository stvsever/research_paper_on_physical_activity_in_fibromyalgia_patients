"""Stage 04b - Missing-data handling: imputation sensitivity comparison.

The primary models use available-case (pairwise) handling within each VAR equation, which is
appropriate under the missing-at-random evidence reported in stage 04 (objective activity
missingness is unrelated to momentary pain, fatigue, or stress). This script documents that
decision quantitatively by benchmarking a broad set of imputation strategies that span the
two families used in intensive longitudinal research:

  Univariate time-series imputation (imputeTS toolkit; Moritz & Bartz-Beielstein, 2017):
    person mean, person median, last observation carried forward, linear interpolation, and
    Kalman state-space (local-level / structural) smoothing.
  Multivariate imputation that borrows strength across the concurrent measures:
    k-nearest-neighbours, multivariate imputation by chained equations (MICE, Bayesian ridge),
    and a random-forest chained imputer (missForest-style).

Three questions are addressed and exported for the supplementary figure and table:
  1. How accurately does each method reconstruct values that are held out at random from the
     observed series (within-person standardized RMSE, MAE, and correlation), overall and by
     measure?
  2. How much does fully substituting each imputation move the pooled descriptive moments
     (mean and SD) away from the available-case values?
  3. What does each method do to a concrete within-person series with an induced gap?
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
import paths  # noqa: E402

warnings.simplefilter("ignore")

CORE = ["PIJN", "MOE", "STRESS", "ENMO_log"]
NICE = {"PIJN": "Pain", "MOE": "Fatigue", "STRESS": "Stress", "ENMO_log": "Activity"}
RNG = np.random.default_rng(2024)
HOLDOUT = 0.20  # fraction of interior observed points masked for reconstruction scoring

# method key -> (display label, family). Order controls table/figure ordering.
METHODS = [
    ("mean", "Mean", "univariate"),
    ("median", "Median", "univariate"),
    ("locf", "LOCF", "univariate"),
    ("linear", "Linear interpolation", "univariate"),
    ("kalman", "Kalman (structural)", "univariate"),
    ("knn", "KNN", "multivariate"),
    ("mice", "MICE (chained eq.)", "multivariate"),
    ("missforest", "missForest (random forest)", "multivariate"),
]
UNIVARIATE = {k for k, _, fam in METHODS if fam == "univariate"}
MULTIVARIATE = {k for k, _, fam in METHODS if fam == "multivariate"}


# --- univariate fillers (imputeTS-style) -------------------------------------
def _interp_fill(y):
    return pd.Series(y).interpolate(method="linear", limit_direction="both").to_numpy()


def _locf_fill(y):
    return pd.Series(y).ffill().bfill().to_numpy()


def _kalman_fill(y):
    import statsmodels.api as sm

    out = y.copy()
    mask = np.isnan(out)
    if mask.sum() == 0:
        return out
    try:
        res = sm.tsa.UnobservedComponents(out, level="local level").fit(disp=False, maxiter=80)
        out[mask] = np.asarray(res.smoothed_state[0])[mask]
    except Exception:
        out = _interp_fill(out)
    if np.isnan(out).any():
        out = _interp_fill(out)
    return out


def _impute_uni(y, method):
    out = y.copy()
    mask = np.isnan(out)
    if mask.sum() == 0:
        return out
    if method == "mean":
        out[mask] = np.nanmean(out)
    elif method == "median":
        out[mask] = np.nanmedian(out)
    elif method == "locf":
        out = _locf_fill(out)
    elif method == "linear":
        out = _interp_fill(out)
    elif method == "kalman":
        out = _kalman_fill(out)
    return out


# --- multivariate fillers ----------------------------------------------------
def _impute_multi(X, method, col_means):
    """Impute a per-person matrix (rows x CORE) using the concurrent measures.

    A within-person time index is appended as an extra predictor so the multivariate
    learners can also exploit temporal position, not only the other measures.
    """
    from sklearn.experimental import enable_iterative_imputer  # noqa: F401
    from sklearn.impute import IterativeImputer, KNNImputer
    from sklearn.linear_model import BayesianRidge
    from sklearn.ensemble import RandomForestRegressor

    out = X.copy()
    for j in range(out.shape[1]):  # guard fully missing columns
        if np.isnan(out[:, j]).all():
            out[:, j] = col_means[j]
    if not np.isnan(out).any():
        return out
    tcol = np.arange(len(out)).reshape(-1, 1) / max(len(out) - 1, 1)
    aug = np.hstack([out, tcol])
    try:
        if method == "knn":
            imp = KNNImputer(n_neighbors=5, weights="distance")
        elif method == "mice":
            imp = IterativeImputer(estimator=BayesianRidge(), max_iter=15, random_state=0)
        elif method == "missforest":
            imp = IterativeImputer(
                estimator=RandomForestRegressor(n_estimators=40, max_depth=8, n_jobs=1,
                                                random_state=0),
                max_iter=5, random_state=0)
        filled = imp.fit_transform(aug)[:, :out.shape[1]]
    except Exception:
        filled = out
        for j in range(filled.shape[1]):
            m = np.isnan(filled[:, j])
            filled[m, j] = np.nanmean(filled[:, j]) if not np.isnan(filled[:, j]).all() else col_means[j]
    return filled


def _score(store, pred, truth, mu, sd):
    """Score a held-out reconstruction. Errors are SD-standardized; the stored values for
    the correlation are also person-mean centred, so the held-out r reflects within-person
    fidelity (tracking momentary fluctuations) rather than between-person level."""
    e = (pred - truth) / sd
    store["sqerr"].extend((e ** 2).tolist())
    store["abserr"].extend(np.abs(e).tolist())
    store["true"].extend(((truth - mu) / sd).tolist())
    store["pred"].extend(((pred - mu) / sd).tolist())


def _run_lengths(y):
    """Lengths of consecutive-missing runs in a series."""
    out, run = [], 0
    for v in np.isnan(y):
        if v:
            run += 1
        elif run:
            out.append(run); run = 0
    if run:
        out.append(run)
    return out


def main() -> None:
    paths.ensure_dirs()
    ema = pd.read_csv(paths.EMA_LONG).sort_values(["pid", "obs"]).reset_index(drop=True)

    # ---- missingness per measure + gap run-length structure ----
    n_total = len(ema)
    miss = pd.DataFrame([{
        "Measure": NICE[v],
        "Observed": int(ema[v].notna().sum()),
        "Missing": n_total - int(ema[v].notna().sum()),
        "% missing": round(100 * (n_total - int(ema[v].notna().sum())) / n_total, 1),
    } for v in CORE])
    miss.to_csv(paths.RESULTS_TABLES / "04_missingness_by_measure.csv", index=False)

    runs = []
    for v in CORE:
        for _, g in ema.groupby("pid"):
            for rl in _run_lengths(g[v].to_numpy(float)):
                runs.append({"Measure": NICE[v], "run_length": rl})
    runs = pd.DataFrame(runs)
    (runs.groupby(["Measure", "run_length"]).size().rename("count").reset_index()
     ).to_csv(paths.RESULTS_TABLES / "04_gap_runlengths.csv", index=False)

    ac = {v: (ema[v].dropna().mean(), ema[v].dropna().std(ddof=1)) for v in CORE}
    col_means = np.array([ac[v][0] for v in CORE])

    recon = {k: {"sqerr": [], "abserr": [], "true": [], "pred": []} for k, _, _ in METHODS}
    by_var = {(k, v): {"sqerr": [], "true": [], "pred": []}
              for k, _, _ in METHODS for v in CORE}
    pooled_full = {k: {v: [] for v in CORE} for k, _, _ in METHODS}

    for _, g in ema.groupby("pid"):
        g = g.sort_values("obs")
        X = g[CORE].to_numpy(dtype=float)
        sds = {}
        for j, v in enumerate(CORE):
            col = X[:, j]
            if (~np.isnan(col)).sum() >= 8 and np.nanstd(col, ddof=1) > 0:
                sds[v] = np.nanstd(col, ddof=1)

        # moment stability: impute every gap on the original scale
        for j, v in enumerate(CORE):
            if np.isnan(X[:, j]).all():
                continue
            for k in UNIVARIATE:
                pooled_full[k][v].append(_impute_uni(X[:, j].copy(), k))
        for k in MULTIVARIATE:
            Xf = _impute_multi(X.copy(), k, col_means)
            for j, v in enumerate(CORE):
                if not np.isnan(X[:, j]).all():
                    pooled_full[k][v].append(Xf[:, j])

        # held-out reconstruction: mask interior observed points of one measure at a time
        for j, v in enumerate(CORE):
            if v not in sds:
                continue
            col = X[:, j]
            obs_idx = np.where(~np.isnan(col))[0]
            interior = obs_idx[(obs_idx > obs_idx.min()) & (obs_idx < obs_idx.max())]
            if len(interior) < 3:
                continue
            masked = RNG.choice(interior, size=max(1, int(round(HOLDOUT * len(interior)))),
                                replace=False)
            truth = col[masked]
            mu, sd = np.nanmean(col), sds[v]
            for k in UNIVARIATE:
                tr = col.copy(); tr[masked] = np.nan
                pred = _impute_uni(tr, k)[masked]
                _score(recon[k], pred, truth, mu, sd)
                by_var[(k, v)]["sqerr"].extend((((pred - truth) / sd) ** 2).tolist())
                by_var[(k, v)]["true"].extend(((truth - mu) / sd).tolist())
                by_var[(k, v)]["pred"].extend(((pred - mu) / sd).tolist())
            for k in MULTIVARIATE:
                Xtr = X.copy(); Xtr[masked, j] = np.nan
                pred = _impute_multi(Xtr, k, col_means)[masked, j]
                _score(recon[k], pred, truth, mu, sd)
                by_var[(k, v)]["sqerr"].extend((((pred - truth) / sd) ** 2).tolist())
                by_var[(k, v)]["true"].extend(((truth - mu) / sd).tolist())
                by_var[(k, v)]["pred"].extend(((pred - mu) / sd).tolist())

    # ---- overall comparison table ----
    rows = []
    for k, label, fam in METHODS:
        rmse = float(np.sqrt(np.mean(recon[k]["sqerr"])))
        mae = float(np.mean(recon[k]["abserr"]))
        r = float(np.corrcoef(recon[k]["true"], recon[k]["pred"])[0, 1])
        dmu, dsd = [], []
        for v in CORE:
            if not pooled_full[k][v]:
                continue
            pooled = np.concatenate(pooled_full[k][v])
            mu0, sd0 = ac[v]
            dmu.append(abs(pooled.mean() - mu0) / sd0)
            dsd.append(abs(pooled.std(ddof=1) - sd0) / sd0 * 100)
        rows.append({"Method": label, "Type": fam.capitalize(),
                     "Std. RMSE": round(rmse, 3), "Std. MAE": round(mae, 3),
                     "r (held-out)": round(r, 3),
                     "Mean shift (SD)": round(float(np.mean(dmu)), 3),
                     "SD change (%)": round(float(np.mean(dsd)), 1)})
    comp = pd.DataFrame(rows)
    comp.to_csv(paths.RESULTS_TABLES / "04_imputation_comparison.csv", index=False)

    # ---- by-measure reconstruction RMSE (method x measure) ----
    bv = []
    for k, label, _ in METHODS:
        for v in CORE:
            s = by_var[(k, v)]["sqerr"]
            r = (np.corrcoef(by_var[(k, v)]["true"], by_var[(k, v)]["pred"])[0, 1]
                 if len(s) > 2 else np.nan)
            bv.append({"Method": label, "Measure": NICE[v],
                       "rmse": round(float(np.sqrt(np.mean(s))), 3) if s else np.nan,
                       "r": round(float(r), 3)})
    pd.DataFrame(bv).to_csv(paths.RESULTS_TABLES / "04_imputation_by_variable.csv", index=False)

    # ---- illustrative reconstruction on one within-person series ----
    _export_example(ema, col_means)

    print("Missingness by measure:\n", miss.to_string(index=False))
    print("\nImputation comparison (held-out reconstruction, averaged over measures):")
    print(comp.to_string(index=False))
    print("\nStage 04b imputation comparison complete.")


def _export_example(ema, col_means):
    """Induce one contiguous gap in a long, clean activity series and record every
    method's reconstruction, for the illustrative panel."""
    target = "ENMO_log"
    j = CORE.index(target)
    best_pid, best_len = None, 0
    for pid, g in ema.groupby("pid"):
        n = g[target].notna().sum()
        if n > best_len:
            best_pid, best_len = pid, n
    g = ema[ema["pid"] == best_pid].sort_values("obs").reset_index(drop=True)
    X = g[CORE].to_numpy(float)
    col = X[:, j].copy()
    obs_idx = np.where(~np.isnan(col))[0]
    lo, hi = obs_idx.min(), obs_idx.max()
    start = lo + (hi - lo) // 2 - 3
    masked = np.array([i for i in range(start, start + 6) if not np.isnan(col[i])])

    out = pd.DataFrame({"obs": np.arange(len(col)), "y_true": col})
    out["is_masked"] = out["obs"].isin(masked)
    for k in UNIVARIATE:
        tr = col.copy(); tr[masked] = np.nan
        out[k] = _impute_uni(tr, k)
    for k in MULTIVARIATE:
        Xtr = X.copy(); Xtr[masked, j] = np.nan
        out[k] = _impute_multi(Xtr, k, col_means)[:, j]
    out.attrs = {}
    out.to_csv(paths.RESULTS_TABLES / "04_imputation_example.csv", index=False)


if __name__ == "__main__":
    main()
