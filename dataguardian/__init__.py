"""DataGuardian - DLP-lite scanner for sensitive data.

This package contains the reusable engine (detectors, scanning, scoring, reports).
"""

from .config import Settings
from .scan import scan_text, scan_dataframe, scan_path
