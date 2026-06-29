# Stage 01 - Preprocessing

**Goal.** Turn the raw Teams exports into two clean, analysis-ready tables.

| Script | Language | Output |
|--------|----------|--------|
| `01_build_person_level.py` | Python | `data/processed/person_level.csv` (one row per participant: POAM-P subscales, demographics, clinical scores, social-cognitive determinants) |
| `02_build_ema_long.py` | Python | `data/processed/ema_long.csv` (one row per trigger), `exclusion_log.csv`, `analytic_tokens.csv` |

**Key decisions for review.**
- Missingness markers `<no-response>` and `<not-shown>` in the raw export are converted to `NA`.
- POAM-P items are already 0-4 in the SPSS file (no offset needed); subscales are sums (range 0-40).
- Exclusions follow Annick's documented reasons (no Axivity, partial recording, single prompt, COVID, <1/3 response). Result: **34 analytic participants**, **1894 triggers**, **1474 completed prompts** (median 44/person), **92.8% ENMO available**, **13.2% could-not-move**. This reproduces the original numbers exactly.
- A within-person standardized log transform of ENMO is added (`ENMO_log`) because raw ENMO is right-skewed (see stage 04).
- Note: 34 participants have EMA but only **31 have baseline POAM-P** (3 lack the baseline questionnaire).
