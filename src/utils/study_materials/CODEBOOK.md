# Codebook: Walk On! EMA study (Study 1)

This codebook documents the variables used in the analysis pipeline, with exact item
wording (translated from Dutch) and the coding decisions made during preprocessing.
It is the single source of truth for variable interpretation. Read it before reviewing
any model output, because the **direction** of several items matters for interpretation.

## Design

- Population: women with fibromyalgia.
- EMA schedule: 4 semi-random prompts per day for 14 days (max 56 prompts per person).
- Each prompt is referred to as a "trigger". Objective physical activity is summarized in a
  120-minute window around each trigger (`trigger_120_ENMO`).
- Baseline (`begin studie`) questionnaire collected once, before the EMA period.

## Core momentary (EMA, trigger-level) variables

| Variable | Item (translated) | Scale | Direction / notes |
|----------|-------------------|-------|-------------------|
| `PIJN` | "How much pain did you have just before the prompt?" | 0-10 NRS | Higher = more pain |
| `MOE` | "How tired were you just before the prompt?" | 0-10 NRS | Higher = more fatigue |
| `STRESS` | "How tense/stressed were you just before the prompt?" | 0-10 NRS | Higher = more stress |
| `trigger_120_ENMO` | Objective acceleration (ENMO) in the 120 min around the trigger | continuous (g) | Higher = more physical activity. Right-skewed. |
| `EIGENEFF` | "In the next two hours I am confident I can move for at least 10 minutes." | 1-5 Likert | Higher = more self-efficacy |
| `INTENTIE` | "In the next two hours I want to move for at least 10 minutes." | 1-5 Likert | Higher = more intention |
| `UITKOMSTVERW` | "It is better for my health to take it physically easy for the next 2 hours." | 1-5 Likert | **Higher = stronger rest-favoring outcome expectancy (i.e., expectancy AGAINST activity).** |
| `TOEK_ACT` | "Do you plan to do one or more movement bouts of >=10 min in the next 2 hours?" | 0/1 | 1 = plans to move |

## Movement-context and pacing variables

| Variable | Item (translated) | Scale | Direction / notes |
|----------|-------------------|-------|-------------------|
| `MOGELIJKHEID_BEW` | "I am currently in a situation that does not allow me to move." (recoded) | 0/1 | **1 = able to move, 0 = not able to move.** ~13% of completed prompts = 0. |
| `ACTIVITEITEN` | "Since the last prompt, did you do activities that involved movement?" | 0/1 | 1 = yes |
| `SPEED` | "To what extent did you deliberately do activities slower than usual?" | 0-10 | Pacing (slowing). Shown only if `ACTIVITEITEN` = yes. |
| `PIECES` | "To what extent did you deliberately break tasks into smaller, manageable parts?" | 0-10 | Pacing (chunking). Conditional. |
| `BREAKS` | "To what extent did you deliberately insert extra breaks?" | 0-10 | Pacing (resting). Conditional. |
| `ACT_STOP` | "Did you have to stop one or more activities?" | 0/1 | 1 = yes |

## Baseline person-level variables

| Variable | Description | Scoring |
|----------|-------------|---------|
| `POAMP_Avoidance` | POAM-P activity avoidance subscale | sum of items 1,6,8,11,13,16,19,22,25,28 (each 0-4) |
| `POAMP_Overdoing` | POAM-P overdoing / persistence subscale | sum of items 2,4,7,10,15,18,20,23,26,30 |
| `POAMP_Pacing` | POAM-P pacing subscale | sum of items 3,5,9,12,14,17,21,24,27,29 |
| `Leeftijd2` | Age in years | from birthdate and submit date |
| `BMI` | Body mass index | weight / (height/100)^2 |
| `GCPS_PEG` / `GCPS_Grade` | Graded Chronic Pain Scale severity / grade | per GCPS scoring |
| `TSK_sum` | Tampa Scale of Kinesiophobia total | items with 4,8,12,16 reverse-coded |
| `pijninterferentie_Tscore` | PROMIS pain interference T-score | sum -> T conversion |
| `SE`,`OE`,`RP`,`AP`,`CP`,`SM` | Social-cognitive determinants (self-efficacy, outcome expectancy, risk perception, action planning, coping planning, self-monitoring) | mean of items |
| `IPAQmet` | IPAQ total MET-min/week | standard IPAQ scoring |

## POAM-P framing (RQ2)

POAM-P (Patterns of Activity Measure - Pain) distinguishes three activity patterns:
- **Avoidance** (activity avoidance, fear-driven under-activity),
- **Overdoing** (task persistence / over-activity, "pushing through"),
- **Pacing** (adaptive activity regulation).

RQ2 asks whether participants form meaningful subgroups on these patterns and whether
those subgroups relate to the momentary dynamics estimated in RQ1.

## Missingness markers in the raw EMA export

The raw trigger-level export encodes non-completion with the string tokens
`<no-response>` (prompt not answered) and `<not-shown>` (item not displayed because of
branching logic). Both are converted to `NA` during preprocessing. A trigger is considered
"completed" if `COMPLETED_TS` is non-missing.
