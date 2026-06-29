"""End-to-end pipeline orchestrator.

Runs every stage of the Walk On! EMA analysis in order. Python stages run in-process;
R analysis stages are executed as standalone ``.R`` files through ``Rscript`` (see
src/utils/lib/runr.py for the rationale). This is the single entry point that reproduces
all processed data, results, figures, and tables from the raw inputs.

Usage:
    python src/utils/pipeline/full/run_all.py            # run everything
    python src/utils/pipeline/full/run_all.py --from 05  # resume from a stage prefix
    python src/utils/pipeline/full/run_all.py --only 05  # run a single stage prefix
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

LIB = Path(__file__).resolve().parents[2] / "lib"
sys.path.insert(0, str(LIB))
import paths  # noqa: E402
from runr import run_r_script  # noqa: E402

SEP = paths.PIPELINE_SEPARATE

# (stage_prefix, kind, relative_script_path, optional_args)
STEPS = [
    ("01", "py", "01_preprocessing/01_build_person_level.py", []),
    ("01", "py", "01_preprocessing/02_build_ema_long.py", []),
    ("02", "py", "02_descriptives/01_descriptives.py", []),
    ("02", "py", "02_descriptives/02_context.py", []),
    ("02", "py", "02_descriptives/03_daytype.py", []),
    ("02", "py", "02_descriptives/04_timing.py", []),
    ("03", "R",  "03_variance_decomposition/01_variance_decomposition.R", []),
    ("04", "R",  "04_stationarity_missingness/01_stationarity.R", []),
    ("04", "py", "04_stationarity_missingness/02_imputation_comparison.py", []),
    ("05", "R",  "05_mlvar/01_mlvar_core.R", []),
    ("05", "R",  "05_mlvar/02_residual_diagnostics.R", []),
    ("06", "R",  "06_sgimme/01_sgimme.R", []),
    ("07", "R",  "07_idiographic_graphicalvar/01_graphicalvar_perperson.R", []),
    ("07", "R",  "07_idiographic_graphicalvar/02_perperson_var_ols.R", []),
    ("08", "py", "08_poamp_subgroups/01_poamp_subgroups.py", []),
    ("09", "py", "09_network_poamp_link/01_link.py", []),
    ("10", "R",  "10_robustness/01_detrended_mlvar.R", []),
    ("10", "R",  "10_robustness/02_leave_one_out.R", []),
    ("10", "R",  "10_robustness/03_person_bootstrap.R", ["500"]),
    ("10", "R",  "10_robustness/04_extended_model.R", []),
    ("10", "R",  "10_robustness/05_cantmove_sensitivity.R", []),
    ("10", "R",  "10_robustness/06_compliance_threshold.R", []),
    ("10", "R",  "10_robustness/07_enmo_transform.R", []),
    ("10", "R",  "10_robustness/08_permutation_link.R", []),
    ("11", "R",  "11_pacing/01_pacing_dynamics.R", []),
    ("12", "py", "12_figures_tables/01_main_figures.py", []),
    ("12", "py", "12_figures_tables/02_supp_figures.py", []),
    ("12", "py", "12_figures_tables/03_tables.py", []),
    ("12", "py", "12_figures_tables/04_latex_tables.py", []),
]


def run_py(script: Path, args):
    print(f"\n>>> python {script.name} {' '.join(args)}", flush=True)
    start = time.time()
    proc = subprocess.run([sys.executable, str(script)] + args,
                          capture_output=True, text=True)
    if proc.stdout:
        print(proc.stdout, flush=True)
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr, flush=True)
        raise RuntimeError(f"Python stage failed: {script}")
    print(f"<<< {script.name} finished in {time.time()-start:0.1f}s", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="frm", default=None,
                    help="resume from this stage prefix (e.g. 05)")
    ap.add_argument("--only", dest="only", default=None,
                    help="run only this stage prefix")
    args = ap.parse_args()

    paths.ensure_dirs()
    started = False if args.frm else True
    t0 = time.time()
    for prefix, kind, rel, sargs in STEPS:
        if args.only and prefix != args.only:
            continue
        if not started:
            if prefix == args.frm:
                started = True
            else:
                continue
        script = SEP / rel
        if kind == "py":
            run_py(script, sargs)
        else:
            run_r_script(script, sargs)
    print(f"\n=== pipeline complete in {time.time()-t0:0.1f}s ===")


if __name__ == "__main__":
    main()
