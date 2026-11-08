## 3.2 Threshold sweep

The 40 labeled cases were run at thresholds **0.75, 0.80, 0.85, 0.90, and 0.95**. The measurements below are copied from `threshold_results.csv`

| Threshold | Hit rate | False-hit rate | Mean latency (ms) | Total cost |
|---:|---:|---:|---:|---:|
| 0.75 | 80.0% | 30.0% | 12.348 | 34 |
| 0.80 | 60.0% | 30.0% | 9.910 | 38 |
| 0.85 | 55.0% | 30.0% | 9.059 | 39 |
| 0.90 | 50.0% | 30.0% | 9.711 | 40 |
| 0.95 | 50.0% | 20.0% | 8.003 | 30 |

The hit rate is the percentage of the 20 labeled hit cases that were served from the cache. 
The false-hit rate is the percentage of the 20 labeled miss cases that were incorrectly served from the cache.


## 3.3 False hit

- Case: `similar_different_01`
- Cached query: What is vulnerability ID 1?
- Incoming query: What is vulnerability ID 2?
- Similarity score: 0.9008
- Threshold: 0.85
- Cached answer returned: ID 1 is a SQL Injection vulnerability in requests.
- Correct answer: ID 2 is a Remote Code Execution vulnerability.
- Short explanation: The embedding treated the questions as similar because they use the same sentence structure and are only different when looking at the ID (vulnerability ID). However, because each ID refers to a different database record, the cached answer for ID 1 was incorrect for the question about ID 2.

## 3.4 Cost model and threshold choice

I defined the following relative cost model for this experiment:

- Cache miss cost = **1 unit** because the HW8 agent must run again.
- False-hit cost = **3 units** because an incorrect cached answer creates a correctness and support risk that is modeled as three times the cost of a normal miss.

```text
total cost = (20 - correct hits) × 1 + false hits × 3
```

| Threshold | Correct hits | Misses | False hits | Total cost |
|---:|---:|---:|---:|---:|
| 0.75 | 16 | 4 | 6 | 22 |
| 0.80 | 12 | 8 | 6 | 26 |
| 0.85 | 11 | 9 | 6 | 27 |
| 0.90 | 10 | 10 | 6 | 28 |
| 0.95 | 10 | 10 | 4 | 22 |

Thresholds **0.75 and 0.95 tie** for the lowest total cost at 22 units. 
I would ship **0.95** because it has the lower false-hit rate, even though it has fewer cache hits, and in this situation, aoiding incorrect cached answers is more important than maximizing cache hits.

## 3.5 Stale answers and invalidation

- Versioned record: `s4544_rel_vulnerability_1`
- Query: What is the urgency score for vulnerability ID 1?
- Original answer at `s4544-rel-v1`: Vulnerability ID 1 has urgency score 9.
- Updated record value: urgency score `3`
- Stale hit at unchanged version: Vulnerability ID 1 has urgency score 9.
- Invalidation strategy: bump the data-version marker from `s4544-rel-v1` to `s4544-rel-v2` after the record update.
- Refreshed answer after invalidation: Vulnerability ID 1 has urgency score 3.

The trade-off is that the version markers prevent stale answers without deleting every cache entry, but every update must correctly advance the related data-version marker. 
Stale answers may be served if the marker isn't updated.


## 4.1 Evaluator repair demonstration

```json
{
  "question": "Which version fixes the GitPython command-injection vulnerability?",
  "initial_answer": "GitPython is associated with GHSA-2f96-g7mh-g2hx.",
  "feedback": "Include the fixed version: 3.1.51.",
  "revised_answer": "GitPython has a HIGH severity issue. The fixed version is 3.1.51.",
  "final_evaluation": {
    "result": "PASS",
    "explanation": "The answer includes the required fixed version.",
    "feedback": ""
  },
  "attempts": 2
}
```

## 4.1 Evaluator repair demonstration

```json
{
  "question": "Which version fixes the GitPython command-injection vulnerability?",
  "initial_answer": "GitPython is associated with GHSA-2f96-g7mh-g2hx.",
  "feedback": "Include the fixed version: 3.1.51.",
  "revised_answer": "GitPython has a HIGH severity issue. The fixed version is 3.1.51.",
  "final_evaluation": {
    "result": "PASS",
    "explanation": "The answer includes the required fixed version.",
    "feedback": ""
  },
  "attempts": 2
}
```

## 4.2 Lesson memory demonstration

- Lesson created after the failed answer: `lesson_001`
- Lesson file: `reports/hw09/lessons.json`
- Later question: Which version fixes the GitPython command-injection vulnerability?
- Lessons loaded before answering: ['lesson_001']
- Answer after lesson reuse: The fixed version is 3.1.51.
- Lesson use count after reuse: 1

## 4.3 Validated improvement

- Validation cases: 7
- Correct before lesson: 6/7
- Correct after lesson: 7/7
- Unrelated unsupported-answer regressions: 0
- Lesson kept: `True`
- Decision: The lesson is kept because failure cases improved or remained unchanged, previously correct answers remained correct, and the unrelated question did not receive an unsupported domain answer.

## Part 4 combined run

### 4.1 Evaluator repair
```json
{
  "question": "Which version fixes the GitPython command-injection vulnerability?",
  "initial_answer": "GitPython is associated with GHSA-2f96-g7mh-g2hx.",
  "feedback": "Include the fixed version: 3.1.51.",
  "revised_answer": "GitPython has a HIGH severity issue. The fixed version is 3.1.51.",
  "final_evaluation": {
    "result": "PASS",
    "explanation": "The answer includes the required fixed version.",
    "feedback": ""
  },
  "attempts": 2
}
```

