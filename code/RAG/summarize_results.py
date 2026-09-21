from pathlib import Path
import json
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR.parent.parent / "reports" / "hw03" / "raw"
print(f"Saving files to: {RAW_DIR}")

rows = []

for path in RAW_DIR.glob("*_results.json"):
    data = json.loads(path.read_text(encoding="utf-8"))

    for result in data["results"]:
        rows.append({
            "technique": data["technique"],
            "retrieval_latency_ms": data["retrieval_latency_ms"],
            "store_score": result["store_score"],
            "cosine_sim": result["cosine_sim"],
            "chunk_len": result["chunk_len"]
        })

df = pd.DataFrame(rows)

summary = df.groupby("technique").agg({
    "retrieval_latency_ms": "mean",
    "store_score": "mean",
    "cosine_sim": "mean",
    "chunk_len": "mean"
}).reset_index()

print(summary)

summary.to_csv(RAW_DIR / "summary.csv", index=False)
print(f"\nSaved summary to: {RAW_DIR / 'summary.csv'}")