# AI_USE - HW10

### (1) What I used an AI assistant for and what I did myself
I used an AI assistant to help me understand the HW10 requirements, organize the extension from HW8 and HW9, and analyze the results and calculations.
I reviewed the terminal output, inspected the generated JSON/CSV files, and decided what
evidence and explanations belong in the report based on results.

### (2) One AI-produced output that was wrong or unsuitable, or one thing I independently verified
The first evaluator used a custom local scoring function instead of the required DeepEval GEval metric because I missed it but was able to and was asking for recommendations. However, that
was unsuitable for the assignment because HW10 explicitly requires GEval/DeepEval.

### (3) How I detected the problem or verified the result
I compared the evaluator implementation with the exact HW10 instructions and identified that the custom scoring function was not GEval. I checked that Ollama had the `qwen2.5:3b` model installed, installed DeepEval and its Ollama adapter in the project environment, and reran the evaluator. The saved scores now identify `DeepEval GEval with Ollama` as the judge source.
I also verified that the 20 evaluation cases and 20 human-label rows were frozen and committed before judge scoring. I ran the judge three times on the same cases, checked the raw per-case data, and ran `verify-hw10.py`. The verification checks passed for the case count, judge runs, trace spans, 50 latency rows, trace examples, and latency stages.

### (4) What I changed and why it works now
I replaced the custom fallback judge with DeepEval GEval using the local Ollama model and kept a bounded timeout. The evaluator now stops with an error if a message is malformed or the judge fails instead of inventing a score.
I also added the required Part 3 comparison and repeatability calculations, including Spearman correlation, mean absolute difference, raw per-case data, three repeated runs, score-change counts, and the deployment trust decision. I also added structured trace output, cache-hit and cache-miss examples, a failed trace, the 50-request latency experiment, and dashboard fields for the trace IDs and stage metrics.
