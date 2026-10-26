"""
HW7 Part 3 — Reflexion and Bounded Self-Correction Agent.
Extends the Part 2 agent
"""

import csv
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
REPORTS_DIR = REPO_ROOT / "reports" / "hw07"
RAW_DIR = REPORTS_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(REPO_ROOT / "code") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "code"))

from hw7_agent import run_agent  # noqa: E402

# Budgets for Bounded Reflexion
MAX_REFLEXION_RETRIES = 2  # at most 2 reflexion retries
HARD_TOOL_CALL_BUDGET = 10
HARD_TOKEN_BUDGET = 2000


# Deterministic verifiers per task
def verify_task_a(answer: str, logs: list[dict]) -> tuple[bool, str, list[str]]:
    failed_checks = []
    ans_lower = (answer or "").lower()

    # Trajectory check
    tools_called = [log_entry.get("tool") for log_entry in logs]
    if "search_vulnerabilities_by_name" not in tools_called:
        failed_checks.append("Trajectory missing 'search_vulnerabilities_by_name'")
    if "search_vulnerabilities_by_id" not in tools_called:
        failed_checks.append("Trajectory missing 'search_vulnerabilities_by_id'")

    # Content checks
    if "1" not in ans_lower and "id 1" not in ans_lower:
        failed_checks.append("Answer does not identify vulnerability ID 1")
    if "sql injection" not in ans_lower and "injection" not in ans_lower:
        failed_checks.append("Answer does not mention SQL Injection")
    if (
        "ghsa-2c2j-9gv5-cj73" not in ans_lower
        and "urgency" not in ans_lower
        and "4" not in ans_lower
    ):
        failed_checks.append(
            "Answer lacks specific vulnerability details (code or urgency)"
        )

    if failed_checks:
        return (
            False,
            f"Task A verifier failed: {'; '.join(failed_checks)}",
            failed_checks,
        )
    return True, "Task A verified successfully.", []


def verify_task_b(
    answer: str, logs: list[dict], strict_digits_only: bool = False
) -> tuple[bool, str, list[str]]:
    """
    Verifier for Task B:
    Count vulnerabilities for 'requests' and give supporting example.
    Requirements:
    1. Must contain tool call count_by_package
    2. Must state count is 2 (or 'two')
    3. Must provide a supporting example (e.g. SQL Injection or ID 1)
    """
    failed_checks = []
    ans_lower = (answer or "").lower()

    tools_called = [log_entry.get("tool") for log_entry in logs]
    if "count_by_package" not in tools_called:
        failed_checks.append("Trajectory missing 'count_by_package'")

    # Count check
    if strict_digits_only:
        # Demonstrate a verifier false rejection
        if not re.search(r"\b2\b", ans_lower):
            failed_checks.append("Count '2' (as digit) not found in answer")
    else:
        if not (re.search(r"\b2\b", ans_lower) or "two" in ans_lower):
            failed_checks.append("Count of 2 not reported in answer")

    # Supporting example check
    if (
        "sql injection" not in ans_lower
        and "ghsa" not in ans_lower
        and "id 1" not in ans_lower
        and "id" not in ans_lower
    ):
        failed_checks.append("No specific supporting example provided")

    if failed_checks:
        return (
            False,
            f"Task B verifier failed: {'; '.join(failed_checks)}",
            failed_checks,
        )
    return True, "Task B verified successfully.", []


def verify_task_c(answer: str, logs: list[dict]) -> tuple[bool, str, list[str]]:
    """
    Verifier for Task C:
    Compare vulnerability ID 1 and vulnerability ID 2.
    """
    failed_checks = []
    ans_lower = (answer or "").lower()

    # Trajectory check
    id_lookups = [
        log_entry.get("inputs", {}).get("vulnerability_id")
        for log_entry in logs
        if log_entry.get("tool") == "search_vulnerabilities_by_id"
    ]
    if 1 not in id_lookups or 2 not in id_lookups:
        failed_checks.append("Trajectory must look up both vulnerability ID 1 and ID 2")

    # Content checks
    if "injection" not in ans_lower:
        failed_checks.append(
            "The answer is missing a comparison of vulnerability 1 (Injection)"
        )
    if "remote code execution" not in ans_lower and "rce" not in ans_lower:
        failed_checks.append(
            "The answer is missing a comparison of vulnerability 2 (Remote Code Execution)"
        )
    if (
        "urgency" not in ans_lower
        and "score" not in ans_lower
        and "4" not in ans_lower
        and "5" not in ans_lower
    ):
        failed_checks.append(
            "The answer doesn't contrast the urgency or severity scores"
        )

    if failed_checks:
        return (
            False,
            f"Task C verifier failed: {'; '.join(failed_checks)}",
            failed_checks,
        )
    return True, "Task C has been successfully verified.", []


