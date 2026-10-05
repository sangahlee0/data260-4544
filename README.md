# data260-4544
## Sang Ah Lee
DATA-260 Section 22  
Student ID: 012634544  

## Configurations and Domain
SID4: 4544
PORT_BASE: 8044
PREFIX: s4544
SEED: 4544
VERIFY_SEED: 264544
DOMAIN_ID: 4 (Open_source package vulnerabilities)

## Hardware/Model Information
Hardware: Apple M3, 16GB
Model: qwen2.5:3b (switched from qwen3.8b due to hardware issues)

## Project Directory Structure

```text
data260-4544/
├── code/
│   ├── Dockerfile
│   ├── RAG/
│   │   ├── corpus/
│   │   │   ├── *.json
│   │   │   └── shakespeare.txt
│   │   ├── corpus_manifest_create.py
│   │   ├── pypi_vulnerabilities.zip
│   │   ├── rag_pipeline.py
│   │   └── summarize_results.py
│   ├── agentgraph_demo.py
│   ├── agents_demo.py
│   ├── domain_agent.py
│   ├── hw1_client.py
│   ├── hw2experiment_run.py
│   ├── hw4_benchmark.py
│   ├── metric_helper.py
│   ├── nodes.py
│   ├── rag.py
│   ├── reports/
│   │   └── hw01/
│   │       └── verification.json
│   ├── router.py
│   ├── simulate_failures_mcp.py
│   ├── state.py
│   ├── test_execute_tool.py
│   ├── validateplanner.py
│   ├── verify-hw01.py
│   ├── verify-hw02.py
│   ├── verify-hw03.py
│   ├── verify-hw04.py
│   ├── verify-hw05.py
│   ├── workflow.py
│   └── web_application/
│       ├── index.html
│       ├── main.py
│       ├── routers/
│       │   ├── api_auth.py
│       │   └── auth.py
│       ├── script.js
│       ├── style.css
│       ├── templates/
│       │   ├── dashboard.html
│       │   ├── home.html
│       │   └── login.html
│       ├── backend/
│       │   ├── __init__.py
│       │   ├── crud.py
│       │   ├── database.py
│       │   ├── models.py
│       │   ├── schema.py
│       │   ├── seed.py
│       │   └── session_crud.py
│       └── frontend/
│           ├── index.html
│           ├── package.json
│           ├── package-lock.json
│           ├── vite.config.js
│           └── src/
│               ├── api/
│               │   ├── axios.js
│               │   └── usersApi.js
│               ├── app.jsx
│               ├── components/
│               │   └── Login.jsx
│               ├── features/
│               │   └── vulnerabilities/
│               │       └── vulnerabilitiesSlice.js
│               ├── main.jsx
│               ├── pages/
│               │   ├── createRecord.jsx
│               │   ├── deleteRecord.jsx
│               │   ├── Home.jsx
│               │   └── updateRecord.jsx
│               ├── store/
│               │   └── store.js
│               └── styles.css
├── corpus/
│   └── hw04/
│       ├── source1.txt
│       ├── source2.txt
│       ├── source3.txt
│       ├── source4.txt
│       └── source5.txt
├── reports/
│   ├── hw01/
│   │   ├── AI_USE.md
│   │   ├── METRICS.md
│   │   ├── RUN_LOG.txt
│   │   ├── cases/
│   │   │   └── nondeterminism_input.json
│   │   ├── raw/
│   │   │   └── nondeterminism_output.json
│   │   ├── report (2).pdf
│   │   ├── reproducible_run_instructions
│   │   └── verification.json
│   ├── hw02/
│   │   ├── AI_USE.md
│   │   ├── METRICS.md
│   │   ├── RUN_LOG.txt
│   │   ├── cases/
│   │   │   └── *.json
│   │   ├── raw/
│   │   │   └── *.json
│   │   ├── LEE_HW2.pdf
│   │   ├── reproducible_run_instructions
│   │   └── verification.json
│   ├── hw03/
│   │   ├── AI_USE.md
│   │   ├── METRICS.md
│   │   ├── RUN_LOG.txt
│   │   ├── SOURCES.md
│   │   ├── questions.yaml
│   │   ├── raw/
│   │   │   └── *.json
│   │   ├── Lee_HW3.pdf
│   │   ├── reproducible_run_instructions
│   │   └── verification.json
│   ├── hw04/
│   │   ├── AI_USE.md
│   │   ├── METRICS.md
│   │   ├── RUN_LOG.txt
│   │   ├── questions.yaml
│   │   ├── raw/
│   │   │   ├── benchmark_raw.csv
│   │   │   └── rag_evaluation.json
│   │   ├── Lee_HW4.pdf
│   │   ├── reproducible_run_instructions
│   │   └── verification.json
│   └── hw05/
│       ├── AI_USE.md
│       ├── METRICS.md
│       ├── REFLECTION.md
│       ├── RUN_LOG.txt
│       ├── Lee_HW5.pdf
│       ├── raw/
│       │   ├── agent_runs.jsonl
│       │   ├── inspector-protocol-*.json
│       │   └── retry_results.csv
│       ├── reproducible_run_instructions
│       └── verification.json
├── src/
│   └── model_client.py
├── .gitignore
├── .vscode/
│   └── settings.json
├── AGENT.md
├── DOMAIN_SCHEMA.md
├── Makefile
└── README.md
```
