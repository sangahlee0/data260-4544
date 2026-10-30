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
├── docker-compose.hw08.yml
├── code/
│   ├── Dockerfile
│   ├── Dockerfile.hw08
│   ├── requirements-hw08.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── kafka_rpc.py
│   │   └── main.py
│   ├── homework_demo.py
│   ├── hw08_kafka_pipeline/
│   │   ├── topics.py
│   │   ├── create_topics.sh
│   │   ├── planner.py
│   │   ├── writer.py
│   │   ├── reviewer.py
│   │   ├── send_question.py
│   │   ├── replay_duplicate.py
│   │   ├── consumer_death_test.py
│   │   ├── poison_message_test.py
│   │   └── ordering_test.py
│   ├── worker/
│   │   ├── __init__.py
│   │   └── consumer.py
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
│   ├── hw7_agent.py
│   ├── hw7_reflexion.py
│   ├── hw7_part4/
│   │   ├── __init__.py
│   │   ├── acceptance.py
│   │   ├── agent.py
│   │   ├── file_tools.py
│   │   ├── main.py
│   │   ├── part6_acceptance.py
│   │   ├── requirements.txt
│   │   ├── raw/
│   │   │   ├── acceptance_cases.json
│   │   │   ├── hostile_pricing_injection.txt
│   │   │   ├── pricing_snapshots/
│   │   │   └── scenarios/
│   │   └── static/
│   │       ├── app.js
│   │       ├── index.html
│   │       └── styles.css
│   ├── mcp_server/
│   │   └── domain_server.py
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
│   ├── verify-hw06.py
│   ├── verify-hw07.py
│   ├── verify-hw08.py
│   ├── workflow.py
│   └── web_application/
│       ├── index.html
│       ├── main.py
│       ├── routers/
│       │   ├── api_auth.py
│       │   ├── auth.py
│       │   ├── memory.py
│       │   └── vulnerabilities.py
│       ├── mongo/
│       │   ├── __init__.py
│       │   ├── config.py
│       │   ├── db.py
│       │   ├── main.py
│       │   ├── models.py
│       │   ├── ollama_service.py
│       │   ├── schemas.py
│       │   └── utils.py
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
│       ├── seed_hw7.py
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
│   ├── hw05/
│   │   ├── AI_USE.md
│   │   ├── METRICS.md
│   │   ├── REFLECTION.md
│   │   ├── RUN_LOG.txt
│   │   ├── Lee_HW5.pdf
│   │   ├── raw/
│   │   │   ├── agent_runs.jsonl
│   │   │   ├── inspector-protocol-*.json
│   │   │   └── retry_results.csv
│   │   ├── reproducible_run_instructions
│   │   └── verification.json
│   ├── hw06/
│   │   ├── AI_USE.md
│   │   ├── METRICS.md
│   │   ├── RUN_LOG.txt
│   │   ├── Lee_HW6.pdf
│   │   ├── memory_probes.yaml
│   │   ├── raw/
│   │   │   └── memory_logs.json
│   │   ├── reproducible_run_instructions
│   │   └── verification.json
│   ├── hw07/
│   │   ├── AI_USE.md
│   │   ├── METRICS.md
│   │   ├── Lee_HW7.pdf
│   │   ├── RUN_LOG.txt
│   │   ├── raw/
│   │   │   ├── reflexion_comparison.csv
│   │   │   ├── reflexion_comparison.json
│   │   │   ├── stored_reflections.json
│   │   │   ├── tool_reliability.csv
│   │   │   └── tool_reliability.json
│   │   ├── reproducible_run_instructions.md
│   │   └── verification.json
│   └── hw08/
│       ├── AI_USE.md
│       ├── METRICS.md
│       ├── RUN_LOG.txt
│       ├── Lee_HW8.pdf
│       ├── raw/
│       │   ├── consumer_death.json
│       │   ├── duplicate_delivery.json
│       │   ├── ordering_results.json
│       │   └── poison_message.json
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


