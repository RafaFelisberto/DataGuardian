from __future__ import annotations

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import pandas as pd

from core.file_processor import process_file
from dataguardian.scan import scan_dataframe, scan_text
from dataguardian.reporting import to_html

app = FastAPI(title="DataGuardian API", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/scan/text")
def scan_text_endpoint(payload: dict):
    text = payload.get("text", "")
    if not isinstance(text, str) or not text.strip():
        raise HTTPException(status_code=400, detail="payload must contain non-empty 'text'")
    report = scan_text(text, target="api:text")
    return JSONResponse(report.to_dict())


@app.post("/scan/file")
async def scan_file(file: UploadFile = File(...), format: str = "json"):
    try:
        df = process_file(file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"could not parse file: {e}")

    if df is None or df.empty:
        raise HTTPException(status_code=400, detail="empty or invalid file")

    report = scan_dataframe(df, target=f"api:file:{file.filename}")
    if format == "html":
        return HTMLResponse(to_html(report))
    return JSONResponse(report.to_dict())
