"""Run standalone R analysis scripts from Python.

Design choice
-------------
The statistical models in this project (multilevel VAR, S-GIMME, graphicalVAR,
mixed-effects variance decomposition) are written as plain ``.R`` files so they can be
read, reviewed, and re-run independently of Python. Python is responsible for
orchestration, preprocessing, and visualization only.

We invoke each ``.R`` file through ``Rscript`` in a subprocess rather than through an
in-process bridge such as ``rpy2``. The subprocess approach is more reproducible and
robust: the R session is isolated, the script is exactly the artifact under version
control, and a non-zero exit status surfaces immediately. Any ``rpy2``-style library
would call the same scripts; the boundary (R does models, Python does the rest) is
identical.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path


def run_r_script(script_path: str | Path, args: list[str] | None = None,
                 echo: bool = True) -> subprocess.CompletedProcess:
    """Execute an R script with ``Rscript`` and stream its output.

    Parameters
    ----------
    script_path : path to the ``.R`` file.
    args : optional list of command-line arguments passed to the script
        (available in R via ``commandArgs(trailingOnly = TRUE)``).
    echo : print stdout/stderr as the script runs.

    Raises
    ------
    RuntimeError if the script exits with a non-zero status.
    """
    script_path = Path(script_path)
    if not script_path.exists():
        raise FileNotFoundError(f"R script not found: {script_path}")

    cmd = ["Rscript", "--vanilla", str(script_path)] + (args or [])
    if echo:
        print(f"\n>>> Rscript {script_path.name} {' '.join(args or [])}", flush=True)

    start = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - start

    if echo:
        if proc.stdout:
            print(proc.stdout, flush=True)
        if proc.stderr:
            # R writes notes/warnings to stderr; show them but do not treat as fatal.
            print(proc.stderr, file=sys.stderr, flush=True)
        print(f"<<< {script_path.name} finished in {elapsed:0.1f}s "
              f"(exit {proc.returncode})", flush=True)

    if proc.returncode != 0:
        raise RuntimeError(
            f"R script failed: {script_path} (exit {proc.returncode}). "
            f"See stderr above."
        )
    return proc
