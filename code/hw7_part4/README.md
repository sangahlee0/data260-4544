# HW7 Part 4: Bay Wheels MRKL/ReAct Analyzer

Standalone LangGraph app for comparing Bay Wheels monthly membership and pay-per-use cost estimates from a trip CSV and Lyft Bike's official pricing page.

## Run

From the repository root:

```bash
/Users/sangah/Desktop/Data260/venv/bin/python -m pip install -r code/hw7_part4/requirements.txt
/Users/sangah/Desktop/Data260/venv/bin/uvicorn hw7_part4.main:app --app-dir code --reload --port 8054
```

Open `http://127.0.0.1:8054` and upload a Bay Wheels CSV with at least 500 trip rows. The default policy URL is `https://lyftbikes.com/pricing`; only official Lyft Bike HTTPS hosts are accepted.

## Tools

The three tools and JSON schemas are in `agent.py`. Their outputs use the common `{success, data?, error?, source?, ts?}` envelope. CSV SQL allows read-only `SELECT` queries; the calculator parses a restricted arithmetic AST without `eval`; and policy retrieval stores the extracted page text with a timestamp and SHA-256 under `raw/pricing_snapshots/`.

## Acceptance scenarios

Run the two 600-row synthetic usage profiles with:

```bash
/Users/sangah/Desktop/Data260/venv/bin/python -m hw7_part4.acceptance
```

The generated CSVs and per-run output are under `code/hw7_part4/raw/`. The scenarios test opposite recommendations and use the public Bay Wheels field names; they are intentionally synthetic and are not represented as an individual rider's real trips. For actual analysis, download trip data from `https://lyftbikes.com/system-data` and upload the CSV.

## Tests

```bash
/Users/sangah/Desktop/Data260/venv/bin/python -m unittest hw7_part4.test_agent
```