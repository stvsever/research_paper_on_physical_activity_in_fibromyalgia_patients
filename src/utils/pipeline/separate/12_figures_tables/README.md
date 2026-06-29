# Stage 12 - Figures and tables

All visualization is done in Python (matplotlib); R is never used for plotting. Figures
are 300-dpi PNGs; multi-panel figures use bold panel letters and per-panel titles with no
global suptitle.

| Script | Produces |
|--------|----------|
| `01_main_figures.py` | `paper/assets/figures/main/MAIN_01..04_*.png` |
| `02_supp_figures.py` | `paper/assets/figures/supplementary/SUP_01..15_*.png` |
| `03_tables.py` | `paper/assets/tables/MAIN_*.md` and `SUP_*.md` |

**Main figures.**
1. `MAIN_01_variance_decomposition` - within/between variance partition per measure.
2. `MAIN_02_mlvar_networks` - temporal, contemporaneous, between-person networks (RQ1 centrepiece).
3. `MAIN_03_temporal_effects_heterogeneity` - fixed-effect forest plot + per-person heterogeneity.
4. `MAIN_04_poamp_subgroups_link` - POAM-P subgroups + the Pain->Activity-by-subgroup bridge (RQ2).

**Supplementary figures.** SUP_01 design/compliance, SUP_02 EMA timing,
SUP_03 stationarity/transform, SUP_04 missingness, SUP_05 imputation,
SUP_06 idiographic feasibility, SUP_07 S-GIMME, SUP_08 extended six-node and
seven-node networks, SUP_09 can't-move sensitivity, SUP_10 pacing, SUP_11
within/between correlations, SUP_12 robustness, SUP_13 diagnostics, SUP_14
context, SUP_15 day type.

Shared drawing logic lives in `src/utils/lib/vizstyle.py` (palette/rcParams) and
`src/utils/lib/netviz.py` (network drawing).