### 4.2 Lesson memory
- Lessons loaded: `['lesson_001']`
- Later answer: GitPython has a HIGH severity issue. The fixed version is 3.1.51.
- Lesson use count: `2`

### 4.3 Validated improvement
- Correct before lesson: `6/7`
- Correct after lesson: `7/7`
- Unrelated regressions: `0`
- Lesson kept: `True`

## Part 4 combined run

### 4.1 Evaluator repair
```json
{
  "question": "Which version fixes the GitPython command-injection vulnerability?",
  "initial_answer": "GitPython is associated with GHSA-2f96-g7mh-g2hx.",
  "feedback": "Include the fixed version: 3.1.51.",
  "revised_answer": "GitPython has a HIGH severity issue. The fixed version is 3.1.51.",
  "final_evaluation": {
    "result": "PASS",
    "explanation": "The answer includes the required fixed version.",
    "feedback": ""
  },
  "attempts": 2
}
```

### 4.2 Lesson memory
- Lessons loaded: `['lesson_001']`
- Later answer: GitPython has a HIGH severity issue. The fixed version is 3.1.51.
- Lesson use count: `3`

### 4.3 Validated improvement
- Correct before lesson: `6/7`
- Correct after lesson: `7/7`
- Unrelated regressions: `0`
- Lesson kept: `True`

### 4.4 Final held-out test comparison
The same `test_data.json` was used independently for all four variants.

| Variant | Correct answers | Incorrect answers | Average attempts | Average latency (ms) |
|---|---:|---:|---:|---:|
| Baseline | 6 | 2 | 1.00 | 0.006 |
| Evaluator Repair | 8 | 0 | 1.25 | 0.004 |
| Lesson Memory | 8 | 0 | 1.00 | 0.003 |
| Validated Improvement | 8 | 0 | 1.00 | 0.003 |


## Part 4 combined run

### 4.1 Evaluator repair
```json
{
  "question": "Which version fixes the GitPython command-injection vulnerability?",
  "initial_answer": "GitPython is associated with GHSA-2f96-g7mh-g2hx.",
  "feedback": "Include the fixed version: 3.1.51.",
  "revised_answer": "GitPython has a HIGH severity issue. The fixed version is 3.1.51.",
  "final_evaluation": {
    "result": "PASS",
    "explanation": "The answer includes the required fixed version.",
    "feedback": ""
  },
  "attempts": 2
}
```

### 4.2 Lesson memory
- Lessons loaded: `['lesson_001']`
- Later answer: GitPython has a HIGH severity issue. The fixed version is 3.1.51.
- Lesson use count: `4`

### 4.3 Validated improvement
- Correct before lesson: `6/7`
- Correct after lesson: `7/7`
- Unrelated regressions: `0`
- Lesson kept: `True`

### 4.4 Final held-out test comparison
The same `test_data.json` was used independently for all four variants.

| Variant | Correct answers | Incorrect answers | Average attempts | Average latency (ms) |
|---|---:|---:|---:|---:|
| Baseline | 6 | 2 | 1.00 | 0.004 |
| Evaluator Repair | 8 | 0 | 1.25 | 0.003 |
| Lesson Memory | 8 | 0 | 1.00 | 0.002 |
| Validated Improvement | 8 | 0 | 1.00 | 0.002 |


## Part 4 combined run

### 4.1 Evaluator repair
```json
{
  "question": "Which version fixes the GitPython command-injection vulnerability?",
  "initial_answer": "GitPython is associated with GHSA-2f96-g7mh-g2hx.",
  "feedback": "Include the fixed version: 3.1.51.",
  "revised_answer": "GitPython has a HIGH severity issue. The fixed version is 3.1.51.",
  "final_evaluation": {
    "result": "PASS",
    "explanation": "The answer includes the required fixed version.",
    "feedback": ""
  },
  "attempts": 2
}
```
- Final response: `GitPython has a HIGH severity issue. The fixed version is 3.1.51.`

### 4.2 Lesson memory
- Lessons loaded: `['lesson_001']`
- Later answer: GitPython has a HIGH severity issue. The fixed version is 3.1.51.
- Lesson use count: `5`

### 4.3 Validated improvement
- Correct before lesson: `6/7`
- Correct after lesson: `7/7`
- Unrelated regressions: `0`
- Lesson kept: `True`

### 4.4 Final held-out test comparison
The same `test_data.json` was used independently for all four variants.

| Variant | Correct answers | Incorrect answers | Average attempts | Average latency (ms) |
|---|---:|---:|---:|---:|
| Baseline | 6 | 2 | 1.00 | 0.005 |
| Evaluator Repair | 8 | 0 | 1.25 | 0.004 |
| Lesson Memory | 8 | 0 | 1.00 | 0.003 |
| Validated Improvement | 8 | 0 | 1.00 | 0.003 |


### Part 4 explanation

- Agent communication: the Answering Agent produces an answer, which the Evaluator Agent uses to compare it with the reference dataset and returns `PASS` or `REVISE` feedback.
- Stopping condition: the repair workflow allows at most two attempts and returns the second result even if it is still `REVISE`.
- Lesson reuse: a repeated failure creates a structured lesson in `lessons.json`. Later questions load matching lessons before answering and increment `use_count`.
- Validation process: the same validation questions are evaluated before and after the lesson, and it is kept only when results improve or remain unchanged and unrelated questions do not receive unsupported domain facts.
- Limitation: this implementation uses deterministic local answering rules rather than a fully generative model, so the measured results may not represent the variability of a production LLM agent.