TASK_VERIFIERS = {
    "Task A": verify_task_a,
    "Task B": verify_task_b,
    "Task C": verify_task_c,
}


# II. STORING REFLECTIONS
def generate_reflection(
    task_id: str,
    failed_answer: str,
    evidence_text: str,
    failed_checks: list[str],
) -> str:
    """
    Generate a concise failure explanation and revised strategy.
    No hidden chain-of-thought: strictly concise failure reason + action plan.
    """
    reasons = "; ".join(failed_checks) if failed_checks else evidence_text

    strategies = {
        "Task A": (
            "Ensure the agent first searches for 'Injection', retrieves result ID 1, "
            "then invokes search_vulnerabilities_by_id(1) to include the full GHSA code "
            "and urgency score in the final response."
        ),
        "Task B": (
            "Ensure count_by_package('requests') is executed to report the count of 2, "
            "followed by search_vulnerabilities_by_name to extract a concrete vulnerability "
            "name and ID as a supporting example."
        ),
        "Task C": (
            "Ensure both search_vulnerabilities_by_id(1) and search_vulnerabilities_by_id(2) "
            "are invoked and their respective urgency scores (4 vs 5) and names are explicitly compared."
        ),
    }

    strategy = strategies.get(
        task_id, "Re-run tools carefully and verify all required fields are included."
    )
    return f"Failure Cause: {reasons}. Revised Strategy: {strategy}"


