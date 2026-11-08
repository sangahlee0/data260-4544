# HW9 Part 3.3: document one measured false hit at threshold 0.85

from __future__ import annotations

import os
from pathlib import Path

import redis
import yaml
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parent.parent
PREFIX = os.environ.get("PREFIX", "s4544")
INDEX_NAME = f"{PREFIX}_threshold_sweep_idx"
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
THRESHOLD = 0.85


def find_match(client: redis.Redis, vector: bytes) -> tuple[str, float]:
    from redis.commands.search.query import Query

    query = (
        Query("*=>[KNN 1 @embedding $vector AS distance]")
        .sort_by("distance")
        .return_fields("query", "distance")
        .dialect(2)
    )
    result = client.ft(INDEX_NAME).search(query, query_params={"vector": vector})
    document = result.docs[0]
    return str(document.query), 1.0 - float(document.distance)


def main() -> None:
    cases_path = ROOT / "reports" / "hw09" / "cache_cases.yaml"
    metrics_path = ROOT / "reports" / "hw09" / "METRICS.md"
    run_log_path = ROOT / "reports" / "hw09" / "RUN_LOG.txt"
    cases = yaml.safe_load(cases_path.read_text(encoding="utf-8"))
    client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    embedder = SentenceTransformer(
        os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    )

    case = next(case for case in cases if case["id"] == "similar_different_01")
    for key in client.scan_iter(match=f"{PREFIX}:threshold_sweep:*"):
        client.delete(key)
    cached_vector = (
        embedder.encode(
            case["cached_query"], normalize_embeddings=True, convert_to_numpy=True
        )
        .astype("float32")
        .tobytes()
    )
    client.hset(
        f"{PREFIX}:threshold_sweep:{case['id']}",
        mapping={
            "query": case["cached_query"],
            "case_id": case["id"],
            "embedding": cached_vector,
        },
    )
    incoming_vector = (
        embedder.encode(
            case["incoming_query"], normalize_embeddings=True, convert_to_numpy=True
        )
        .astype("float32")
        .tobytes()
    )
    cached_query, similarity = find_match(client, incoming_vector)
    if similarity < THRESHOLD:
        raise RuntimeError(
            f"The selected case was not a false hit: similarity={similarity:.4f}"
        )
    answers = {
        "What is vulnerability ID 1?": "ID 1 is a SQL Injection vulnerability in requests.",
        "What is vulnerability ID 2?": "ID 2 is a Remote Code Execution vulnerability.",
    }
    cached_answer = answers.get(cached_query, "Cached answer not available.")
    correct_answer = answers.get(
        case["incoming_query"], "Correct answer not available."
    )
    report = f"""## 3.3 False hit

- Case: `{case["id"]}`
- Cached query: {cached_query}
- Incoming query: {case["incoming_query"]}
- Similarity score: {similarity:.4f}
- Threshold: {THRESHOLD:.2f}
- Cached answer returned: {cached_answer}
- Correct answer: {correct_answer}
- Explanation: [observation about why the embedding confused these two different vulnerability records]
"""
    with metrics_path.open("a", encoding="utf-8") as metrics:
        metrics.write(f"\n{report}")
    with run_log_path.open("a", encoding="utf-8") as run_log:
        run_log.write(f"\n--- Part 3.3 false-hit report ---\n{report}")
    print(report)
    print(f"Appended report to {metrics_path}")
    print(f"Appended report to {run_log_path}")


if __name__ == "__main__":
    main()
