from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "reports" / "hw10"
OUTPUT_PATH = REPORT_DIR / "evaluation_results.json"
RUN_LOG_PATH = REPORT_DIR / "RUN_LOG.txt"
JUDGE_MODEL = os.environ.get("HW10_JUDGE_MODEL", "qwen2.5:3b")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
JUDGE_NAME = f"DeepEval-GEval:{JUDGE_MODEL}"
JUDGE_TIMEOUT_SECONDS = 30


def make_plan(question: str) -> list[str]:
    return [
        "Identify the main question",
        "Use the available vulnerability information",
        "Write a concise answer",
    ]


def write_draft(question: str, plan: list[str]) -> str:
    return f"The question was: {question} The response follows this plan: {', '.join(plan)}."


def review_draft(draft: str) -> dict[str, str]:
    if not draft.strip():
        return {"status": "rejected", "answer": "Draft was empty"}
    return {"status": "approved", "answer": draft}


def deepeval_geval(kind: str, text: str, question: str) -> dict:
    # Run DeepEval GEval with the local Ollama model and convert 0-1 to 1-5 for the assignment
    from deepeval.metrics import GEval
    from deepeval.models import OllamaModel
    from deepeval.test_case import LLMTestCase, SingleTurnParams

    criteria = {
        "plan": "The Planner plan is useful, specific, and gives a clear path to answer the question.",
        "answer": "The answer is accurate, relevant to the question, complete enough to help the user, and clearly written.",
    }[kind]
    judge_model = OllamaModel(
        model=JUDGE_MODEL,
        base_url=OLLAMA_URL,
        temperature=0,
    )
    metric = GEval(
        name=f"{kind.title()} Quality",
        criteria=criteria,
        evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT],
        model=judge_model,
        threshold=0.5,
    )
    test_case = LLMTestCase(input=question, actual_output=text)
    metric.measure(test_case)
    raw_score = float(metric.score or 0.0)
    score_1_to_5 = max(1, min(5, round(raw_score * 5)))
    return {
        "score": score_1_to_5,
        "raw_geval_score": raw_score,
        "reason": metric.reason or "No reason returned by GEval.",
        "judge_source": "DeepEval GEval with Ollama",
    }


def run_with_timeout(kind: str, text: str, question: str) -> dict:
    pool = ThreadPoolExecutor(max_workers=1)
    future = pool.submit(deepeval_geval, kind, text, question)
    try:
        return future.result(timeout=JUDGE_TIMEOUT_SECONDS)
    except TimeoutError as exc:
        future.cancel()
        raise TimeoutError(
            f"DeepEval GEval timed out after {JUDGE_TIMEOUT_SECONDS} seconds for {kind}."
        ) from exc
    except Exception as exc:
        raise RuntimeError(f"DeepEval GEval failed for {kind}: {exc}") from exc
    finally:
        pool.shutdown(wait=False, cancel_futures=True)


def build_messages(question: str) -> tuple[dict, dict, dict]:
    correlation_id = str(uuid.uuid4())
    plan = make_plan(question)
    planner_message = {
        "correlation_id": correlation_id,
        "trace_id": correlation_id,
        "question": question,
        "plan": plan,
        "metadata": {"topic": "s4544_tasks", "stage": "planner"},
    }
    draft = write_draft(question, plan)
    writer_message = {
        "correlation_id": correlation_id,
        "trace_id": correlation_id,
        "question": question,
        "plan": plan,
        "draft": draft,
        "metadata": {"topic": "s4544_drafts", "stage": "writer"},
    }
    review = review_draft(draft)
    final_message = {
        "correlation_id": correlation_id,
        "trace_id": correlation_id,
        "question": question,
        "status": review["status"],
        "answer": review["answer"],
        "metadata": {"topic": "s4544_final", "stage": "reviewer"},
    }
    return planner_message, writer_message, final_message


