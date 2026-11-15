# HW10 evidence folder

## Code and run commands

- `../../code/hw10_evaluate.py`: Part 2 evaluation, Part 3 judge validation, and Part 4 tracing/latency runner
- `../../code/hw10_dashboard.py`: Streamlit operations dashboard
- `../../code/verify-hw10.py`: evidence and artifact verification
- `reproducible_run_instructions`: installation and reproducible commands

## Part 2 evidence

- `evaluation_results.json`: Planner, Writer, and Reviewer evaluation results
- `RUN_LOG.txt`: terminal run log, including Part 2, Part 3, and Part 4 sections

## Part 3 evidence

- `eval_cases.json`: frozen 20 Writer drafts
- `human_labels.csv`: 20 human reference labels
- `judge_runs.json`: raw judge results for all three runs
- `judge_validation.json`: Spearman correlation, mean absolute difference, repeatability, and trust decision

## Part 4 evidence

- `traces.jsonl`: structured trace spans
- `latency_results.csv`: 50 cache-miss latency rows
- `metrics.json`: dashboard summary, trace IDs, and stage-latency metrics

## Report and verification

- `METRICS.md`: report metrics and explanations
- `AI_USE.md`: HW10 AI-use disclosure
- `verification.json`: output from `python code/verify-hw10.py`

