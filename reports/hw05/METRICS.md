# HW05 Metrics

## Fault-Injection Results

| Injected Failure Rate | Success Rate | Mean Latency (ms) | p99 Latency (ms) |
|---|---:|---:|---:|
| 0% | 100.00% | 1.31 | 13.65 |
| 20% | 98.00% | 56.88 | 315.39 |
| 50% | 82.00% | 140.47 | 317.56 |


## Part 5 - Agent Scenario Metrics

| Scenario | Step Count | Stop Reason | Tool-Call Count |
|---|---:|---|---:|
| Count vulnerabilities associated with requests | 2 | completed | 1 |
| Find vulnerabilities with Injection in the name | 2 | completed | 1 |
| Find vulnerability with ID 1 | 2 | invalid_json | 1 |
| Search for vulnerabilities with an empty name | 1 | invalid_json | 0 |