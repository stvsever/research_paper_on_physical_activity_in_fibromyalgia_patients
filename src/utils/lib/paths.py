"""Canonical project paths shared by every Python stage.

A single import point so that scripts never hard-code absolute paths. The project
root is resolved relative to this file, which lives at
``src/utils/lib/paths.py``.
"""
from __future__ import annotations

from pathlib import Path

# .../src/utils/lib/paths.py -> project root is four parents up.
ROOT = Path(__file__).resolve().parents[3]

SRC = ROOT / "src"
DATA = SRC / "data"
DATA_RAW = DATA / "raw"
DATA_PROCESSED = DATA / "processed"

RESULTS = SRC / "results"
RESULTS_TABLES = RESULTS / "tables"
RESULTS_MODELS = RESULTS / "models"
RESULTS_NETWORKS = RESULTS / "networks"
RESULTS_LOGS = RESULTS / "logs"

PIPELINE = SRC / "utils" / "pipeline"
PIPELINE_SEPARATE = PIPELINE / "separate"

PAPER = ROOT / "paper"
FIG_MAIN = PAPER / "assets" / "figures" / "main"
FIG_SUPP = PAPER / "assets" / "figures" / "supplementary"
TABLES_PAPER = PAPER / "assets" / "tables"
TABLES_MAIN = TABLES_PAPER / "main"
TABLES_SUPP = TABLES_PAPER / "supplementary"

# Raw source files (migrated from the gitignored Walk On EMA Teams folder).
RAW_BASELINE_SAV = DATA_RAW / "baseline_begin_studie.sav"
RAW_EMA_XLSX = DATA_RAW / "ema_triggerlevel_merged.xlsx"

# Processed analysis-ready files.
EMA_LONG = DATA_PROCESSED / "ema_long.csv"
PERSON_LEVEL = DATA_PROCESSED / "person_level.csv"
EXCLUSION_LOG = DATA_PROCESSED / "exclusion_log.csv"


def ensure_dirs() -> None:
    """Create every output directory if it does not yet exist."""
    for d in (
        DATA_PROCESSED,
        RESULTS_TABLES,
        RESULTS_MODELS,
        RESULTS_NETWORKS,
        RESULTS_LOGS,
        FIG_MAIN,
        FIG_SUPP,
        TABLES_PAPER,
        TABLES_MAIN,
        TABLES_SUPP,
    ):
        d.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    ensure_dirs()
    print("project root:", ROOT)
