from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    """Runtime settings.

    Keep this small and explicit — it makes the project easier to reason about.
    """

    # Safety/perf
    max_rows_preview: int = int(os.getenv("DATAGUARDIAN_MAX_ROWS", "200"))
    max_unique_per_column: int = int(os.getenv("DATAGUARDIAN_MAX_UNIQUE_PER_COLUMN", "200"))
    max_chars_per_cell: int = int(os.getenv("DATAGUARDIAN_MAX_CHARS_PER_CELL", "20000"))

    # Detection toggles
    enable_presidio: bool = os.getenv("DATAGUARDIAN_ENABLE_PRESIDIO", "1") == "1"

    # Reporting
    mask_keep_last: int = int(os.getenv("DATAGUARDIAN_MASK_KEEP_LAST", "4"))
