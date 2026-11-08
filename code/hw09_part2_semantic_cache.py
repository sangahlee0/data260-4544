"""HW9 Part 2: Redis semantic response cache for the HW8 agent."""

from __future__ import annotations

import os
import time
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable

PREFIX = os.environ.get("PREFIX", "s4544")
THRESHOLD = float(os.environ.get("CACHE_THRESHOLD", "0.85"))
CACHE_PREFIX = f"{PREFIX}:semantic_cache:"
INDEX_NAME = f"{PREFIX}_semantic_idx"
EMBEDDING_DIMENSION = 384


@dataclass
class CacheResponse:
    answer: str
    is_cached: bool
    similarity: float | None
    latency_ms: float
    started_at: str
    finished_at: str
    data_version: str


class SemanticResponseCache:
    # Cache final HW8 answers using RedisSearch cosine similarity
    def __init__(
        self,
        redis_client: Any,
        embedder: Any,
        agent: Callable[[str], dict[str, Any]],
        threshold: float = THRESHOLD,
    ) -> None:
        self.redis = redis_client
        self.embedder = embedder
        self.agent = agent
        self.threshold = threshold

    def ensure_index(self) -> None:
        from redis.commands.search.field import TagField, TextField, VectorField
        from redis.commands.search.index_definition import IndexDefinition, IndexType

        try:
            self.redis.ft(INDEX_NAME).info()
            return
        except Exception:
            pass

        self.redis.ft(INDEX_NAME).create_index(
            [
                TextField("query"),
                TextField("answer"),
                TagField("data_version"),
                VectorField(
                    "embedding",
                    "FLAT",
                    {
                        "TYPE": "FLOAT32",
                        "DIM": EMBEDDING_DIMENSION,
                        "DISTANCE_METRIC": "COSINE",
                    },
                ),
            ],
            definition=IndexDefinition(
                prefix=[CACHE_PREFIX], index_type=IndexType.HASH
            ),
        )

    def _embedding(self, query: str) -> bytes:
        vector = self.embedder.encode(
            query, normalize_embeddings=True, convert_to_numpy=True
        )
        if len(vector) != EMBEDDING_DIMENSION:
            raise ValueError(
                f"Expected {EMBEDDING_DIMENSION}-dimension embedding, got {len(vector)}"
            )
        return vector.astype("float32").tobytes()

    def _nearest(self, vector: bytes) -> tuple[dict[str, Any] | None, float | None]:
        from redis.commands.search.query import Query

        query = (
            Query("*=>[KNN 1 @embedding $vector AS distance]")
            .sort_by("distance")
            .return_fields("query", "answer", "data_version", "distance")
            .dialect(2)
        )
        result = self.redis.ft(INDEX_NAME).search(
            query, query_params={"vector": vector}
        )
        if not result.docs:
            return None, None
        document = result.docs[0]
        return document.__dict__, 1.0 - float(document.distance)

    def answer(self, query: str, data_version: str) -> CacheResponse:
        started_at = datetime.now(timezone.utc).isoformat()
        started = time.perf_counter()
        vector = self._embedding(query)
        cached_record, similarity = self._nearest(vector)

        if (
            cached_record
            and similarity is not None
            and similarity >= self.threshold
            and cached_record.get("data_version") == data_version
        ):
            answer = cached_record["answer"]
            is_cached = True
            print(f"CACHE HIT similarity={similarity:.4f} query={query}")
        else:
            answer = self.agent(query)["answer"]
            is_cached = False
            self.redis.hset(
                f"{CACHE_PREFIX}{time.time_ns()}",
                mapping={
                    "query": query,
                    "answer": answer,
                    "data_version": data_version,
                    "embedding": vector,
                },
            )
            print(f"CACHE MISS similarity={similarity} query={query}")

        finished_at = datetime.now(timezone.utc).isoformat()
        return CacheResponse(
            answer,
            is_cached,
            similarity,
            (time.perf_counter() - started) * 1000,
            started_at,
            finished_at,
            data_version,
        )


def run_required_queries(cache: SemanticResponseCache) -> list[CacheResponse]:
    queries = [
        "What is vulnerability ID 1?",
        "What is vulnerability ID 1?",
        "How many vulnerabilities affect requests?",
        "How many security issues affect the requests package?",
        "What is vulnerability ID 2?",
        "Please provide details for vulnerability ID 2.",
        "How should a team prioritize a high-severity vulnerability?",
        "What package has the most recent release?",
        "What is the weather today?",
        "How do I reset my laptop password?",
    ]
    return [cache.answer(query, data_version="v1") for query in queries]


def main() -> None:
    import domain_agent
    import redis
    from sentence_transformers import SentenceTransformer

    # Keep HW9 agent-run evidence separate from the historical HW5 report.
    domain_agent.AGENT_LOG_PATH = (
        Path(__file__).resolve().parent.parent
        / "reports"
        / "hw09"
        / "raw"
        / "agent_runs.jsonl"
    )

    redis_client = redis.Redis.from_url(
        os.environ.get("REDIS_URL", "redis://localhost:6379/0"), decode_responses=False
    )
    embedder = SentenceTransformer(
        os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    )
    cache = SemanticResponseCache(redis_client, embedder, domain_agent.run_agent)
    cache.ensure_index()
    results = run_required_queries(cache)
    hits = [result for result in results if result.is_cached]
    misses = [result for result in results if not result.is_cached]
    hit_rate = len(hits) / len(results) * 100
    cached_latency = sum(item.latency_ms for item in hits) / len(hits) if hits else 0
    miss_latency = (
        sum(item.latency_ms for item in misses) / len(misses) if misses else 0
    )

    log_path = (
        Path(__file__).resolve().parent.parent / "reports" / "hw09" / "RUN_LOG.txt"
    )
    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"\n--- Part 2 run: {date.today().isoformat()} ---\n")
        for result in results:
            log.write(f"{asdict(result)}\n")
        log.write(f"Cache hit rate: {hit_rate:.1f}% ({len(hits)}/{len(results)})\n")
        log.write(f"Average cached latency: {cached_latency:.3f} ms\n")
        log.write(f"Average non-cached latency: {miss_latency:.3f} ms\n")

    print(f"Cache hit rate: {hit_rate:.1f}% ({len(hits)}/{len(results)})")
    print(f"Average cached latency: {cached_latency:.3f} ms")
    print(f"Average non-cached latency: {miss_latency:.3f} ms")


if __name__ == "__main__":
    main()
