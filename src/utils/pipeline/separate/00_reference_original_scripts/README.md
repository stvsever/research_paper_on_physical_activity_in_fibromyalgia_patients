# 00 - Reference: original author scripts (read-only)

Verbatim copies of Annick De Paepe's original R scripts, kept for provenance. They are
**not** part of the runnable pipeline (they use absolute Windows paths and SPSS reads).

- `ORIGINAL_data_start_merge.R` - baseline scoring + merge with SEMA/Axivity (reimplemented
  in stage 01 Python).
- `ORIGINAL_analysisEMA.R` - exclusions, variance decomposition, and lagged mixed models
  (reimplemented/extended in stages 01, 03, 05).

The current pipeline reproduces the original sample (N = 34, 1894 triggers) and variance
results, then extends them with the network analyses.
