from __future__ import annotations
import json
import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "reports" / "hw10"
OUTPUT_PATH = REPORT_DIR / "evaluation_results.json"
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
    #Run DeepEval GEval with the local Ollama model and convert 0-1 to 1-5 for the assignment
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
        raise ValueError("Planner, Writer, and Reviewer messages require correlation_id")
    ids = {planner["correlation_id"], writer["correlation_id"], final["correlation_id"]}
    if len(ids) != 1:
        raise ValueError("Planner, Writer, and Reviewer messages do not share correlation_id")
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
        interpretation = "The Reviewer output stayed at the same judged quality as the draft."
    else:
        interpretation = "The Reviewer output scored lower than the Writer draft; coordination needs review."

    return {
        "correlation_id": planner["correlation_id"],
        "trace_id": planner["trace_id"],
        "judge": {"name": JUDGE_NAME, "framework": "DeepEval", "metric": "GEval", "model": JUDGE_MODEL, "scale": "1-5", "timeout_seconds": JUDGE_TIMEOUT_SECONDS},
        "question": question,
        "plan": planner,
        "draft": writer,
        "final": final,
        "scores": {
            "plan_quality": plan_result,
            "writer_helpfulness": {**draft_result, "trace_id": writer["trace_id"]},
            "final_answer_helpfulness": {**final_result, "final_answer": final["answer"]},
            "final_vs_draft_improvement": {
                "draft_score": draft_result["score"],
                "final_score": final_result["score"],
                "difference": difference,
                "interpretation": interpretation,
            },
        },
    }

def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    print("DATA260 HW10 Part 2")
    question = "How should a team prioritize a high-severity vulnerability?"
    planner, writer, final = build_messages(question)
    result = evaluate_messages(planner, writer, final)
    output = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cases": [result],
        "interpretation": result["scores"]["final_vs_draft_improvement"]["interpretation"],
        "notes": "DeepEval GEval uses the local Ollama qwen2.5:3b model. The run stops with an error if a message is malformed or GEval times out/fails.",
    }
    OUTPUT_PATH.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))
    print(f"Saved evaluation evidence to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

