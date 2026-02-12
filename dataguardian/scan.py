from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd

from .config import Settings
from .detectors.base import Detector, Match
from .detectors.regex_detector import RegexDetector
from .detectors.presidio_detector import PresidioDetector
from .reporting import Finding, ScanReport, now_iso
from .scoring import score_matches


def mask_value(value: str, keep_last: int = 4) -> str:
    if value is None:
        return value
    s = str(value)
    if len(s) <= keep_last:
        return "*" * len(s)
    return "*" * (len(s) - keep_last) + s[-keep_last:]


def default_detectors(settings: Settings) -> List[Detector]:
    dets: List[Detector] = [RegexDetector()]
    if settings.enable_presidio:
        p = PresidioDetector()
        if getattr(p, "available", False):
            dets.append(p)
    return dets


def scan_text(text: str, *, target: str = "text", settings: Optional[Settings] = None, detectors: Optional[List[Detector]] = None) -> ScanReport:
    settings = settings or Settings()
    detectors = detectors or default_detectors(settings)

    matches: List[Match] = []
    for d in detectors:
        matches.extend(d.detect(text))

    summary = score_matches(matches)
    findings = []
    if matches:
        findings.append(Finding(location="text", masked_value=mask_value(text, settings.mask_keep_last), matches=matches))

    return ScanReport(
        created_at=now_iso(),
        target=target,
        summary=summary,
        findings=findings,
        meta={"rows_scanned": 1, "detectors": [getattr(d, "name", d.__class__.__name__) for d in detectors]},
    )


def scan_dataframe(df: pd.DataFrame, *, target: str = "dataframe", settings: Optional[Settings] = None, detectors: Optional[List[Detector]] = None) -> ScanReport:
    settings = settings or Settings()
    detectors = detectors or default_detectors(settings)

    findings: List[Finding] = []
    all_matches: List[Match] = []

    max_rows = min(settings.max_rows_preview, len(df))
    for col in df.columns:
        series = df[col].dropna().astype(str)

        # safety: cap huge cells (DoS-ish)
        series = series.map(lambda x: x[: settings.max_chars_per_cell])

        values = series.head(max_rows).unique().tolist()[: settings.max_unique_per_column]

        for i, text in enumerate(values):
            m_here: List[Match] = []
            for d in detectors:
                m_here.extend(d.detect(text))

            if m_here:
                all_matches.extend(m_here)
                findings.append(
                    Finding(
                        location=f"column:{col}",
                        masked_value=mask_value(text, settings.mask_keep_last),
                        matches=m_here,
                    )
                )

    summary = score_matches(all_matches)
    return ScanReport(
        created_at=now_iso(),
        target=target,
        summary=summary,
        findings=findings,
        meta={
            "rows_scanned": max_rows,
            "columns": list(map(str, df.columns)),
            "detectors": [getattr(d, "name", d.__class__.__name__) for d in detectors],
        },
    )


def scan_path(path: str | Path, *, settings: Optional[Settings] = None) -> ScanReport:
    """Scan a file or folder.

    For folders, we scan supported files and aggregate (simple merge).
    """
    settings = settings or Settings()
    p = Path(path)

    if not p.exists():
        raise FileNotFoundError(str(p))

    from core.file_processor import process_file  # reuse existing robust parsing

    if p.is_file():
        # emulate UploadedFile-ish object
        class _F:
            def __init__(self, file_path: Path):
                self.name = file_path.name
                self.type = ""
                self._b = file_path.read_bytes()
                self._pos = 0
            def read(self):
                self._pos = len(self._b)
                return self._b
            def seek(self, pos: int):
                self._pos = pos

        df = process_file(_F(p))
        return scan_dataframe(df, target=str(p), settings=settings)

    # folder: aggregate reports
    supported = {".csv", ".json", ".jsonl", ".txt", ".sql"}
    reports: List[ScanReport] = []
    for fp in sorted(p.rglob("*")):
        if fp.is_file() and fp.suffix.lower() in supported:
            try:
                reports.append(scan_path(fp, settings=settings))
            except Exception:
                continue

    # merge
    all_findings: List[Finding] = []
    all_matches: List[Match] = []
    for r in reports:
        all_findings.extend(r.findings)
        for f in r.findings:
            all_matches.extend(f.matches)

    summary = score_matches(all_matches)
    return ScanReport(
        created_at=now_iso(),
        target=str(p),
        summary=summary,
        findings=all_findings,
        meta={"files_scanned": len(reports), "detectors": default_detectors(settings) and [getattr(d, "name", d.__class__.__name__) for d in default_detectors(settings)]},
    )
