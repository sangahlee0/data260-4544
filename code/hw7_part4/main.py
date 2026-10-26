from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from hw7_part4.agent import DEFAULT_PRICING_URL, run_analysis

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="Bay Wheels Membership Analyzer", version="1.0.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/")
def home():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/api/tools")
def tools():
    from hw7_part4.agent import TOOL_SCHEMAS

    return {"tools": list(TOOL_SCHEMAS.values())}


@app.post("/api/analyze")
async def analyze(
    trips_csv: UploadFile = File(...),
    pricing_url: str = Form(DEFAULT_PRICING_URL),
):
    if not trips_csv.filename or not trips_csv.filename.lower().endswith(".csv"):
        return {
            "success": False,
            "error": "Upload a .csv trip data file.",
            "step_count": 0,
            "total_time_ms": 0,
            "stop_reason": "human_review",
        }
    content = await trips_csv.read(25 * 1024 * 1024 + 1)
    if len(content) > 25 * 1024 * 1024:
        return {
            "success": False,
            "error": "CSV exceeds the 25 MB upload limit.",
            "step_count": 0,
            "total_time_ms": 0,
            "stop_reason": "human_review",
        }
    result = run_analysis(content.decode("utf-8-sig", errors="replace"), pricing_url)
    if result.get("success"):
        result["data"]["uploaded_filename"] = trips_csv.filename
    return result
