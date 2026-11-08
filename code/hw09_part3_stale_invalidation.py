# HW9 Part 3.5: stale answers and invalidation

from __future__ import annotations

import os
from pathlib import Path

import redis
from hw09_part2_semantic_cache import SemanticResponseCache
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parent.parent
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
QUERY = "What is the urgency score for vulnerability ID 1?"


def main() -> None:
    client = redis.Redis.from_url(REDIS_URL, decode_responses=False)
    embedder = SentenceTransformer(
        os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    )
    record = {
        "id": "s4544_rel_vulnerability_1",
        "vulnerability_id": 1,
        "urgency_score": 9,
    }

    def answer_from_record(_query: str) -> dict[str, str]:
        return {
            "answer": (
                f"Vulnerability ID {record['vulnerability_id']} has urgency score "
                f"{record['urgency_score']}."
            )
        }

    cache = SemanticResponseCache(client, embedder, answer_from_record)
    cache.ensure_index()

    first = cache.answer(QUERY, data_version="s4544-rel-v1")
    record["urgency_score"] = 3
    stale = cache.answer(QUERY, data_version="s4544-rel-v1")
    refreshed = cache.answer(QUERY, data_version="s4544-rel-v2")

    report = f"""\n## 3.5 Stale answers and invalidation

- Versioned record: `{record["id"]}`
- Query: {QUERY}
- Original answer at `s4544-rel-v1`: {first.answer}
- Updated record value: urgency score `{record["urgency_score"]}`
- Stale hit at unchanged version: {stale.answer}
- Invalidation strategy: bump the data-version marker from `s4544-rel-v1` to `s4544-rel-v2` after the record update.
- Refreshed answer after invalidation: {refreshed.answer}
"""
    metrics_path = ROOT / "reports" / "hw09" / "METRICS.md"
    run_log_path = ROOT / "reports" / "hw09" / "RUN_LOG.txt"
    with metrics_path.open("a", encoding="utf-8") as metrics:
        metrics.write(report)
    with run_log_path.open("a", encoding="utf-8") as run_log:
        run_log.write(f"\n--- Part 3.5 stale invalidation ---{report}")
    print(report)


if __name__ == "__main__":
    main()
