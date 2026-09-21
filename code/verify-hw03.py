"""
verify-hw03.py

Basic self-check for HW3. Confirms the local RAG inputs and retrieval results
are present and writes reports/hw03/verification.json.

Usage:
    python3 verify-hw03.py
"""

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import yaml


SID4 = 4544
MODEL = "sentence-transformers/all-MiniLM-L6-v2"
TECHNIQUES = ("token", "semantic", "sentence_window")

ROOT_DIR = Path(__file__).resolve().parent.parent
RAG_DIR = Path(__file__).resolve().parent / "RAG"
CORPUS_DIR = RAG_DIR / "corpus"
QUESTIONS_PATH = ROOT_DIR / "reports/hw03/questions.yaml"
RAW_DIR = ROOT_DIR / "reports/hw03/raw"
MANIFEST_PATH = RAW_DIR / "CORPUS_MANIFEST.json"
OUTPUT_PATH = ROOT_DIR / "reports/hw03/verification.json"


def get_commit_hash():
    # Record the exact repository revision used for this verification run.
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT_DIR,
        text=True,
    ).strip()


def check_pipeline_imports():
    # Confirm the RAG module loads and exposes the functions used by the run.
    try:
        spec = importlib.util.spec_from_file_location(
            "rag_pipeline", RAG_DIR / "rag_pipeline.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        required_functions = (
            "load_documents",
            "build_token_nodes",
            "build_semantic_nodes",
            "build_sentence_window_nodes",
            "retriever_helper",
        )
        return all(hasattr(module, name) for name in required_functions)
    except Exception as error:
        print(f"Pipeline import check failed: {error}", file=sys.stderr)
        return False


def check_corpus_manifest():
    # Detect missing or modified corpus files using the recorded manifest.
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        files = manifest["files"]
        if not files:
            return False

        for entry in files:
            path = CORPUS_DIR / entry["filename"]
            data = path.read_bytes()
            if len(data) != entry["byte_size"]:
                return False
            if hashlib.sha256(data).hexdigest() != entry["sha256"]:
                return False
        return True
    except (KeyError, OSError, json.JSONDecodeError):
        return False


def load_questions():
    # Share YAML loading and basic shape validation across question checks.
    questions = yaml.safe_load(QUESTIONS_PATH.read_text(encoding="utf-8"))
    if not isinstance(questions, list) or not questions:
        raise ValueError("questions.yaml must contain a non-empty list")
    return questions


def check_questions_and_sources():
    # Ensure every configured question points to a local corpus source.
    try:
        questions = load_questions()
        for question in questions:
            required = {"id", "question", "expected_answer", "expected_source"}
            if not required.issubset(question):
                return False
            if not (CORPUS_DIR / question["expected_source"]).is_file():
                return False
        return len({question["id"] for question in questions}) == len(questions)
    except (OSError, ValueError, yaml.YAMLError):
        return False

def check_retrieval_results():
    # Validate that each question/technique produced three ranked results.
    try:
        questions = load_questions()
        for question in questions:
            for technique in TECHNIQUES:
                path = RAW_DIR / f"{question['id']}_{technique}_results.json"
                data = json.loads(path.read_text(encoding="utf-8"))
                results = data["results"]
                if data["technique"].lower().replace("-", "_") != technique:
                    return False
                if len(results) != 3:
                    return False
                if data["query_dimension"] <= 0:
                    return False
                if data["document_vectors_shape"] != [3, data["query_dimension"]]:
                    return False
                if [result["rank"] for result in results] != [1, 2, 3]:
                    return False
        return True
    except (KeyError, OSError, json.JSONDecodeError, TypeError):
        return False


def main():
    # Keep each verification result visible in the generated report.
    checks = [
        {
            "check": "RAG pipeline imports with required functions",
            "passed": check_pipeline_imports(),
        },
        {
            "check": "Corpus manifest matches local corpus files",
            "passed": check_corpus_manifest(),
        },
        {
            "check": "Questions and expected source files are valid",
            "passed": check_questions_and_sources(),
        },
        {
            "check": "Five questions have three ranked retrieval results each",
            "passed": check_retrieval_results(),
        },
    ]

    verification = {
        "homework": 3,
        "sid4": SID4,
        "commit_hash": get_commit_hash(),
        "model": MODEL,
        "techniques": list(TECHNIQUES),
        "checks": checks,
        "all_passed": all(check["passed"] for check in checks),
    }

    # Write a machine-readable report and fail the command if any check failed.
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(verification, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(verification, indent=2))
    sys.exit(0 if verification["all_passed"] else 1)


if __name__ == "__main__":
    main()