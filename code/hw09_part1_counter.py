from __future__ import annotations

import logging
import sys
from collections.abc import Callable
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class VulnerabilityViewCounter:
    # Count vulnerability accesses in Redis and checkpoint every 10 hits
    def __init__(
        self,
        redis_client: Any,
        session_factory: Callable[[], Any],
        prefix: str = "s4544",
        entity_model: Any | None = None,
    ) -> None:
        self.redis_client = redis_client
        self.session_factory = session_factory
        self.prefix = prefix
        self.entity_model = entity_model

    def increment_vulnerability_views(self, vulnerability_id: int) -> int:
        # Increment Redis and persist the durable count on every 10th hit
        key = f"{self.prefix}:views:vulnerability:{vulnerability_id}"
        count = int(self.redis_client.incr(key))

        if count % 10 == 0:
            db = self.session_factory()
            try:
                model = self.entity_model
                if model is None:
                    from web_application.backend.models import Vulnerability

                    model = Vulnerability
                vulnerability = (
                    db.query(model).filter(model.id == vulnerability_id).one()
                )
                vulnerability.view_count = count
                db.commit()
                logger.info(
                    "Synced views to database: vulnerability_id=%s count=%s",
                    vulnerability_id,
                    count,
                )
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()

        return count


class DemoRedis:
    def __init__(self) -> None:
        self.values: dict[str, int] = {}

    def incr(self, key: str) -> int:
        self.values[key] = self.values.get(key, 0) + 1
        return self.values[key]


class DemoRow:
    def __init__(self, row_id: int) -> None:
        self.id = row_id
        self.view_count = 0


class DemoModel:
    id = object()


class DemoQuery:
    def __init__(self, row: DemoRow) -> None:
        self.row = row

    def filter(self, *_args: Any, **_kwargs: Any) -> "DemoQuery":
        return self

    def one(self) -> DemoRow:
        return self.row


class DemoSession:
    def __init__(self, row: DemoRow) -> None:
        self.row = row

    def query(self, _model: Any) -> DemoQuery:
        return DemoQuery(self.row)

    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass

    def close(self) -> None:
        pass


if __name__ == "__main__":
    run_log_path = (
        Path(__file__).resolve().parent.parent / "reports" / "hw09" / "RUN_LOG.txt"
    )
    run_log_path.parent.mkdir(parents=True, exist_ok=True)

    class Tee:
        def __init__(self, *streams: Any) -> None:
            self.streams = streams

        def write(self, text: str) -> int:
            for stream in self.streams:
                stream.write(text)
                stream.flush()
            return len(text)

        def flush(self) -> None:
            for stream in self.streams:
                stream.flush()

    with run_log_path.open("a", encoding="utf-8") as run_log:
        run_log.write(f"\n--- Part 1 run: {date.today().isoformat()} ---\n")
        terminal_and_log = Tee(sys.stdout, run_log)
        error_and_log = Tee(sys.stderr, run_log)
        with redirect_stdout(terminal_and_log), redirect_stderr(error_and_log):
            logging.basicConfig(level=logging.INFO, format="%(message)s")
            print(
                "Command: PYTHONPATH=data260-4544/code python3 data260-4544/code/hw09_part1_counter.py"
            )
            row = DemoRow(row_id=1)
            counter = VulnerabilityViewCounter(
                redis_client=DemoRedis(),
                session_factory=lambda: DemoSession(row),
                entity_model=DemoModel,
            )
            print("=== Testing Counter ===")
            for access_number in range(1, 26):
                total = counter.increment_vulnerability_views(vulnerability_id=1)
                print(f"Access #{access_number}: Total = {total}")
                if total % 10 == 0:
                    print("✓ Synced views to database")

            print(f"Database checkpoint after 25 accesses: {row.view_count}")
