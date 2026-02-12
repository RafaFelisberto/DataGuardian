from __future__ import annotations

from pathlib import Path
import sys

import typer

from dataguardian.scan import scan_path
from dataguardian.reporting import to_html

app = typer.Typer(add_completion=False, help="DataGuardian - scan files/folders for sensitive data (DLP-lite).")


@app.command()
def scan(
    path: Path = typer.Argument(..., help="File or folder to scan"),
    out: Path = typer.Option(Path("reports/report.json"), "--out", "-o", help="Output JSON report path"),
    html: bool = typer.Option(True, help="Also write an HTML report next to JSON"),
):
    """Scan PATH and export a report."""
    report = scan_path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report.to_json(), encoding="utf-8")
    typer.echo(f"✅ JSON report written to: {out}")

    if html:
        html_path = out.with_suffix(".html")
        html_path.write_text(to_html(report), encoding="utf-8")
        typer.echo(f"✅ HTML report written to: {html_path}")

    typer.echo(f"Risk: {report.summary.level} (score={report.summary.score})")


def main():
    app()


if __name__ == "__main__":
    main()
