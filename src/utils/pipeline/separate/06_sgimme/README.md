# Stage 06 - S-GIMME (complementary, data-driven)

**Goal.** Run the exact method Annick proposed (Subgrouping GIMME) as a complement to
mlVAR, and read it qualitatively given the short series.

`01_sgimme.R` writes per-person complete-case series (>=30 timepoints, gimme's hard
minimum), fits S-GIMME (group + subgroup + individual structure, contemporaneous + lag-1),
and curates gimme's output CSVs into `results/`.

**Results.**
- **No cross-variable path reached the group threshold** (0.75); only the four
  autoregressive paths are group-level.
- The most common individual path is contemporaneous **Pain -> Fatigue (10/30 persons)**,
  echoing mlVAR's strong Pain-Fatigue contemporaneous edge.
- Data-driven subgrouping is weak: 16 subgroups (sizes 7 and 9 plus 14 singletons,
  modularity 0.27), i.e. no robust subgroups at this series length.

**Two implementation gotchas (documented in the script).** With this gimme build you must
(1) feed a *directory* of CSVs with an explicit `sep`, and (2) **not** wrap the call in
`tryCatch` and **not** pass `standardize = TRUE` - both trigger a non-standard-evaluation
bug ("promise already under evaluation"). The script is written accordingly.
