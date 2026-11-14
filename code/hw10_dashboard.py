from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "reports" / "hw10"
METRICS_PATH = REPORT_DIR / "metrics.json"
EVALUATION_PATH = REPORT_DIR / "evaluation_results.json"
TRACE_PATH = REPORT_DIR / "traces.jsonl"

st.set_page_config(page_title="DATA260 HW10 Operations", layout="wide")


@st.cache_data
def load_json(path_string: str) -> dict:
    path = Path(path_string)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


@st.cache_data
def load_jsonl(path_string: str) -> list[dict]:
    path = Path(path_string)
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


metrics = load_json(str(METRICS_PATH))
evaluation = load_json(str(EVALUATION_PATH))
traces = load_jsonl(str(TRACE_PATH))

page = st.sidebar.radio("Page", ["Summary", "Evaluation", "Trace lookup"])
st.sidebar.caption("Data source: local JSON/JSONL files in reports/hw10")

if page == "Summary":
    st.title("DATA260 HW10 Operations Dashboard")
    st.write("System health and evidence from the HW8/HW9 pipeline.")

    window = metrics.get("time_window", "Not available yet")
    source = metrics.get("data_source", "reports/hw10/metrics.json")
    st.info(f"Time window: {window} | Data source: {source}")

    values = metrics.get("summary", {})
    columns = st.columns(5)
    columns[0].metric("Recent requests", values.get("recent_request_count", "N/A"))
    columns[1].metric("Cache hit rate", f"{values.get('cache_hit_rate_pct', 'N/A')}%")
    columns[2].metric("Cache hits", values.get("cache_hits", "N/A"))
    columns[3].metric("Cache misses", values.get("cache_misses", "N/A"))
    columns[4].metric("Error rate", f"{values.get('error_rate_pct', 'N/A')}%")

    st.subheader("Latency")
    latency = values.get("latency", {})
    st.dataframe(
        pd.DataFrame([latency]) if latency else pd.DataFrame(), use_container_width=True
    )
    stage_latency = metrics.get("stage_latency_experiment", [])
    if stage_latency:
        st.subheader("50-request cache-miss stage latency")
        st.dataframe(pd.DataFrame(stage_latency), use_container_width=True)
        st.write(
            f"Dominant contributor: **{metrics.get('dominant_contributor', 'N/A')}**"
        )
    trace_examples = metrics.get("trace_examples", {})
    if trace_examples:
        st.subheader("Required trace examples")
        st.json(trace_examples)
    st.caption(
        "Each metric is labeled by the time window and local evidence file above."
    )

elif page == "Evaluation":
    st.title("Evaluation")
    if not evaluation:
        st.warning("No evaluation_results.json has been generated yet.")
    else:
        st.subheader("Pipeline evaluation")
        st.dataframe(
            pd.DataFrame(evaluation.get("cases", [])), use_container_width=True
        )
        st.subheader("Judge validation")
        st.json(evaluation.get("judge_validation", {}))
        st.subheader("Interpretation")
        st.write(evaluation.get("interpretation", "Not available yet."))

else:
    st.title("Trace lookup")
    trace_id = st.text_input("Enter trace_id")
    trace_rows = [
        row for row in traces if not trace_id or row.get("trace_id") == trace_id
    ]
    if not trace_rows:
        st.info("Enter one of the available trace IDs, or generate traces first.")
    else:
        table = pd.DataFrame(trace_rows)
        expected = [
            "trace_id",
            "stage",
            "start_time",
            "end_time",
            "duration_ms",
            "status",
            "error",
            "cache_path",
        ]
        st.dataframe(
            table[[c for c in expected if c in table.columns]], use_container_width=True
        )
        st.subheader("Journey in stage order")
        for row in trace_rows:
            label = f"{row.get('stage', 'unknown')} - {row.get('status', 'unknown')}"
            with st.expander(label, expanded=True):
                st.json(row)
