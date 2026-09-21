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
│   │   ├── corpus_manifest_create.py
│   │   ├── pypi_vulnerabilities.zip
│   │   ├── rag_pipeline.py
│   │   └── summarize_results.py
│   ├── agentgraph_demo.py
│   ├── agents_demo.py
│   ├── hw1_client.py
│   ├── hw2experiment_run.py
│   ├── metric_helper.py
│   ├── nodes.py
│   ├── reports/
│   │   └── hw01/
│   │       └── verification.json
│   ├── router.py
│   ├── state.py
│   ├── validateplanner.py
│   ├── verify-hw01.py
│   ├── verify-hw02.py
│   ├── verify-hw03.py
│   ├── web_application/
│   │   ├── __pycache__/
│   │   ├── index.html
│   │   ├── main.py
│   │   ├── routers/
│   │   ├── script.js
│   │   ├── style.css
│   │   ├── templates/
│   │   └── temp.js
│   └── workflow.py
├── src/
│   └── model_client.py
├── reports/
│   ├── hw01/
│   │   ├── AI_USE.md
│   │   ├── METRICS.md
│   │   ├── RUN_LOG.txt
│   │   ├── cases/
│   │   ├── raw/
│   │   ├── report (2).pdf
│   │   ├── reproducible_run_instructions
│   │   └── verification.json
│   ├── hw02/
│   │   ├── AI_USE.md
│   │   ├── METRICS.md
│   │   ├── RUN_LOG.txt
│   │   ├── cases/
│   │   ├── raw/
│   │   ├── reproducible_run_instructions
│   │   ├── LEE_HW2.pdf
│   │   └── verification.json
│   └── hw03/
│       ├── AI_USE.md
│       ├── METRICS.md
│       ├── RUN_LOG.txt
│       ├── SOURCES.md
│       ├── questions.yaml
│       ├── raw/
│       ├── reproducible_run_instructions
│       ├── Lee_HW3.pdf
│       └── verification.json
├── AGENT.md
├── DOMAIN_SCHEMA.md
├── Makefile
└── README.md
```