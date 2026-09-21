# Retrieval Metrics

The three chunking techniques (token, semantic, and sentence-window) were evaluated using five questions and
top-k retrieval with `k = 3`.

| Technique | Chunks | Avg chunk length | Top-1 cosine | Mean@3 cosine | Recall@3 | Mean retrieval latency (ms) |
|---|---:|---:|---:|---:|---:|---:|
| Token | 3,615 | 542.61 | 0.6620 | 0.5671 | 0.80 | 43.74 |
| Semantic | 826 | 1,970.38 | 0.5892 | 0.4483 | 0.80 | 13.89 |
| Sentence-window | 13,165 | 123.63 | 0.6543 | 0.5478 | 1.00 | 126.77 |
