# Shared helpers for all R analysis scripts.
# Sourced at the top of each stage script via:
#   source(file.path(Sys.getenv("PROJECT_LIB"), "common.R"))
# or by a relative path resolved by the orchestrator.

# ---- paths -----------------------------------------------------------------
# Resolve the project root from this file's location. Works when sourced.
.this_file <- tryCatch(
  normalizePath(sys.frame(1)$ofile, mustWork = FALSE),
  error = function(e) NA_character_
)
if (is.na(.this_file) || .this_file == "") {
  # Fallback: assume common.R lives in src/utils/lib
  .this_file <- file.path(getwd(), "common.R")
}

project_root <- function() {
  # src/utils/lib/common.R -> up three levels to project root
  p <- normalizePath(file.path(dirname(.this_file), "..", "..", ".."),
                     mustWork = FALSE)
  p
}

ROOT <- project_root()
DIR_PROCESSED <- file.path(ROOT, "src", "data", "processed")
DIR_TABLES    <- file.path(ROOT, "src", "results", "tables")
DIR_MODELS    <- file.path(ROOT, "src", "results", "models")
DIR_NETWORKS  <- file.path(ROOT, "src", "results", "networks")
DIR_LOGS      <- file.path(ROOT, "src", "results", "logs")
for (d in c(DIR_TABLES, DIR_MODELS, DIR_NETWORKS, DIR_LOGS)) {
  if (!dir.exists(d)) dir.create(d, recursive = TRUE, showWarnings = FALSE)
}

# ---- package loading -------------------------------------------------------
need <- function(pkgs) {
  for (p in pkgs) {
    suppressPackageStartupMessages(
      ok <- requireNamespace(p, quietly = TRUE)
    )
    if (!ok) stop(sprintf("Required R package not installed: %s", p))
    suppressPackageStartupMessages(library(p, character.only = TRUE))
  }
  invisible(TRUE)
}

# ---- io --------------------------------------------------------------------
read_ema <- function() {
  f <- file.path(DIR_PROCESSED, "ema_long.csv")
  utils::read.csv(f, stringsAsFactors = FALSE)
}
read_person <- function() {
  f <- file.path(DIR_PROCESSED, "person_level.csv")
  utils::read.csv(f, stringsAsFactors = FALSE)
}
write_result <- function(df, name, dir = DIR_TABLES) {
  f <- file.path(dir, name)
  utils::write.csv(df, f, row.names = FALSE)
  cat(sprintf("  wrote %s (%d rows)\n", f, nrow(df)))
  invisible(f)
}

# Core analytic node sets (column names in ema_long.csv).
CORE_NODES <- c("PIJN", "MOE", "STRESS", "ENMO_log")
CORE_LABELS <- c("Pain", "Fatigue", "Stress", "Activity")
EXTENDED_NODES <- c("PIJN", "MOE", "STRESS", "ENMO_log", "EIGENEFF", "INTENTIE")

cat(sprintf("[common.R] project root: %s\n", ROOT))
