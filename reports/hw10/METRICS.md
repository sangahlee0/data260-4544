# DATA260 HW10 Metrics

## Part 2 - Automated evaluation

The evaluator joins the Planner plan, Writer draft, and Reviewer final message
using the existing HW8 `correlation_id`. The same value is also propagated as
`trace_id` in this evidence run.

- Judge framework: DeepEval
- Metric: GEval
- Local judge model: Ollama `qwen2.5:3b`
- Score scale: 1-5, where 1 is very poor and 5 is excellent
- Timeout: 30 seconds per judge call
- Evidence: `evaluation_results.json`

The plan, Writer draft, and Reviewer final each scored 1/5, rated like this because the demo response restated the question instead of explaining how to prioritize a high-severity vulnerability. The final-vs-draft difference was 0, so the Reviewer did not improve the draft in this test, indicating that the Planner/Writer/Reviewer coordination path is connected, but the demo content needs a stronger domain-specific answer and reviewer revision step.
Run command:

```bash
.venv/bin/python code/hw10_evaluate.py
```


## Part 3 - Validate the judge

- Frozen cases: 20
- Human labels: `human_labels.csv`, committed before judge scores
- Spearman correlation: 0.3143
- Mean absolute difference: 1.95
- Repeatability: 0/20 cases changed across the three runs (0.0%).
- Mean absolute score change: 0
- Maximum absolute score change: 0
- Trust decision: Do not use this judge as the sole deployment gate yet. Require a larger human-labeled set, agreement across multiple judge models, and review of high-impact disagreements first.

## 3.2 Compare judge scores with human labels

The same 20 frozen Writer drafts were scored by DeepEval GEval. The human
labels in `human_labels.csv` were used as the reference set.

- Number of cases: 20
- Spearman rank correlation: **0.3143**
- Mean absolute difference: **1.95**
- Raw recomputable data: `judge_validation.json` under `raw_case_data`
- Full repeated raw outputs: `judge_runs.json`

### Raw per-case comparison from Run 1

| Case | Human label | Judge score | Absolute difference |
|---|---:|---:|---:|
| case_01 | 5 | 4 | 1 |
| case_02 | 5 | 1 | 4 |
| case_03 | 5 | 1 | 4 |
| case_04 | 5 | 4 | 1 |
| case_05 | 5 | 1 | 4 |
| case_06 | 5 | 1 | 4 |
| case_07 | 5 | 1 | 4 |
| case_08 | 5 | 1 | 4 |
| case_09 | 5 | 1 | 4 |
| case_10 | 5 | 1 | 4 |
| case_11 | 2 | 1 | 1 |
| case_12 | 2 | 1 | 1 |
| case_13 | 2 | 1 | 1 |
| case_14 | 2 | 1 | 1 |
| case_15 | 2 | 1 | 1 |
| case_16 | 1 | 1 | 0 |
| case_17 | 1 | 1 | 0 |
| case_18 | 1 | 1 | 0 |
| case_19 | 1 | 1 | 0 |
| case_20 | 1 | 1 | 0 |

The Spearman correlation was computed from the 20 human labels and the 20
judge scores in this table. The mean absolute difference was computed as the
mean of the final column.

## 3.3 Test repeatability

The judge ran three times with the same 20 drafts, the same prompts, the same
Ollama model, temperature 0, and the same 30-second timeout.

- Number of runs: 3
- Cases with any score change: **0/20**
- Score-change rate: **0%**
- Mean absolute score change: **0**
- Maximum absolute score change: **0**

The judge showed weak agreement with the human reference labels, with a Spearman correlation of 0.3143 and an average difference of 1.95 points. Due to this, it should not be used as the sole deployment gate, but it was perfectly repeatable in this experiment. None of the 20 cases changed score across the three runs, and both the mean and maximum score changes were 0. Before using the judge for deployment decisions, I would collect a larger and more diverse human-labeled set, use a second independent human reviewer, test additional judge models or prompts, and manually review high-impact disagreements.


## Part 4
| Stage | p50 (ms) | p95 (ms) | % of cache-miss end-to-end |
|---|---:|---:|---:|
| Cache lookup | 0.005 | 0.008 | 0.03% |
| Planner | 3.148 | 3.794 | 20.79% |
| Writer | 5.463 | 6.406 | 36.08% |
| Reviewer | 2.754 | 3.287 | 18.19% |
| Queue wait (total) | 1.649 | 2.285 | 10.89% |
| Evaluation | 2.394 | 2.909 | 15.81% |

The Writer was the dominant contributor at 36.08% of cache-miss latency, so I would optimize the Writer stage first. Cache-hit latency was measured separately at 0.114 ms.
The percentages use p50 stage latency divided by p50 total cache-miss end-to-end latency.