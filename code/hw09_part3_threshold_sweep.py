# HW9 Part 3.2: evaluate fixed thresholds against cache_cases.yaml

from __future__ import annotations

import csv
import os
import time
from pathlib import Path

import redis
import yaml
from sentence_transformers import SentenceTransformer

PREFIX = os.environ.get("PREFIX", "s4544")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
SWEEP_PREFIX = f"{PREFIX}:threshold_sweep:"
INDEX_NAME = f"{PREFIX}_threshold_sweep_idx"
DIMENSION = 384
THRESHOLDS = (0.75, 0.80, 0.85, 0.90, 0.95)
ROOT = Path(__file__).resolve().parent.parent
CASES_PATH = ROOT / "reports" / "hw09" / "cache_cases.yaml"
RESULTS_PATH = ROOT / "reports" / "hw09" / "threshold_results.csv"


def ensure_index(client: redis.Redis) -> None:
    from redis.commands.search.field import TagField, TextField, VectorField
    from redis.commands.search.index_definition import IndexDefinition, IndexType

    try:
        client.ft(INDEX_NAME).info()
        return
    except Exception:
        pass

    client.ft(INDEX_NAME).create_index(
        [
            TextField("query"),
            TagField("case_id"),
            VectorField(
                "embedding",
                "FLAT",
                {
                    "TYPE": "FLOAT32",
                    "DIM": DIMENSION,
                    "DISTANCE_METRIC": "COSINE",
                },
            ),
        ],
        definition=IndexDefinition(prefix=[SWEEP_PREFIX], index_type=IndexType.HASH),
    )


def nearest(client: redis.Redis, index_name: str, vector: bytes) -> float | None:
    from redis.commands.search.query import Query

    query = (
        Query("*=>[KNN 1 @embedding $vector AS distance]")
        .sort_by("distance")
        .return_fields("distance")
        .dialect(2)
    )
    result = client.ft(index_name).search(query, query_params={"vector": vector})
    if not result.docs:
        return None
    return 1.0 - float(result.docs[0].distance)


def main() -> None:
    cases = yaml.safe_load(CASES_PATH.read_text(encoding="utf-8"))
    client = redis.Redis.from_url(REDIS_URL, decode_responses=False)
    embedder = SentenceTransformer(
        os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    )
    ensure_index(client)

    # Seed exactly one cached record for each labeled case's cached query.
    for case in cases:
        vector = embedder.encode(
            case["cached_query"], normalize_embeddings=True, convert_to_numpy=True
        )
        client.hset(
            f"{SWEEP_PREFIX}{case['id']}",
            mapping={
                "query": case["cached_query"],
                "case_id": case["id"],
                "embedding": vector.astype("float32").tobytes(),
            },
        )

    rows = []
    for threshold in THRESHOLDS:
        true_hits = false_hits = 0
        latencies = []
        for case in cases:
            started = time.perf_counter()
            vector = embedder.encode(
                case["incoming_query"], normalize_embeddings=True, convert_to_numpy=True
            )
            similarity = nearest(client, INDEX_NAME, vector.astype("float32").tobytes())
            actual_hit = similarity is not None and similarity >= threshold
            expected_hit = case["expected"] == "hit"
            true_hits += int(expected_hit and actual_hit)
            false_hits += int(not expected_hit and actual_hit)
            latencies.append((time.perf_counter() - started) * 1000)

        rows.append(
            {
                "threshold": threshold,
                "hit_rate": true_hits / 20 * 100,
                "false_hit_rate": false_hits / 20 * 100,
                "mean_latency_ms": sum(latencies) / len(latencies),
            }
        )

    with RESULTS_PATH.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print("Threshold,Hit rate,False-hit rate,Mean latency (ms)")
    for row in rows:
        print(
            f"{row['threshold']:.2f},{row['hit_rate']:.1f}%,{row['false_hit_rate']:.1f}%,{row['mean_latency_ms']:.3f}"
        )
    print(f"Saved results to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
