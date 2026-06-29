# Supplementary Table S3. Missing data and imputation benchmark

Missingness by momentary measure (of 1,894 scheduled prompts) and a benchmark of univariate (imputeTS) and multivariate imputation strategies by held-out reconstruction accuracy and the resulting change in pooled descriptive moments. See Figure S5.

| Measure | Observed | Missing | % missing |
| --- | --- | --- | --- |
| Pain | 1497 | 397 | 21.0 |
| Fatigue | 1495 | 399 | 21.1 |
| Stress | 1492 | 402 | 21.2 |
| Activity | 1757 | 137 | 7.2 |

Note. The primary models use available-case (pairwise) handling within each VAR equation, consistent with the missing-at-random evidence. Multivariate methods (KNN, MICE, missForest) reconstruct held-out momentary values best; all methods leave the descriptive moments essentially unchanged (Moritz & Bartz-Beielstein, 2017).


**Imputation method comparison (held-out reconstruction)**

| Method | Type | Std. RMSE | Std. MAE | r (held-out) | Mean shift (SD) | SD change (%) |
| --- | --- | --- | --- | --- | --- | --- |
| Mean | Univariate | 1.021 | 0.801 | -0.286 | 0.014 | 3.6 |
| Median | Univariate | 1.067 | 0.771 | -0.064 | 0.026 | 2.4 |
| LOCF | Univariate | 1.321 | 0.961 | 0.117 | 0.011 | 1.6 |
| Linear interpolation | Univariate | 1.12 | 0.832 | 0.189 | 0.01 | 0.6 |
| Kalman (structural) | Univariate | 0.988 | 0.755 | 0.204 | 0.011 | 2.6 |
| KNN | Multivariate | 1.029 | 0.769 | 0.228 | 0.012 | 1.9 |
| MICE (chained eq.) | Multivariate | 0.954 | 0.73 | 0.321 | 0.012 | 3.2 |
| missForest (random forest) | Multivariate | 1.011 | 0.75 | 0.287 | 0.014 | 2.0 |
