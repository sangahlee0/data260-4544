import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

import csv
import random
import time
import numpy as np
import statistics

from web_application.backend.database import SessionLocal
from web_application.backend.models import Vulnerability
from mcp_server.domain_server import run_with_retries


VERIFY_SEED = 264544
# Simulation failurs at rates of 0%. 20%, and 50% of calls, with 50 calls at each failure rate.
FAILURE_RATES = [0.0, 0.2, 0.5]
FAILURE_CALLS_COUNT = 50

REPO_ROOT = Path(__file__).resolve().parent.parent
output_dir = REPO_ROOT / "reports" / "hw05" / "raw"


def run_benchmark_call(db, rng, failure_rate):
    def operation():
        # Simulate a storage failure
        if rng.random() < failure_rate:
            raise RuntimeError("Simulated storage failure")

        # Real storage operation
        return db.query(Vulnerability).first()

    return run_with_retries(operation)

def main():
    all_results = []
    summary_results = []

    db = SessionLocal()

    try:
        for failure_rate in FAILURE_RATES:

            # Same seed gives reproducible failure sequences
            rng = random.Random(VERIFY_SEED)

            rate_results = []

            for test_number in range(1, FAILURE_CALLS_COUNT + 1):

                start = time.perf_counter()

                try:
                    run_benchmark_call(db, rng, failure_rate)

                    success = True

                except Exception:
                    success = False

                latency_ms = (time.perf_counter() - start) * 1000

                result = {
                    "failure_rate": failure_rate,
                    "test_number": test_number,
                    "success": success,
                    "latency_ms": latency_ms
                }

                all_results.append(result)
                rate_results.append(result)

            # Metrics for the current failure rate
            successful_calls = sum(
                1 for result in rate_results
                if result["success"])
            
            success_rate = (successful_calls / FAILURE_CALLS_COUNT) * 100

            latencies = [
                result["latency_ms"]
                for result in rate_results
            ]

            mean_latency = statistics.mean(latencies)

            p99_latency_res = np.percentile(latencies, 99)

            # Summary for the chart and console output
            summary_results.append({
                "failure_rate": failure_rate,
                "success_rate": success_rate,
                "mean_latency_ms": mean_latency,
                "p99_latency_ms": p99_latency_res
            })

    finally:
        db.close()

    # Save raw data in reports/hw05/raw
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "retry_results.csv"

    with open(output_file, "w", newline="") as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "failure_rate",
                "test_number",
                "success",
                "latency_ms"
            ]
        )

        writer.writeheader()
        writer.writerows(all_results)

    print("\nSimulation Results")

    for result in summary_results:
        print(
            f"Injected failure rate: {result['failure_rate'] * 100:.0f}% | "
            f"Success rate: {result['success_rate']:.2f}% | "
            f"Mean latency: {result['mean_latency_ms']:.2f} ms | "
            f"p99 latency: {result['p99_latency_ms']:.2f} ms"
        )

if __name__ == "__main__":
    main()