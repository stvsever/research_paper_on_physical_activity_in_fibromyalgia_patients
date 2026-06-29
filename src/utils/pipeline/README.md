# Analysis pipeline

This directory holds the full Walk On! EMA analysis as a sequence of numbered stages.

```
pipeline/
├── full/
│   └── run_all.py        # one entry point that runs every stage in order
└── separate/             # the stages, runnable individually (clean sequential numbering)
    ├── 00_reference_original_scripts/   # provenance (not executed)
    ├── 01_preprocessing/                # Python: build clean datasets
    ├── 02_descriptives/                 # Python: descriptives, compliance, correlations, context
    ├── 03_variance_decomposition/       # R (lme4): ICC / within-between variance
    ├── 04_stationarity_missingness/     # R: skew, stationarity, MNAR probe
    ├── 05_mlvar/                        # R (mlVAR): PRIMARY network model (RQ1) + residual diagnostics
    ├── 06_sgimme/                       # R (gimme): complementary S-GIMME
    ├── 07_idiographic_graphicalvar/     # R: per-person feasibility + OLS VAR coefficients
    ├── 08_poamp_subgroups/              # Python: POAM-P subgroups (RQ2)
    ├── 09_network_poamp_link/           # Python: RQ1<->RQ2 bridge
    ├── 10_robustness/                   # R: detrend, LOPO, bootstrap, extended, cant-move, threshold, transform, permutation
    ├── 11_pacing/                       # R: pacing behaviour dynamics (substantive supplement)
    └── 12_figures_tables/               # Python: MAIN_/SUP_ figures, markdown tables, LaTeX tables
```

The supplementary analyses are no longer numbered with a `9x` jump; robustness/sensitivity
work is consolidated in `10_robustness/`, the pacing supplement is `11_pacing/`, and all
visualization and table generation is the final stage `12_figures_tables/`.

## Language split (and how R is run from Python)

- **R** does the statistical models (multilevel VAR, S-GIMME, graphicalVAR, mixed models,
  variance decomposition). Each model is a standalone `.R` file.
- **Python** does preprocessing, the POAM-P subgroup/link analysis, all visualization, and
  orchestration.
- The orchestrator (`full/run_all.py`) executes each `.R` file through `Rscript` in a
  subprocess (`src/utils/lib/runr.py`). This keeps the R scripts as first-class,
  independently runnable artifacts while letting Python drive the whole workflow - the role
  played by an `rpy2`-style bridge, but more reproducible (isolated R session, exact file
  under version control, hard failure on non-zero exit).

## Run it

```bash
# everything, from raw data to figures and tables
python src/utils/pipeline/full/run_all.py

# resume from a stage, or run one stage
python src/utils/pipeline/full/run_all.py --from 05
python src/utils/pipeline/full/run_all.py --only 10
```

Each stage folder has its own `README.md` describing inputs, outputs, and the key results
to review. A consolidated review summary is in `src/results/REVIEW.md`.
