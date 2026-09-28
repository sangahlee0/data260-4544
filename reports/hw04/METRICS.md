# METRICS

## Benchmark Results
| Page size | Version | SQL stmts/req | p50 (ms) | p95 (ms) | p99 (ms) |
|-----------|---------|---------------|----------|----------|----------|
| 10        | naive   | 11            | 33.73    | 37.90    | 40.33    |
| 10        | fixed   | 2             | 1.84     | 2.09     | 2.22     |
| 50        | naive   | 51            | 39.42    | 43.42    | 44.25    |
| 50        | fixed   | 2             | 2.34     | 2.72     | 2.75     |
| 200       | naive   | 201           | 57.87    | 64.37    | 75.98    |
| 200       | fixed   | 2             | 5.39     | 8.90     | 21.63    |

10  → naive 11 queries  vs fixed 2
50  → naive 51 queries  vs fixed 2
200 → naive 201 queries vs fixed 2

### Speed-up Comparison

| Page Size | Naive p50 (ms) | Fixed p50 (ms) | Speed-up |
|-----------|----------------|----------------|----------|
| 10        | 33.73          | 1.84           | 18.33x   |
| 50        | 39.42          | 2.34           | 16.85x   |
| 200       | 57.87          | 5.39           | 10.74x   |

### Speed-up Calculation

**Equation:**

Speed-up = Naive p50 latency / Fixed p50 latency


### Comparison of No RAG, Basic RAG, and Context-engineered RAG

### Configuration

| Setting | Value |
|---|---|
| Documents | 5 |
| Chunks | 121 |
| Chunk Size | 500 |
| Chunk Overlap | 50 |
| Top-k | 3 |
| Embedding Model | sentence-transformers/all-MiniLM-L6-v2 |
| Vector Store | LlamaIndex VectorStoreIndex |
| LLM | qwen2.5:3b |

### Retrieval Results

| Question | Rank 1 | Score | Rank 2 | Score | Rank 3 | Score |
|---|---|---:|---|---:|---|---:|
| Q1 | source3.txt | 0.6443 | source1.txt | 0.3640 | source5.txt | 0.3550 |
| Q2 | source3.txt | 0.7556 | source2.txt | 0.4869 | source2.txt | 0.4684 |
| Q3 | source5.txt | 0.5984 | source4.txt | 0.5340 | source5.txt | 0.4864 |
| Q4 | source5.txt | 0.4828 | source5.txt | 0.4115 | source5.txt | 0.3559 |
| Q5 | source5.txt | 0.4197 | source5.txt | 0.2996 | source5.txt | 0.2047 |
| Q6 | source2.txt | 0.1897 | source1.txt | 0.1738 | source2.txt | 0.1605 |

RELEVANCE_THRESHOLD of 0.30 was chosen based on the initial results, and so any similarity score chunks below 0.3 were excluded.

### Context Size Sweep (Question 3) - k=1,3,5

| k | Chunks Retrieved | Chunks Kept | Chunks Dropped by Relevance Filter | Basic RAG Result | Context RAG Result |
|---:|---:|---:|---:|---|---|
| 1 | 1 | 1 | 0 | Correct | Correct |
| 3 | 3 | 3 | 0 | Correct | Correct |
| 5 | 5 | 5 | 0 | Correct | Incorrect |

The Context-Engineering RAG refused to answer the question at k=5, even though Question 3 should be able to, but they all remained above the relevance threshold. 
More context did not seem to improve results, and k=3 was the best for this situation, as it retrieved the chunks correctly and produced the correct answer without requiring additional context. k=1 is also a good contender, but as Question 3 specifically focuses on similar information across documents, I would choose k=3 as the best k value.

### Three-Configuration Results

| Question | No RAG | Basic RAG | Context-Engineered RAG |
|---|---|---|---|
| Q1 | Answered | Answered | Answered |
| Q2 | Answered | Answered | Answered |
| Q3 | Answered | Answered | Answered |
| Q4 | Answered broadly | Answered using React context | Answered using React context |
| Q5 | Answered from model knowledge | Answered despite missing evidence | Refused |
| Q6 | Answered from model knowledge | Answered despite irrelevant evidence | Refused |

### RAG Evaluation

| Question | Configuration | Correct Retrieval | Correct Answer | Grounded | Refused When Needed |
|---|---|---|---|---|---|
| Q1 | No RAG | N/A | Yes | N/A | N/A |
| Q1 | Basic RAG | Yes | Yes | Yes | N/A |
| Q1 | Context-Engineered RAG | Yes | Yes | Yes | N/A |
| Q2 | No RAG | N/A | No | N/A | N/A |
| Q2 | Basic RAG | Yes | Yes | Yes | N/A |
| Q2 | Context-Engineered RAG | Yes | Yes | Yes | N/A |
| Q3 | No RAG | N/A | Yes | N/A | N/A |
| Q3 | Basic RAG | Yes | Yes | Yes | N/A |
| Q3 | Context-Engineered RAG | Yes | Yes | Yes | N/A |
| Q4 | No RAG | N/A | Yes | N/A | N/A |
| Q4 | Basic RAG | No | No | Yes | N/A |
| Q4 | Context-Engineered RAG | No | No | Yes | N/A |
| Q5 | No RAG | N/A | No | N/A | No |
| Q5 | Basic RAG | No | No | No | No |
| Q5 | Context-Engineered RAG | No | Yes | Yes | Yes |
| Q6 | No RAG | N/A | No | N/A | No |
| Q6 | Basic RAG | No | No | No | No |
| Q6 | Context-Engineered RAG | No | Yes | Yes | Yes |

### Summary Metrics

| Configuration | Accuracy | Faithfulness | Format Compliance | Robustness |
|---|---:|---:|---:|---:|
| No RAG | 50.0% | N/A | N/A | 33.3% |
| Basic RAG | 50.0% | 66.7% | N/A | 0.0% |
| Context-Engineered RAG | 83.3% | 100.0% | 50.0% | 66.7% |

**Metric definitions**
- Accuracy: calculated across 6 evaluation questions
- Faithfulness: whether answer is supported by the context
- Format compliance: adherence to the instructions
- Robustness: measured across q4-q5