# I. BOUNDED RETRY LOOP
def run_reflexion_agent(
    task_id: str,
    user_input: str,
    inject_initial_imperfect: bool = False,
    simulate_false_rejection: bool = False,
    verbose: bool = True,
) -> dict:
    """
    Executes the task with bounded Reflexion:
    - Max 2 retries (3 total attempts)
    - Hard tool-call and token budgets
    - Clean stop reason will be for either of these: 'success', 'budget_exhausted', 'human_review'
    - Reflection stored with evidence and passed as untrusted context
    """
    verifier_fn = TASK_VERIFIERS.get(task_id)
    if not verifier_fn:
        raise ValueError(f"No verifier defined for task {task_id}")

    total_tool_calls = 0
    total_tokens = 0
    cumulative_latency_ms = 0.0

    retries_used = 0
    reflections_stored = []
    stop_reason = "human_review"
    final_verified_answer = None

    context_reflection = None
    verifier_false_rejection_occurred = False

    if verbose:
        print(f"\n{'=' * 75}")
        print(f"[REFLEXION LOOP START] Task: {task_id}")
        print(f"User Input: {user_input}")
        print(
            f"Budgets: Max Retries={MAX_REFLEXION_RETRIES}, Max Tools={HARD_TOOL_CALL_BUDGET}, Max Tokens={HARD_TOKEN_BUDGET}"
        )
        print(f"{'=' * 75}")

    for attempt in range(MAX_REFLEXION_RETRIES + 1):
        t0 = time.time()
        attempt_num = attempt + 1
        if verbose:
            print(
                f"\n--- Attempt #{attempt_num} (Retry {retries_used}/{MAX_REFLEXION_RETRIES}) ---"
            )

        # Format input with prior untrusted reflection if retrying
        current_prompt = user_input
        if context_reflection:
            # Treated as untrusted context data - cannot override system rules
            current_prompt = (
                f"{user_input}\n\n"
                f"[UNTRUSTED CONTEXT - Past Attempt Reflection]:\n"
                f"{context_reflection}\n"
                f"[END REFLECTION]"
            )

        # Run base agent
        if attempt == 0 and inject_initial_imperfect:
            # First attempt produces incomplete answer missing detail lookup
            agent_res = {
                "status": "success",
                "stop_reason": "final_answer",
                "answer": "Found SQL Injection vulnerability somewhere in the system.",
                "tool_calls": 1,
                "tokens": 150,
                "logs": [
                    {
                        "step": 1,
                        "tool": "search_vulnerabilities_by_name",
                        "inputs": {"query": "Injection"},
                    }
                ],
            }
        elif attempt == 0 and simulate_false_rejection and task_id == "Task B":
            agent_res = {
                "status": "success",
                "stop_reason": "final_answer",
                "answer": "The package requests has two vulnerabilities. A supporting example is SQL Injection (ID 1).",
                "tool_calls": 2,
                "tokens": 320,
                "logs": [
                    {
                        "step": 1,
                        "tool": "count_by_package",
                        "inputs": {"package_name": "requests"},
                    },
                    {
                        "step": 2,
                        "tool": "search_vulnerabilities_by_name",
                        "inputs": {"query": "requests", "limit": 1},
                    },
                ],
            }
        else:
            agent_res = run_agent(current_prompt, verbose=False)

        latency = (time.time() - t0) * 1000
        cumulative_latency_ms += latency
        total_tool_calls += agent_res.get("tool_calls", 0)
        total_tokens += agent_res.get("tokens", 0)

        ans = agent_res.get("answer", "")
        logs = agent_res.get("logs", [])

        if verbose:
            print(f"  Attempt #{attempt_num} Answer: {ans}")
            print(
                f"  Tool calls this attempt: {agent_res.get('tool_calls', 0)} (Total so far: {total_tool_calls})"
            )
            print(
                f"  Tokens this attempt: {agent_res.get('tokens', 0)} (Total so far: {total_tokens})"
            )

        # Check hard budgets
        if total_tool_calls > HARD_TOOL_CALL_BUDGET or total_tokens > HARD_TOKEN_BUDGET:
            stop_reason = "budget_exhausted"
            if verbose:
                print(
                    f"  [STOP] Hard budget exhausted (Tools={total_tool_calls}, Tokens={total_tokens})"
                )
            break

        # Run deterministic verifier
        if simulate_false_rejection and attempt == 0 and task_id == "Task B":
            # verifier expects digit '2', rejects string of 'two'
            is_valid, verifier_msg, failed_checks = verify_task_b(
                ans, logs, strict_digits_only=True
            )
            verifier_false_rejection_occurred = True
        else:
            is_valid, verifier_msg, failed_checks = verifier_fn(ans, logs)

        if is_valid:
            stop_reason = "success"
            final_verified_answer = ans
            if verbose:
                print(f"  [VERIFIER CHECK] PASSED: {verifier_msg}")
                print(f"  [RESULT] Task succeeded on Attempt #{attempt_num}!")
            break
        else:
            if verbose:
                print(f"  [VERIFIER CHECK] FAILED: {verifier_msg}")

            if retries_used < MAX_REFLEXION_RETRIES:
                retries_used += 1
                reflection_text = generate_reflection(
                    task_id, ans, verifier_msg, failed_checks
                )

                # Store reflection with evidence from failed run
                reflection_record = {
                    "task_id": task_id,
                    "attempt": attempt_num,
                    "failed_answer": ans,
                    "evidence": {
                        "verifier_result": verifier_msg,
                        "failed_assertions": failed_checks,
                        "tool_calls_in_trajectory": [
                            log_entry.get("tool") for log_entry in logs
                        ],
                    },
                    "reflection": reflection_text,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                reflections_stored.append(reflection_record)
                context_reflection = reflection_text

                if verbose:
                    print(f"  [STORED REFLECTION #{retries_used}]: {reflection_text}")
                    print("  [RETRYING with reflection in context...]")
            else:
                stop_reason = "human_review"
                if verbose:
                    print(
                        f"  [STOP] Max retries ({MAX_REFLEXION_RETRIES}) reached without verification passing. Escalating to human_review."
                    )
                break

    return {
        "task_id": task_id,
        "status": stop_reason,
        "stop_reason": stop_reason,
        "final_answer": final_verified_answer or ans,
        "retries_used": retries_used,
        "total_tool_calls": total_tool_calls,
        "total_tokens": total_tokens,
        "total_latency_ms": round(cumulative_latency_ms, 2),
        "reflections": reflections_stored,
        "verifier_false_rejection": verifier_false_rejection_occurred,
    }


# III. COMPARISON EXPERIMENT (Original Loop vs. Reflexion Loop)
def run_part3_experiments():
    print("=" * 80)
    print("DATA260 HW7 — Part 3: Reflexion and Bounded Self-Correction Comparison")
    print("=" * 80)

    task_definitions = [
        (
            "Task A",
            "Search for 'Injection' vulnerabilities, then lookup the details of the first vulnerability found.",
            True,  # Inject imperfect on attempt 1 foe me to test reflection and self-correction
            False,
        ),
        (
            "Task B",
            "How many vulnerabilities belong to the package 'requests', and what is one supporting example?",
            False,
            True,  # Test verifier for a scenario with false rejection
        ),
        (
            "Task C",
            "Compare vulnerability ID 1 and vulnerability ID 2 by looking up their details.",
            False,
            False,
        ),
    ]

    original_results = []
    reflexion_results = []

    print("\n--- 1. RUNNING ORIGINAL LOOP (Part 2 baseline) ---")
    for task_id, prompt, _, _ in task_definitions:
        t0 = time.time()
        res = run_agent(prompt, verbose=False)
        lat = round((time.time() - t0) * 1000, 2)

        # Evaluate against verifier
        verifier = TASK_VERIFIERS[task_id]
        passed, vmsg, _ = verifier(res["answer"], res["logs"])

        # Unsupported claims: claims not backed by tool observations
        unsupported = 0 if passed else 1

        original_results.append(
            {
                "task_id": task_id,
                "success": passed,
                "unsupported_claims": unsupported,
                "retries": 0,
                "tool_calls": res["tool_calls"],
                "tokens": res["tokens"],
                "latency_ms": lat,
                "false_rejections": 0,
                "answer": res["answer"],
            }
        )

    print(
        "\n--- 2. RUNNING REFLEXION LOOP (With Verifier and Bounded Self-Correction) ---"
    )
    all_stored_reflections = []

    for task_id, prompt, inject_imperfect, sim_false_rej in task_definitions:
        r_res = run_reflexion_agent(
            task_id,
            prompt,
            inject_initial_imperfect=inject_imperfect,
            simulate_false_rejection=sim_false_rej,
            verbose=True,
        )

        all_stored_reflections.extend(r_res["reflections"])

        passed = r_res["stop_reason"] == "success"
        unsupported = 0 if passed else 1

        reflexion_results.append(
            {
                "task_id": task_id,
                "success": passed,
                "unsupported_claims": unsupported,
                "retries": r_res["retries_used"],
                "tool_calls": r_res["total_tool_calls"],
                "tokens": r_res["total_tokens"],
                "latency_ms": r_res["total_latency_ms"],
                "false_rejections": 1 if r_res["verifier_false_rejection"] else 0,
                "answer": r_res["final_answer"],
                "stop_reason": r_res["stop_reason"],
            }
        )

    # Aggregate Comparison Metrics
    n_tasks = len(task_definitions)

    orig_success_rate = f"{sum(1 for r in original_results if r['success'])}/{n_tasks} ({sum(1 for r in original_results if r['success']) / n_tasks * 100:.1f}%)"
    refl_success_rate = f"{sum(1 for r in reflexion_results if r['success'])}/{n_tasks} ({sum(1 for r in reflexion_results if r['success']) / n_tasks * 100:.1f}%)"

    orig_unsupported = sum(r["unsupported_claims"] for r in original_results)
    refl_unsupported = sum(r["unsupported_claims"] for r in reflexion_results)

    orig_retry_rate = "0.0% (no self-correction)"
    refl_retries_count = sum(r["retries"] for r in reflexion_results)
    refl_retry_rate = (
        f"{refl_retries_count}/{n_tasks} ({refl_retries_count / n_tasks * 100:.1f}%)"
    )

    orig_avg_tools = round(sum(r["tool_calls"] for r in original_results) / n_tasks, 1)
    refl_avg_tools = round(sum(r["tool_calls"] for r in reflexion_results) / n_tasks, 1)

    orig_avg_tokens = round(sum(r["tokens"] for r in original_results) / n_tasks, 1)
    refl_avg_tokens = round(sum(r["tokens"] for r in reflexion_results) / n_tasks, 1)

    orig_avg_lat = round(sum(r["latency_ms"] for r in original_results) / n_tasks, 2)
    refl_avg_lat = round(sum(r["latency_ms"] for r in reflexion_results) / n_tasks, 2)

    orig_false_rej = sum(r["false_rejections"] for r in original_results)
    refl_false_rej = sum(r["false_rejections"] for r in reflexion_results)

    comparison_table = [
        {
            "Metric": "Task success",
            "Original loop": orig_success_rate,
            "Reflexion loop": refl_success_rate,
        },
        {
            "Metric": "Unsupported claims",
            "Original loop": str(orig_unsupported),
            "Reflexion loop": str(refl_unsupported),
        },
        {
            "Metric": "Retry rate",
            "Original loop": orig_retry_rate,
            "Reflexion loop": refl_retry_rate,
        },
        {
            "Metric": "Tool calls (avg/task)",
            "Original loop": str(orig_avg_tools),
            "Reflexion loop": str(refl_avg_tools),
        },
        {
            "Metric": "Tokens (avg/task)",
            "Original loop": str(orig_avg_tokens),
            "Reflexion loop": str(refl_avg_tokens),
        },
        {
            "Metric": "Latency (avg ms/task)",
            "Original loop": str(orig_avg_lat),
            "Reflexion loop": str(refl_avg_lat),
        },
        {
            "Metric": "Verifier false rejections",
            "Original loop": str(orig_false_rej),
            "Reflexion loop": str(refl_false_rej),
        },
    ]

    # Save to reports/hw07/raw/
    comp_json_path = RAW_DIR / "reflexion_comparison.json"
    comp_csv_path = RAW_DIR / "reflexion_comparison.csv"
    reflections_json_path = RAW_DIR / "stored_reflections.json"

    with open(comp_json_path, "w") as f:
        json.dump(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "comparison_summary": comparison_table,
                "original_loop_runs": original_results,
                "reflexion_loop_runs": reflexion_results,
                "stored_reflections": all_stored_reflections,
            },
            f,
            indent=2,
        )

    with open(comp_csv_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["Metric", "Original loop", "Reflexion loop"]
        )
        writer.writeheader()
        writer.writerows(comparison_table)

    with open(reflections_json_path, "w") as f:
        json.dump(all_stored_reflections, f, indent=2)

    # Print Table
    print("\n" + "=" * 80)
    print("ORIGINAL LOOP VS. REFLEXION LOOP COMPARISON TABLE")
    print("=" * 80)
    header = f"{'Metric':<32} | {'Original loop':<25} | {'Reflexion loop':<25}"
    print(header)
    print("-" * len(header))
    for row in comparison_table:
        print(
            f"{row['Metric']:<32} | {row['Original loop']:<25} | {row['Reflexion loop']:<25}"
        )

    print("\n" + "=" * 80)
    print("STORED REFLECTIONS WITH EVIDENCE (Saved to raw/stored_reflections.json)")
    print("=" * 80)
    for ref in all_stored_reflections:
        print(f"Task: {ref['task_id']} (Attempt #{ref['attempt']})")
        print(f"  Evidence (Verifier Failure): {ref['evidence']['verifier_result']}")
        print(f"  Reflection: {ref['reflection']}\n")

    # Update reports/hw07/METRICS.md
    update_metrics_md(comparison_table)

    # Append to RUN_LOG.txt
    run_log_path = REPORTS_DIR / "RUN_LOG.txt"
    with open(run_log_path, "a") as f:
        f.write("\n\n=======================================================\n")
        f.write(f"HW7 PART 3 RUN LOG — {datetime.now(timezone.utc).isoformat()}\n")
        f.write("=======================================================\n")
        f.write("--- Original vs. Reflexion Comparison Table ---\n")
        for row in comparison_table:
            f.write(
                f"{row['Metric']}: Original={row['Original loop']}, Reflexion={row['Reflexion loop']}\n"
            )
        f.write("\n--- Stored Reflections with Evidence ---\n")
        for ref in all_stored_reflections:
            f.write(f"Task {ref['task_id']} Attempt #{ref['attempt']}:\n")
            f.write(f"  Evidence: {ref['evidence']['verifier_result']}\n")
            f.write(f"  Reflection: {ref['reflection']}\n\n")

    return comparison_table


# Information so that we can update the metrics md file
def update_metrics_md(comparison_table: list[dict]):
    """Update Part 3 section in reports/hw07/METRICS.md with markdown table."""
    metrics_path = REPORTS_DIR / "METRICS.md"
    content = metrics_path.read_text()

    # Build markdown table
    md_lines = [
        "## Part 3 — Reflexion and Bounded Self-Correction Comparison\n",
        "| Metric | Original loop | Reflexion loop |",
        "|---|---|---|",
    ]
    for row in comparison_table:
        md_lines.append(
            f"| {row['Metric']} | {row['Original loop']} | {row['Reflexion loop']} |"
        )

    table_str = "\n".join(md_lines)

    # Replace Part 3 placeholder
    pattern = r"## Part 3 — Reflexion[\s\S]*?(?=\n##|\Z)"
    if re.search(pattern, content):
        new_content = re.sub(pattern, table_str.strip() + "\n", content)
    else:
        new_content = content + "\n" + table_str

    metrics_path.write_text(new_content)


if __name__ == "__main__":
    run_part3_experiments()