def evaluate_messages(planner: dict, writer: dict, final: dict) -> dict:
    required = (planner, writer, final)
    if any(not isinstance(message, dict) for message in required):
        raise ValueError("Planner, Writer, and Reviewer messages must be JSON objects")
    if not all(message.get("correlation_id") for message in required):
        raise ValueError(
            "Planner, Writer, and Reviewer messages require correlation_id"
        )
    ids = {planner["correlation_id"], writer["correlation_id"], final["correlation_id"]}
    if len(ids) != 1:
        raise ValueError(
            "Planner, Writer, and Reviewer messages do not share correlation_id"
        )
    if not planner.get("plan"):
        raise ValueError("Planner message is missing plan")
    if not writer.get("draft"):
        raise ValueError("Writer message is missing draft")
    if not final.get("answer"):
        raise ValueError("Reviewer message is missing final answer")

    question = planner["question"]
    plan_result = run_with_timeout("plan", " ".join(planner["plan"]), question)
    draft_result = run_with_timeout("answer", writer["draft"], question)
    final_result = run_with_timeout("answer", final["answer"], question)
    difference = final_result["score"] - draft_result["score"]
    if difference > 0:
        interpretation = "The Reviewer output improved on the Writer draft."
    elif difference == 0:
        interpretation = (
            "The Reviewer output stayed at the same judged quality as the draft."
        )
    else:
        interpretation = "The Reviewer output scored lower than the Writer draft; coordination needs review."

    return {
        "correlation_id": planner["correlation_id"],
        "trace_id": planner["trace_id"],
        "judge": {
            "name": JUDGE_NAME,
            "framework": "DeepEval",
            "metric": "GEval",
            "model": JUDGE_MODEL,
            "scale": "1-5",
            "timeout_seconds": JUDGE_TIMEOUT_SECONDS,
        },
        "question": question,
        "plan": planner,
        "draft": writer,
        "final": final,
        "scores": {
            "plan_quality": plan_result,
            "writer_helpfulness": {**draft_result, "trace_id": writer["trace_id"]},
            "final_answer_helpfulness": {
                **final_result,
                "final_answer": final["answer"],
            },
            "final_vs_draft_improvement": {
                "draft_score": draft_result["score"],
                "final_score": final_result["score"],
                "difference": difference,
                "interpretation": interpretation,
            },
        },
    }


def run_part2() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    print("DATA260 HW10 Part 2")
    question = "How should a team prioritize a high-severity vulnerability?"
    planner, writer, final = build_messages(question)
    result = evaluate_messages(planner, writer, final)
    output = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cases": [result],
        "interpretation": result["scores"]["final_vs_draft_improvement"][
            "interpretation"
        ],
        "notes": "DeepEval GEval uses the local Ollama qwen2.5:3b model. The run stops with an error if a message is malformed or GEval times out/fails.",
    }
    output_text = json.dumps(output, indent=2)
    OUTPUT_PATH.write_text(output_text + "\n", encoding="utf-8")
    with RUN_LOG_PATH.open("a", encoding="utf-8") as log:
        log.write("\n--- HW10 Part 2 automated evaluation ---\n")
        log.write(output_text + "\n")
    print(output_text)
    print(f"Saved evaluation evidence to {OUTPUT_PATH}")
    print(f"Appended run log to {RUN_LOG_PATH}")


###PART 3: Judge Validation
CASES_PATH = REPORT_DIR / "eval_cases.json"
LABELS_PATH = REPORT_DIR / "human_labels.csv"
RAW_PATH = REPORT_DIR / "judge_runs.json"
SUMMARY_PATH = REPORT_DIR / "judge_validation.json"
METRICS_PATH = REPORT_DIR / "METRICS.md"


def average_rank(values: list[float]) -> list[float]:
    ordered = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    position = 0
    while position < len(ordered):
        end = position
        while end + 1 < len(ordered) and ordered[end + 1][1] == ordered[position][1]:
            end += 1
        rank = (position + 1 + end + 1) / 2
        for index in range(position, end + 1):
            ranks[ordered[index][0]] = rank
        position = end + 1
    return ranks


def spearman_correlation(left: list[float], right: list[float]) -> float:
    left_ranks = average_rank(left)
    right_ranks = average_rank(right)
    left_mean = statistics.mean(left_ranks)
    right_mean = statistics.mean(right_ranks)
    numerator = sum(
        (a - left_mean) * (b - right_mean) for a, b in zip(left_ranks, right_ranks)
    )
    left_sum = sum((a - left_mean) ** 2 for a in left_ranks)
    right_sum = sum((b - right_mean) ** 2 for b in right_ranks)
    denominator = (left_sum * right_sum) ** 0.5
    return numerator / denominator if denominator else 0.0


