from pathlib import Path
from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex

from llama_index.core.node_parser import TokenTextSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.core.retrievers import VectorIndexRetriever
import numpy as np
import time
import json

import yaml

from src.model_client import complete

# Locate the local corpus folder
BASE_DIR = Path(__file__).resolve().parent
CORPUS_DIR = BASE_DIR.parent / "corpus" / "hw04"
RAW_DIR = BASE_DIR.parent / "reports" / "hw04" / "raw"
QUESTIONS_PATH = BASE_DIR.parent / "reports" / "hw04" / "questions.yaml"

# For moderately sized chunks without creating excessive duplication
TOKEN_CHUNK_SIZE = 500
TOKEN_CHUNK_OVERLAP = 50
TOP_K = 3

def load_documents():
# Load the local document
    documents = SimpleDirectoryReader(input_dir=str(CORPUS_DIR)).load_data()

    # For the printed document
    print(f"Documents loaded: {len(documents)}")
    return documents


##### Indexing (in memory) ########
def build_index(nodes, embed_model):
    vector_store = SimpleVectorStore()
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    return VectorStoreIndex(nodes, storage_context=storage_context, embed_model=embed_model)

#### Build Nodes
def build_nodes(documents):
    splitter = TokenTextSplitter(chunk_size=TOKEN_CHUNK_SIZE, chunk_overlap=TOKEN_CHUNK_OVERLAP)
    nodes = splitter.get_nodes_from_documents(documents)

    print(f"Chunks created: {len(nodes)}")
    return nodes

##### Retrieval ######
def retriever_helper(index, query, k=3):
    retriever = VectorIndexRetriever(index=index, similarity_top_k=k)

    # Start time
    start_time = time.perf_counter()
    
    results = retriever.retrieve(query)

    retrieval_latency_ms = (time.perf_counter() - start_time) * 1000

    print(f"Retrieval latency: {retrieval_latency_ms:.2f} ms")
    print("-" * 60)

    # For each, compute returned chunk's embedding
    for rank, result in enumerate(results, start=1):
        text = result.node.get_content()    # Each result has retrieved text chunk and similarity score

        source_file = result.node.metadata.get("file_name", "Unknown")


        if source_file is None:
            source_path = result.node.metadata.get("file_path")
            source_file = Path(source_path).name if source_path else None
     

        store_score = float(result.score) if result.score is not None else None
        
        print(f"\nRank: {rank}")
        print(f"Source: {source_file}")
        print(f"Score: {result.score}")
        print(f"Preview: {text[:300]}")
    return results


# No RAG for baseline
def no_rag(query):
    messages = [{"role": "user", "content": query}]

    response = complete(messages)
    return response

# Basic RAG 
def basic_rag(query, results):
    context = "\n\n".join(result.node.get_content() for result in results)

    messages = [{"role": "user", "content": f"""Use the input context to answer the query.
        Context: {context}
        Query: {query}"""}
        ]

    response = complete(messages)
    return response

RELEVANCE_THRESHOLD = 0.3

# Context-engineered RAG
def context_rag(query, results):
    unique_context = []
    seen_context = set()
    for r in results:
        text = r.node.get_content()


        # Drop irrelevant chunks using the threshold
        if r.score is not None and r.score < RELEVANCE_THRESHOLD:
            print(f"Dropped low-relevance chunk with score: {r.score:.4f}")
            continue

        # Don't include duplicate chunks
        new_text = " ".join(text.lower().split())
        if new_text in seen_context:
            print("Dropped duplicate")
            continue

        seen_context.add(new_text)
        unique_context.append(r)

    print(f"Number of context chunks that were kept: {len(unique_context)}/{len(results)}")

    context_info = []
    # Order and label survivors with their sources
    for i, r in enumerate(unique_context, start=1):
        source = r.node.metadata.get("file_name","Unknown")
        text = r.node.get_content()
        
        context_info.append(f"[Source {i}: {source}]\n{text}")
        
    context = "\n\n".join(context_info)

    messages = [
            {"role": "system", "content": (
                    "Answer only from the provided context. "
                    "Cite the source number used. "
                    "When the evidence is insufficient, refuse with this quote: 'I cannot answer this question from the provided documents.'"
                )},
            {
                "role": "user",
                "content": 
                    f"""Context: {context}
                    Query: {query}"""
            }
        ]

    response = complete(messages)
    return response, unique_context


# For Evaluation Part 4 Q6
REFUSAL_TEXT = "I cannot answer this question from the provided documents"

