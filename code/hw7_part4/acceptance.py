"""Create two 600-row synthetic usage scenarios and record actual page evidence."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from hw7_part4.agent import DEFAULT_PRICING_URL, run_analysis

PART4_DIR = Path(__file__).resolve().parent
RAW_DIR = PART4_DIR / "raw"
SCENARIO_DIR = RAW_DIR / "scenarios"


def _write_scenario(name: str, trip_months: list[str], duration_seconds: int) -> Path:
    SCENARIO_DIR.mkdir(parents=True, exist_ok=True)
    path = SCENARIO_DIR / f"{name}.csv"
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["start_time", "duration_sec", "user_type", "rideable_type"])
        for month in trip_months:
            for ride in range(20):
                day = ride % 27 + 1
                writer.writerow(
                    [
                        f"{month}-{day:02d}T08:00:00",
                        duration_seconds,
                        "Customer",
                        "classic_bike",
                    ]
                )
    return path


def run_acceptance_cases() -> list[dict]:
    membership_months = ["2026-08"] * 30
    paygo_months = []
    year, month = 2023, 1
    for _ in range(30):
        paygo_months.append(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            year += 1
            month = 1

    cases = [
        ("membership_wins", membership_months, 80 * 60, "Buy Monthly Membership"),
        ("paygo_wins", paygo_months, 60, "Pay Per Ride/Minute"),
    ]
    reports = []
    for name, months, duration_seconds, expected in cases:
        csv_path = _write_scenario(name, months, duration_seconds)
        report = run_analysis(csv_path.read_text(encoding="utf-8"), DEFAULT_PRICING_URL)
        report["scenario"] = {
            "name": name,
            "trip_rows": 600,
            "expected_decision": expected,
            "synthetic": True,
            "note": "Hypothetical usage profile using Bay Wheels public trip-data field names; not an identified rider's history.",
            "csv_file": str(csv_path.relative_to(PART4_DIR)),
        }
        if not report.get("success") or report["data"]["decision"] != expected:
            raise RuntimeError(f"Acceptance scenario {name} failed: {report}")
        reports.append(report)

    output = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "pricing_url": DEFAULT_PRICING_URL,
        "cases": reports,
    }
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / "acceptance_cases.json").write_text(
        json.dumps(output, indent=2), encoding="utf-8"
    )
    return reports


if __name__ == "__main__":
    for case in run_acceptance_cases():
        print(
            case["scenario"]["name"],
            case["data"]["decision"],
            case["data"]["cost_breakdown"],
            case["data"]["citations"],
        )
