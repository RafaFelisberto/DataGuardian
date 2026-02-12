from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .detectors.base import Match
from .scoring import RiskSummary


@dataclass
class Finding:
    location: str
    masked_value: str
    matches: List[Match]


@dataclass
class ScanReport:
    created_at: str
    target: str
    summary: RiskSummary
    findings: List[Finding]
    meta: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "created_at": self.created_at,
            "target": self.target,
            "summary": asdict(self.summary),
            "findings": [
                {
                    "location": f.location,
                    "masked_value": f.masked_value,
                    "matches": [asdict(m) for m in f.matches],
                }
                for f in self.findings
            ],
            "meta": self.meta,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


_HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>DataGuardian Report</title>
  <style>
    body { font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial; margin: 24px; }
    .card { border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px; margin-bottom: 16px; }
    .pill { display:inline-block; padding: 4px 10px; border-radius: 999px; border: 1px solid #e5e7eb; font-size: 12px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { text-align: left; border-bottom: 1px solid #f1f5f9; padding: 10px 8px; vertical-align: top; }
    th { font-size: 12px; color: #475569; text-transform: uppercase; letter-spacing: .04em; }
    code { background: #f8fafc; padding: 2px 6px; border-radius: 6px; }
    .muted { color: #64748b; }
  </style>
</head>
<body>
  <h1>DataGuardian Report</h1>
  <p class="muted">Generated at: {{created_at}} • Target: <code>{{target}}</code></p>

  <div class="card">
    <h2>Risk Summary</h2>
    <p><span class="pill">Level: {{level}}</span> <span class="pill">Score: {{score}}</span></p>
    <p class="muted">Counts by type:</p>
    <ul>
      {{counts_li}}
    </ul>
  </div>

  <div class="card">
    <h2>Findings</h2>
    <table>
      <thead><tr><th>Location</th><th>Masked value</th><th>Matches</th></tr></thead>
      <tbody>
        {{rows}}
      </tbody>
    </table>
  </div>
</body>
</html>
"""


def to_html(report: ScanReport) -> str:
    counts_li = "\n".join([f"<li><code>{k}</code>: {v}</li>" for k, v in sorted(report.summary.counts_by_type.items())]) or "<li>(none)</li>"
    rows = []
    for f in report.findings:
        match_types = ", ".join(sorted({m.type for m in f.matches})) or "-"
        rows.append(
            "<tr>"
            f"<td><code>{_escape(f.location)}</code></td>"
            f"<td><code>{_escape(f.masked_value)}</code></td>"
            f"<td>{_escape(match_types)}</td>"
            "</tr>"
        )

    html = _HTML_TEMPLATE
    html = html.replace("{{created_at}}", _escape(report.created_at))
    html = html.replace("{{target}}", _escape(report.target))
    html = html.replace("{{level}}", _escape(report.summary.level))
    html = html.replace("{{score}}", str(report.summary.score))
    html = html.replace("{{counts_li}}", counts_li)
    html = html.replace("{{rows}}", "\n".join(rows) if rows else "<tr><td colspan=3>(no findings)</td></tr>")
    return html


def _escape(s: str) -> str:
    return (
        (s or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
