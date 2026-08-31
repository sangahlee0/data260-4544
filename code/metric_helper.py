"""
Reads reports/hw01/raw/nondeterminism_results.json and computes the metrics required by Part 3.
Writes a markdown table directly into reports/hw01/METRICS.md.
"""

import json
import numpy as np

with open("reports/hw01/raw/nondeterminism_results.json", "r") as f:
    all_runs = json.load(f)

# Separate the runs by temperature for the table
t7_run = [r for r in all_runs if r["temperature"] == 0.7]
t0_run = [r for r in all_runs if r["temperature"] == 0.0]


def calculate_metrics(run_list):
    # Count how many unique tag combinations happened
    tag_combinations = []
    for r in run_list:
        # Sort the tags
        sorted_tags = tuple(sorted(r["tags"]))
        tag_combinations.append(sorted_tags)
    # Count the number of distinct tag combinations
    distinct_count = len(set(tag_combinations))

    # Tags in all 20 runs for each temperature
    common_tags = set(run_list[0]["tags"])
    for r in run_list:
        common_tags = common_tags.intersection(set(r["tags"]))

    tag_counts = {}
    for r in run_list:
        for tag in r["tags"]:
            if tag in tag_counts:
                tag_counts[tag] += 1
            else:
                tag_counts[tag] = 1

    # Tags in exactly 1 run for each temperature
    single_tags = []
    for tag, count in tag_counts.items():
        if count == 1:
            single_tags.append(tag)

    # Latency percentiles for each temperature
    latencies = [r["latency_ms"] for r in run_list]
    p50 = np.percentile(latencies, 50)
    p95 = np.percentile(latencies, 95)
    p99 = np.percentile(latencies, 99)

    return distinct_count, sorted(list(common_tags)), single_tags, p50, p95, p99

# Get metrics for both temperatures
t7_dist, t7_all, t7_single, t7_p50, t7_p95, t7_p99 = calculate_metrics(t7_run)
t0_dist, t0_all, t0_single, t0_p50, t0_p95, t0_p99 = calculate_metrics(t0_run)

# Build table in markdown format
markdown_content = f"""## Non-Determinism Metrics

### Temperature 0.7
| Metric | Value |
|---|---|
| Distinct tag sets | {t7_dist} |
| Tags in all 20 runs | {', '.join(t7_all) or '(none)'} |
| Tags in exactly 1 run | {', '.join(t7_single) or '(none)'} |

### Temperature 0.0
| Metric | Value |
|---|---|
| Distinct tag sets | {t0_dist} |
| Tags in all 20 runs | {', '.join(t0_all) or '(none)'} |
| Tags in exactly 1 run | {', '.join(t0_single) or '(none)'} |


### Side-by-Side Comparison of Temperatures 0.7 and 0.0 latency and metrics
| Metric | Temp 0.7 | Temp 0.0 |
|---|---|---|
| Distinct tag sets | {t7_dist} | {t0_dist} |
| Tags in all 20 runs | {', '.join(t7_all) or '(none)'} | {', '.join(t0_all) or '(none)'} |
| Tags in exactly 1 run | {', '.join(t7_single) or '(none)'} | {', '.join(t0_single) or '(none)'} |
| Latency p50 (ms) | {t7_p50:.1f} | {t0_p50:.1f} |
| Latency p95 (ms) | {t7_p95:.1f} | {t0_p95:.1f} |
| Latency p99 (ms) | {t7_p99:.1f} | {t0_p99:.1f} |
"""
# save it into the METRICS.md file
with open("reports/hw01/METRICS.md", "w") as f:
    f.write(markdown_content)

print("Successfully generated table in reports/hw01/METRICS.md")