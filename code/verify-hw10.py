"""Verify hw10"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports" / "hw10"
OUTPUT = REPORTS / "verification.json"


def check(name: str, passed: bool, detail: str) -> dict:
    return {"name": name, "pass": passed, "detail": detail}


def main() -> None:
    checks = []
    required_files = [
        ROOT / "code" / "hw10_evaluate.py",
        ROOT / "code" / "hw10_dashboard.py",
        REPORTS / "eval_cases.json",
        REPORTS / "human_labels.csv",
        REPORTS / "evaluation_results.json",
        REPORTS / "judge_runs.json",
        REPORTS / "judge_validation.json",
        REPORTS / "traces.jsonl",
        REPORTS / "latency_results.csv",
        REPORTS / "metrics.json",
        REPORTS / "AI_USE.md",
        REPORTS / "reproducible_run_instructions",
    ]
    missing = [
        str(path.relative_to(ROOT)) for path in required_files if not path.exists()
    ]
    checks.append(
        check(
            "required_hw10_files",
            not missing,
            f"Missing: {missing}" if missing else "All required HW10 files exist.",
        )
    )

    cases = json.loads((REPORTS / "eval_cases.json").read_text(encoding="utf-8"))
    with (REPORTS / "human_labels.csv").open(encoding="utf-8", newline="") as source:
        labels = list(csv.DictReader(source))
    checks.append(
        check(
            "frozen_cases_and_labels",
            len(cases) == 20 and len(labels) == 20,
            f"Cases: {len(cases)}, labels: {len(labels)}",
        )
    )

    validation = json.loads(
        (REPORTS / "judge_validation.json").read_text(encoding="utf-8")
    )
    raw_case_data = validation.get("raw_case_data", [])
    checks.append(
        check(
            "judge_validation_statistics",
            all(
                key in validation
                for key in (
                    "spearman_correlation",
                    "mean_absolute_difference",
                    "repeatability",
                )
            )
            and len(raw_case_data) == 20,
            f"Raw comparison rows: {len(raw_case_data)}",
        )
    )

    judge_runs = json.loads((REPORTS / "judge_runs.json").read_text(encoding="utf-8"))
    checks.append(
        check(
            "three_judge_runs",
            len(judge_runs) == 3 and all(len(run) == 20 for run in judge_runs),
            f"Runs: {len(judge_runs)}, rows per run: {[len(run) for run in judge_runs]}",
        )
    )

    span_lines = [
        line
        for line in (REPORTS / "traces.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    spans = [json.loads(line) for line in span_lines]
    required_span_fields = {
        "trace_id",
        "stage",
        "start_time",
        "end_time",
        "duration_ms",
        "status",
        "error",
    }
    valid_spans = all(required_span_fields.issubset(span) for span in spans)
    checks.append(
        check(
            "structured_trace_spans",
            bool(spans) and valid_spans,
            f"Span count: {len(spans)}",
        )
    )

    with (REPORTS / "latency_results.csv").open(encoding="utf-8", newline="") as source:
        latency_rows = list(csv.DictReader(source))
    checks.append(
        check(
            "fifty_cache_miss_requests",
            len(latency_rows) == 50,
            f"Latency rows: {len(latency_rows)}",
        )
    )

    metrics = json.loads((REPORTS / "metrics.json").read_text(encoding="utf-8"))
    examples = metrics.get("trace_examples", {})
    latency_table = metrics.get("stage_latency_experiment", [])
    checks.append(
        check(
            "trace_examples_and_latency_table",
            set(examples) == {"cache_hit", "cache_miss", "failed"}
            and len(latency_table) == 6,
            f"Trace examples: {list(examples)}, stages: {len(latency_table)}",
        )
    )

    all_passed = all(item["pass"] for item in checks)
    result = {
        "homework": 10,
        "sid4": "4544",
        "prefix": "s4544",
        "model": "qwen2.5:3b",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "all_passed": all_passed,
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