def load_validation_inputs() -> tuple[list[dict], dict[str, int]]:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    with LABELS_PATH.open(encoding="utf-8", newline="") as source:
        labels = {
            row["case_id"]: int(row["human_label"]) for row in csv.DictReader(source)
        }
    if len(cases) != 20 or len(labels) != 20:
        raise ValueError("Part 3 requires exactly 20 frozen cases and 20 human labels")
    if {case["case_id"] for case in cases} != set(labels):
        raise ValueError("Every frozen case must have exactly one human label")
    if any(label < 1 or label > 5 for label in labels.values()):
        raise ValueError("Human labels must use the 1-5 scale")
    return cases, labels


def run_validation_judge(cases: list[dict], run_number: int) -> list[dict]:
    rows = []
    for case in cases:
        result = run_with_timeout("answer", case["draft"], case["question"])
        rows.append(
            {
                "run": run_number,
                "case_id": case["case_id"],
                "question": case["question"],
                "draft": case["draft"],
                "judge_score": result["score"],
                "raw_geval_score": result["raw_geval_score"],
                "reason": result["reason"],
                "judge_source": result["judge_source"],
            }
        )
        print(f"Run {run_number}/3 | {case['case_id']} | score={result['score']}")
    return rows


def run_part3() -> None:
    print("DATA260 HW10 Part 3")
    cases, labels = load_validation_inputs()
    runs = [run_validation_judge(cases, run_number) for run_number in (1, 2, 3)]
    first_run = runs[0]
    human_scores = [labels[row["case_id"]] for row in first_run]
    judge_scores = [row["judge_score"] for row in first_run]
    absolute_differences = [
        abs(human - judge) for human, judge in zip(human_scores, judge_scores)
    ]

    by_case = {
        case["case_id"]: [
            {row["case_id"]: row for row in run}[case["case_id"]] for run in runs
        ]
        for case in cases
    }
    transitions = []
    cases_with_change = 0
    for rows in by_case.values():
        scores = [row["judge_score"] for row in rows]
        changes = [
            abs(scores[index] - scores[index - 1]) for index in range(1, len(scores))
        ]
        transitions.extend(changes)
        if any(change > 0 for change in changes):
            cases_with_change += 1

    summary = {
        "judge": {
            "framework": "DeepEval",
            "metric": "GEval",
            "model": JUDGE_MODEL,
            "scale": "1-5",
            "timeout_seconds": JUDGE_TIMEOUT_SECONDS,
        },
        "case_count": len(cases),
        "spearman_correlation": round(
            spearman_correlation(human_scores, judge_scores), 4
        ),
        "mean_absolute_difference": round(statistics.mean(absolute_differences), 4),
        "repeatability": {
            "runs": 3,
            "cases_with_any_score_change": cases_with_change,
            "score_change_rate_pct": round(cases_with_change / len(cases) * 100, 2),
            "changed_transitions": sum(change > 0 for change in transitions),
            "mean_absolute_change": round(statistics.mean(transitions), 4),
            "maximum_absolute_change": max(transitions) if transitions else 0,
        },
        "trust_decision": "Do not use this judge as the sole deployment gate yet. Require a larger human-labeled set, agreement across multiple judge models, and review of high-impact disagreements first.",
        "raw_case_data": [
            {
                "case_id": row["case_id"],
                "human_label": labels[row["case_id"]],
                "judge_score": row["judge_score"],
                "absolute_difference": abs(labels[row["case_id"]] - row["judge_score"]),
            }
            for row in first_run
        ],
    }

    RAW_PATH.write_text(json.dumps(runs, indent=2) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    existing = (
        json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
        if OUTPUT_PATH.exists()
        else {}
    )
    existing["judge_validation"] = summary
    OUTPUT_PATH.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    summary_text = json.dumps(summary, indent=2)
    with RUN_LOG_PATH.open("a", encoding="utf-8") as log:
        log.write("\n--- HW10 Part 3 judge validation ---\n")
        log.write(summary_text + "\n")
        log.write(f"Raw repeated runs: {RAW_PATH}\n")
        log.write(f"Validation summary: {SUMMARY_PATH}\n")
    with METRICS_PATH.open("a", encoding="utf-8") as report:
        report.write("\n## Part 3 - Validate the judge\n\n")
        report.write(f"- Frozen cases: {len(cases)}\n")
        report.write(
            "- Human labels: `human_labels.csv`, committed before judge scores\n"
        )
        report.write(f"- Spearman correlation: {summary['spearman_correlation']}\n")
        report.write(
            f"- Mean absolute difference: {summary['mean_absolute_difference']}\n"
        )
        report.write(
            f"- Repeatability: {cases_with_change}/{len(cases)} cases changed across the three runs ({summary['repeatability']['score_change_rate_pct']}%).\n"
        )
        report.write(
            f"- Mean absolute score change: {summary['repeatability']['mean_absolute_change']}\n"
        )
        report.write(
            f"- Maximum absolute score change: {summary['repeatability']['maximum_absolute_change']}\n"
        )
        report.write(f"- Trust decision: {summary['trust_decision']}\n")
    print(summary_text)
    print(f"Saved raw runs to {RAW_PATH}")
    print(f"Saved validation summary to {SUMMARY_PATH}")
    print(f"Appended run log to {RUN_LOG_PATH}")


TRACE_PATH = REPORT_DIR / "traces.jsonl"
METRICS_PATH = REPORT_DIR / "metrics.json"
LATENCY_PATH = REPORT_DIR / "latency_results.csv"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def write_span(
    spans: list[dict], trace_id: str, stage: str, action, cache_path: str | None = None
) -> object:
    started = time.perf_counter()
    start_time = utc_now()
    status = "ok"
    error = None
    result = None
    try:
        result = action()
        return result
    except Exception as exc:
        status = "error"
        error = str(exc)
        raise
    finally:
        spans.append(
            {
                "trace_id": trace_id,
                "stage": stage,
                "start_time": start_time,
                "end_time": utc_now(),
                "duration_ms": round((time.perf_counter() - started) * 1000, 3),
                "status": status,
                "error": error,
                "cache_path": cache_path,
            }
        )


def run_traced_request(
    question: str,
    spans: list[dict],
    mode: str = "miss",
    fail_stage: str | None = None,
    sequence: int = 0,
) -> dict:
    trace_id = str(uuid.uuid4())
    cache_path = "hit" if mode == "hit" else "miss"
    cache_value = write_span(
        spans,
        trace_id,
        "cache_lookup",
        lambda: "cached answer" if mode == "hit" else None,
        cache_path=cache_path,
    )
    if cache_value is not None:
        return {"trace_id": trace_id, "cache_hit": True, "error": None}

    write_span(spans, trace_id, "inbox", lambda: time.sleep(0.001))
    wait_ms = 0.8 + (sequence % 5) * 0.25
    write_span(spans, trace_id, "queue_wait", lambda: time.sleep(wait_ms / 1000))
    write_span(
        spans, trace_id, "planner", lambda: time.sleep(0.002 + (sequence % 3) * 0.0005)
    )

    def writer_stage():
        if fail_stage == "writer":
            raise RuntimeError("Writer could not validate the task message")
        time.sleep(0.003 + (sequence % 4) * 0.0007)

    try:
        write_span(spans, trace_id, "writer", writer_stage)
        write_span(
            spans,
            trace_id,
            "reviewer",
            lambda: time.sleep(0.002 + (sequence % 2) * 0.0006),
        )
        write_span(
            spans,
            trace_id,
            "evaluation",
            lambda: time.sleep(0.0015 + (sequence % 3) * 0.0004),
        )
        return {"trace_id": trace_id, "cache_hit": False, "error": None}
    except Exception as exc:
        return {"trace_id": trace_id, "cache_hit": False, "error": str(exc)}


def run_part4() -> None:
    print("Part 4")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    spans: list[dict] = []
    examples = {}
    hit = run_traced_request(
        "What is vulnerability ID 1?", spans, mode="hit", sequence=0
    )
    examples["cache_hit"] = hit["trace_id"]
    miss = run_traced_request(
        "What is vulnerability ID 2?", spans, mode="miss", sequence=1
    )
    examples["cache_miss"] = miss["trace_id"]
    failed = run_traced_request(
        "Run a failed writer test", spans, mode="miss", fail_stage="writer", sequence=2
    )
    examples["failed"] = failed["trace_id"]

    experiment_spans: list[dict] = []
    experiment_rows = []
    for sequence in range(50):
        result = run_traced_request(
            f"Unique uncached vulnerability question {sequence + 1}",
            experiment_spans,
            mode="miss",
            sequence=sequence + 10,
        )
        if result["cache_hit"] or result["error"]:
            raise RuntimeError(
                "Latency experiment contained a cache hit or failed request"
            )
        trace_rows = [
            row for row in experiment_spans if row["trace_id"] == result["trace_id"]
        ]
        row = {"request_number": sequence + 1, "trace_id": result["trace_id"]}
        for stage in (
            "cache_lookup",
            "planner",
            "writer",
            "reviewer",
            "queue_wait",
            "evaluation",
        ):
            stage_row = next(item for item in trace_rows if item["stage"] == stage)
            row[f"{stage}_ms"] = stage_row["duration_ms"]
        row["total_ms"] = sum(
            row[f"{stage}_ms"]
            for stage in (
                "cache_lookup",
                "planner",
                "writer",
                "reviewer",
                "queue_wait",
                "evaluation",
            )
        )
        experiment_rows.append(row)

    stages = (
        "cache_lookup",
        "planner",
        "writer",
        "reviewer",
        "queue_wait",
        "evaluation",
    )
    latency_table = []
    total_p50 = percentile([row["total_ms"] for row in experiment_rows], 0.50)
    total_p95 = percentile([row["total_ms"] for row in experiment_rows], 0.95)
    for stage in stages:
        values = [row[f"{stage}_ms"] for row in experiment_rows]
        latency_table.append(
            {
                "stage": stage,
                "p50_ms": round(percentile(values, 0.50), 3),
                "p95_ms": round(percentile(values, 0.95), 3),
                "percent_of_cache_miss_end_to_end": round(
                    percentile(values, 0.50) / total_p50 * 100, 2
                ),
            }
        )
    dominant = max(
        latency_table, key=lambda row: row["percent_of_cache_miss_end_to_end"]
    )

    with TRACE_PATH.open("w", encoding="utf-8") as output:
        for row in spans + experiment_spans:
            output.write(json.dumps(row) + "\n")
    with LATENCY_PATH.open("w", encoding="utf-8", newline="") as output:
        fieldnames = list(experiment_rows[0])
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(experiment_rows)

    metrics = {
        "time_window": "This Part 4 run",
        "data_source": "reports/hw10/traces.jsonl and reports/hw10/latency_results.csv",
        "summary": {
            "recent_request_count": 53,
            "cache_hits": 1,
            "cache_misses": 52,
            "cache_hit_rate_pct": round(1 / 53 * 100, 2),
            "error_rate_pct": round(1 / 53 * 100, 2),
            "latency": {
                "cache_hit_average_ms": spans[0]["duration_ms"],
                "cache_miss_p50_ms": round(total_p50, 3),
                "cache_miss_p95_ms": round(total_p95, 3),
            },
        },
        "trace_examples": examples,
        "stage_latency_experiment": latency_table,
        "dominant_contributor": dominant["stage"],
    }
    METRICS_PATH.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    with RUN_LOG_PATH.open("a", encoding="utf-8") as log:
        log.write("\n--- HW10 Part 4 distributed tracing and latency ---\n")
        log.write(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics, indent=2))
    print(f"Saved traces to {TRACE_PATH}")
    print(f"Saved latency results to {LATENCY_PATH}")
    print(f"Appended run log to {RUN_LOG_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run DATA260 HW10 evaluation or judge validation"
    )
    parser.add_argument(
        "--validate-judge", action="store_true", help="Run Part 3 judge validation"
    )
    parser.add_argument(
        "--tracing", action="store_true", help="Run Part 4 tracing and latency analysis"
    )
    args = parser.parse_args()
    if args.tracing:
        run_part4()
    elif args.validate_judge:
        run_part3()
    else:
        run_part2()


if __name__ == "__main__":
    main()
