"""Stage 08 - POAM-P activity-pattern subgroups (RQ2).

Two complementary, deliberately exploratory views on whether participants form meaningful
subgroups by their baseline activity patterns (avoidance / overdoing / pacing):

  A. Dominant-pattern typology - each person is labelled by their highest z-scored POAM-P
     subscale (Avoider / Overdoer / Pacer). Simple, interpretable, robust at small N, and
     it maps directly onto the three POAM-P constructs Annick named.

  B. Data-driven clustering - standardize the three subscales, then k-means (k = 2..5,
     silhouette) plus a Gaussian mixture (BIC). Reported with explicit small-N caveats:
     with ~31 participants and three correlated subscales, cluster solutions are unstable
     and used only descriptively.

Outputs: per-person labels and cluster profiles in src/results/tables.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
import paths  # noqa: E402

paths.ensure_dirs()
rng = 20260626

SUB = ["POAMP_Avoidance", "POAMP_Overdoing", "POAMP_Pacing"]
SHORT = {"POAMP_Avoidance": "Avoidance", "POAMP_Overdoing": "Overdoing",
         "POAMP_Pacing": "Pacing"}

pl = pd.read_csv(paths.PERSON_LEVEL)
df = pl[pl["in_analytic_sample"] & pl[SUB].notna().all(axis=1)].copy()
print(f"Participants with complete POAM-P in analytic sample: {len(df)}")

Z = StandardScaler().fit_transform(df[SUB].values)
zdf = pd.DataFrame(Z, columns=[SHORT[c] for c in SUB], index=df.index)

# --- A. dominant-pattern typology --------------------------------------------
df["dominant_pattern"] = zdf.idxmax(axis=1).values
for c in SUB:
    df[f"z_{SHORT[c]}"] = zdf[SHORT[c]].values

# --- B. data-driven clustering -----------------------------------------------
sel = []
for k in range(2, 6):
    km = KMeans(n_clusters=k, n_init=25, random_state=rng).fit(Z)
    sil = silhouette_score(Z, km.labels_)
    gmm = GaussianMixture(n_components=k, covariance_type="full",
                          n_init=10, random_state=rng).fit(Z)
    sel.append({"k": k, "kmeans_silhouette": round(sil, 3),
                "kmeans_inertia": round(km.inertia_, 2),
                "gmm_bic": round(gmm.bic(Z), 2), "gmm_aic": round(gmm.aic(Z), 2)})
sel_df = pd.DataFrame(sel)
sel_df.to_csv(paths.RESULTS_TABLES / "08_cluster_selection.csv", index=False)
print("Cluster model selection:\n", sel_df.to_string(index=False))

best_k = int(sel_df.loc[sel_df["kmeans_silhouette"].idxmax(), "k"])
km = KMeans(n_clusters=best_k, n_init=50, random_state=rng).fit(Z)
# Order clusters by mean avoidance for stable labelling.
order = pd.Series(Z[:, 0]).groupby(km.labels_).mean().sort_values().index
relabel = {old: new for new, old in enumerate(order)}
df["cluster"] = [relabel[l] for l in km.labels_]
print(f"\nSelected k = {best_k} (max silhouette).")

# --- profiles ----------------------------------------------------------------
def profile(group_col):
    g = df.groupby(group_col)
    prof = g[SUB].mean().round(1)
    prof.columns = [SHORT[c] for c in SUB]
    prof["n"] = g.size()
    return prof.reset_index()


prof_type = profile("dominant_pattern")
prof_clust = profile("cluster")
prof_type.to_csv(paths.RESULTS_TABLES / "08_profile_dominant_type.csv", index=False)
prof_clust.to_csv(paths.RESULTS_TABLES / "08_profile_cluster.csv", index=False)
print("\nDominant-pattern profiles:\n", prof_type.to_string(index=False))
print("\nData-driven cluster profiles:\n", prof_clust.to_string(index=False))

# cross-tab of the two solutions
ct = pd.crosstab(df["dominant_pattern"], df["cluster"])
ct.to_csv(paths.RESULTS_TABLES / "08_type_by_cluster_crosstab.csv")

# per-person labels (carry POAM-P and z-scores for the link stage)
keep = ["pid", "token"] + SUB + [f"z_{SHORT[c]}" for c in SUB] + \
       ["dominant_pattern", "cluster"]
labels = df[keep].copy()
labels.to_csv(paths.DATA_PROCESSED / "poamp_subgroups.csv", index=False)
print(f"\nWrote per-person subgroup labels: {len(labels)} participants.")
print("Dominant-pattern counts:", df["dominant_pattern"].value_counts().to_dict())
print("Cluster counts:", df["cluster"].value_counts().sort_index().to_dict())
