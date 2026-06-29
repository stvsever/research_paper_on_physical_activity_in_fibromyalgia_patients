# Stage 11 - Pacing behaviour dynamics

The EMA also captured momentary pacing on active prompts: SPEED (deliberate slowing),
PIECES (chunking tasks), BREAKS (extra breaks) - the moment-level analogue of the POAM-P
pacing construct.

`01_pacing_dynamics.R` describes the three items and fits multilevel models for
(2) symptoms -> concurrent pacing and (3) pacing -> objective activity.

**Findings.**
- Pacing items each average ~3 on 0-10 (used on ~990 active prompts).
- Within-person, more momentary **pain (b = 0.13, p = .001)** and **fatigue (b = 0.12,
  p < .001)** predict more concurrent pacing; stress does not. People pace more when they
  hurt more - adaptive in-the-moment regulation.
- Momentary pacing is **not** associated with the objective activity in the window
  (b = 0.003, p = .81): pacing changes *how* activity is done, not the total amount.

Output -> `SUP_07` figure and `SUP_06` table.
