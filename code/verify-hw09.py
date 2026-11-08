"""HW9 artifact and evidence verifier."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports" / "hw09"
OUTPUT = REPORTS / "verification.json"


def check(name: str, passed: bool, detail: str) -> dict:
    return {"name": name, "pass": passed, "detail": detail}


def main() -> None:
    checks = []
    required_code = [
        "hw09_part1_counter.py",
        "hw09_part2_semantic_cache.py",
        "hw09_part3_threshold_sweep.py",
        "hw09_part3_false_hit.py",
        "hw09_part3_stale_invalidation.py",
        "hw09_part4.py",
    ]
    missing = [name for name in required_code if not (ROOT / "code" / name).exists()]
    checks.append(
        check(
            "required_code_files",
            not missing,
            f"Missing: {missing}" if missing else "All HW9 code files exist.",
        )
    )

    cases = REPORTS / "cache_cases.yaml"
    case_text = cases.read_text(encoding="utf-8") if cases.exists() else ""
    counts = {
        "exact_duplicate": case_text.count("category: exact_duplicate"),
        "paraphrase": case_text.count("category: paraphrase"),
        "similar_different_answer": case_text.count(
            "category: similar_different_answer"
        ),
        "unrelated": case_text.count("category: unrelated"),
    }
    checks.append(
        check(
            "cache_case_labels",
            counts == {key: 10 for key in counts},
            f"Counts: {counts}",
        )
    )

    threshold_path = REPORTS / "threshold_results.csv"
    thresholds = []
    if threshold_path.exists():
        with threshold_path.open(newline="", encoding="utf-8") as source:
            thresholds = [float(row["threshold"]) for row in csv.DictReader(source)]
    checks.append(
        check(
            "threshold_results",
            thresholds == [0.75, 0.8, 0.85, 0.9, 0.95],
            f"Thresholds: {thresholds}",
        )
    )

    metrics_text = (
        (REPORTS / "METRICS.md").read_text(encoding="utf-8")
        if (REPORTS / "METRICS.md").exists()
        else ""
    )
    checks.append(
        check(
            "part3_reports",
            all(
                section in metrics_text
                for section in [
                    "3.2 Threshold sweep",
                    "3.3 False hit",
                    "3.4 Cost model",
                    "3.5 Stale answers",
                ]
            ),
            "Sections 3.2 through 3.5 are present.",
        )
    )

    json_files = [
        "reference_data.json",
        "training_data.json",
        "validation_data.json",
        "test_data.json",
        "lessons.json",
    ]
    invalid = []
    lengths = {}
    for filename in json_files:
        try:
            data = json.loads((REPORTS / filename).read_text(encoding="utf-8"))
            lengths[filename] = (
                len(data) if isinstance(data, list) else len(data.get("records", []))
            )
        except Exception as error:
            invalid.append(f"{filename}: {error}")
    checks.append(
        check(
            "part4_json_artifacts",
            not invalid,
            f"Lengths: {lengths}" if not invalid else str(invalid),
        )
    )

    part4_text = (ROOT / "code" / "hw09_part4.py").read_text(encoding="utf-8")
    required_terms = [
        "class AnsweringAgent",
        "class EvaluatorAgent",
        "Evaluator Repair",
        "Lesson Memory",
        "Validated Improvement",
    ]
    checks.append(
        check(
            "part4_workflow_and_variants",
            all(term in part4_text for term in required_terms),
            "Answering/Evaluator agents and four variants are present.",
        )
    )

    all_passed = all(item["pass"] for item in checks)
    result = {
        "homework": 9,
        "sid4": "4544",
        "prefix": "s4544",
        "model": "qwen2.5:3b",
        "seed": 4544,
        "verify_seed": 264544,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "all_passed": all_passed,
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