def eval_retrieval(query, results):
    expected_sources = query.get("expected_sources", [])

    retrieved_sources = [
        r.node.metadata.get("file_name", "Unknown")
        for r in results
    ]

    if not expected_sources:
        return False, retrieved_sources

    correct_retrieval = all(
        source in retrieved_sources
        for source in expected_sources
    )

    return correct_retrieval, retrieved_sources


def eval_refusal(query, answer):
    should_refuse = query["type"] in ["not_in_documents","unrelated",]

    if should_refuse:
        return REFUSAL_TEXT in answer

    return not REFUSAL_TEXT in answer



def main():
    documents = load_documents()
    embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

    nodes = build_nodes(documents)

    #Indexing
    index = build_index(nodes, embed_model)

    # TEST
    # Load questions from questions.yaml
    with open(QUESTIONS_PATH, "r", encoding="utf-8") as file:
        questions = yaml.safe_load(file)


    eval_results = []

    # Run question for each configuration
    for question in questions:
        qid = question["id"]
        query = question["question"]

        print("-" * 60)
        print(f"{qid}: {query}")

        results = retriever_helper(index, query, k=TOP_K)

        no_rag_result = no_rag(query)
        basic_rag_result = basic_rag(query, results)
        context_rag_result, filtered_rag_context = context_rag(query, results)

        correct_retrieval, retrieved_sources = eval_retrieval(question, results)
        no_rag_refusal = eval_refusal(question, no_rag_result["content"])
        basic_rag_refusal = eval_refusal(question, basic_rag_result["content"])
        context_rag_refusal = eval_refusal(question, context_rag_result["content"])

        retrieved_chunks = [{
            "source": r.node.metadata.get("file_name", "Unknown"),
            "score": float(r.score) if r.score is not None else None,
            "text": r.node.get_content()
        } for r in results]

        filtered_chunks = [{
                "source": r.node.metadata.get("file_name", "Unknown"),
                "score": float(r.score) if r.score is not None else None,
                "text": r.node.get_content()
        } for r in filtered_rag_context]

        eval_results.append({
            "question_id": qid,
            "configuration": "No RAG",
            "correct_retrieval": None,
            "correct_answer": None,
            "grounded": None,
            "refused_when_needed": no_rag_refusal,
            "answer": no_rag_result["content"],
        })

        eval_results.append({
            "question_id": qid,
            "configuration": "Basic RAG",
            "correct_retrieval": correct_retrieval,
            "correct_answer": None,
            "grounded": None,
            "refused_when_needed": basic_rag_refusal,
            "retrieved_chunks": retrieved_chunks,
            "retrieved_sources": retrieved_sources,
            "answer": basic_rag_result["content"],
        })

        eval_results.append({
            "question_id": qid,
            "configuration": "Context-Engineered RAG",
            "correct_retrieval": correct_retrieval,
            "correct_answer": None,
            "grounded": None,
            "refused_when_needed": context_rag_refusal,

            # Original retrieval
            "retrieved_chunks": retrieved_chunks,
            "retrieved_sources": retrieved_sources,

            # After filtered
            "filtered_context_chunks": filtered_chunks,
            "answer": context_rag_result["content"],
        })

        # Print the values
        print("\n--- NO RAG ---")
        print(no_rag_result["content"])

        print("\n--- BASIC RAG ---")
        print(basic_rag_result["content"])

        print("\n--- CONTEXT-ENGINEERED RAG ---")
        print(context_rag_result["content"])

    ## Chosen question (Q3) for Part 4 Q5
    """chosen_question = questions[2]
    qid = chosen_question["id"]
    query = chosen_question["question"]

    print("\n" + "=" * 60)
    print("PART 4; SWEEP CONTEXT SIZE")
    print(f"Question: {qid}: {query}")

    for k in [1, 3, 5]:
        print("\n" + "-" * 60)
        print(f"k value: {k}")

        results = retriever_helper(index, query, k=k)

        #BasicRag and ContextEngRag
        basic_result = basic_rag(query, results)
        context_result = context_rag(query, results)

        print("\n----- Basic RAG Answer: -----")
        print(basic_result["content"])

        print("\n----- Context-Engineered RAG Answer: -----")
        print(context_result["content"])"""

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    evaluation_path = RAW_DIR / "rag_evaluation.json"

    evaluation_path.write_text(
        json.dumps(eval_results, indent=2),
        encoding="utf-8"
    )
    print(f"\nSaved evaluation results to: {evaluation_path}")
if __name__ == "__main__":
    main()

