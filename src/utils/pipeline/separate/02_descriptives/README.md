# Stage 02 - Descriptives

**Goal.** Sample, compliance, and distributional descriptives that feed Table 1, Table 2,
and the design/compliance figure.

`01_descriptives.py` writes (to `results/tables/`): EMA variable descriptives with
within/between SD decomposition, compliance summary and per-person compliance, the
baseline Table 1, education distribution, and within- vs between-person correlation
matrices among the four core nodes.

`02_context.py` uses the otherwise-unused context fields (location `WAAR`, social setting
`ALLEEN`) to describe where and with whom momentary reports occur, objective activity by
location, and momentary affect alone vs accompanied. Feeds the context supplement
(`SUP_11`).

`04_timing.py` returns the raw-protocol timing audit from the trigger-level export:
scheduled clock times, adjacent-prompt intervals, response latency, questionnaire duration,
weekday/weekend completion, and trigger rows missing from the expected 14 x 4 schedule.

**What to look at.**
- Compliance: mean 77.9% answered, median 44 completed prompts/person.
- Within-person SD is sizeable for every measure (motivates within-person modelling).
- Within-person correlations: Pain-Fatigue 0.43, Activity weakly negative with Pain/Fatigue.
- Between-person correlations are much stronger (e.g., Pain-Fatigue 0.72), a classic
  within vs between divergence that justifies separating the two in mlVAR.
