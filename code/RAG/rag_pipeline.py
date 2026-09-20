from pathlib import Path
from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex

from llama_index.core.node_parser import TokenTextSplitter, SemanticSplitterNodeParser, SentenceWindowNodeParser
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.vector_stores import SimpleVectorStore

from llama_index.core.retrievers import VectorIndexRetriever
import numpy as np
import time
import json

import yaml

# Locate the local corpus folder
BASE_DIR = Path(__file__).resolve().parent
CORPUS_DIR = BASE_DIR / "corpus"
RAW_DIR = BASE_DIR.parent.parent / "reports" / "hw03" / "raw"
QUESTIONS_PATH = BASE_DIR / "questions.yaml"

# For moderately sized chunks without creating excessive duplication
TOKEN_CHUNK_SIZE = 256
TOKEN_CHUNK_OVERLAP = 40

def load_documents():
# Load the local document
    documents = SimpleDirectoryReader(input_dir=str(CORPUS_DIR)).load_data()

    # For the printed document
    print(f"Documents loaded: {len(documents)}")
    return documents

# Embedding model to be used for the indexing and retrieval steps later
#embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
def build_token_nodes(documents):

    token_splitter = TokenTextSplitter(
        chunk_size=TOKEN_CHUNK_SIZE,
        chunk_overlap=TOKEN_CHUNK_OVERLAP
    )
    token_nodes = token_splitter.get_nodes_from_documents(documents)
    print(f"Token nodes created: {len(token_nodes)}")
    return token_nodes


####### Create the semantic node parser #########
def build_semantic_nodes(documents, embed_model):
    semantic_splitter = SemanticSplitterNodeParser.from_defaults(
        buffer_size=1,
        breakpoint_percentile_threshold=95,
        embed_model=embed_model
    )

    semantic_nodes = semantic_splitter.get_nodes_from_documents(documents)

    print(f"\nSemantic nodes created: {len(semantic_nodes)}")
    return semantic_nodes

######## SENTENCE-WINDOW #########
def build_sentence_window_nodes(documents):
    sentence_window_parser = SentenceWindowNodeParser.from_defaults(
        window_size=3,  # Stores up to three sentences before and after each sentence
        window_metadata_key="window", # Stores into node.metadata["window"]
        original_text_metadata_key="original_text", # Stores ea og sentence into node.metadata["original_text"]
    )

    sentence_window_nodes = sentence_window_parser.get_nodes_from_documents(documents)

    print(f"\nSentence-window nodes created: {len(sentence_window_nodes)}")
    return sentence_window_nodes


##### Indexing (in memory) ########
def build_index(nodes, embed_model):
    vector_store = SimpleVectorStore()
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    return VectorStoreIndex(nodes, storage_context=storage_context, embed_model=embed_model)

##### Retrieval ######
def retriever_helper(index, technique, query, k, embed_model, qid="q1"):
    # Compute the query embedding
    query_embedding = np.array(embed_model.get_query_embedding(query))

    # Show its dimension and the first 8 values
    print("\n" + "=" * 75)
    print(f"\nTechnique: {technique}")
    print(f"Query vector shape: {query_embedding.shape}")
    print(f"Query dimension: {len(query_embedding)}")
    print(f"First 8 values: {query_embedding[:8]}")

    # Retrieve top-k nodes
    retriever = VectorIndexRetriever(index=index, similarity_top_k=k)

    # Start time
    start_time = time.perf_counter()
    
    results = retriever.retrieve(query)

    retrieval_latency_ms = (time.perf_counter() - start_time) * 1000

    print(f"Retrieval latency: {retrieval_latency_ms:.2f} ms")
    print(f"{'rank':<8}{'store_score':<15}{'cosine_sim':<15}{'chunk_len':<12}preview")
    print("-" * 60)


    doc_embeddings = []
    saved_rows = []


    # For each, compute returned chunk's embedding
    for rank, result in enumerate(results, start=1):
        text = result.node.get_content()    # Each result has retrieved text chunk and similarity score
        doc_embedding = np.array(embed_model.get_text_embedding(text))

        doc_embeddings.append(doc_embedding)

        # Compute cosine similarity
        cos_sim = float(np.dot(query_embedding, doc_embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)))        

        store_score = float(result.score) if result.score is not None else None
        
        # A lower rank number means the result is more relevant and store_score is the similarity score provided by LlamaIndex
        # cos_sim is the cosine similarity calculated manually, and we also have chunk length and ~160 short text preview
        print(f"{rank:<8}{str(store_score):<15}{cos_sim:<15.4f}{len(text):<12}{text[:160].replace(chr(10), ' ')}")
        saved_rows.append({"rank" : rank, "store_score" : store_score, "cosine_sim" : cos_sim, "chunk_len" : len(text), "preview" : text[:160].replace("\n", " ")})

    # Save one JSON file for this query and technique
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # Stack document embeddings and print shape
    document_embeddings = np.vstack(doc_embeddings)

    print(f"Shape of stacked doc vectors: {document_embeddings.shape}")

    output = {"technique": technique, "retrieval_latency_ms": retrieval_latency_ms, "query_dimension": len(query_embedding), "query_shape": list(query_embedding.shape), "document_vectors_shape": list(document_embeddings.shape), "results": saved_rows}

    output_path = RAW_DIR / f"{qid}_{technique.lower().replace('-', '_')}_results.json"
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(f"Saved results to: {output_path}")

def main():
    documents = load_documents()
    embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Chunking
    token_nodes = build_token_nodes(documents)
    semantic_nodes = build_semantic_nodes(documents,embed_model)
    sentence_window_nodes = build_sentence_window_nodes(documents)

    # Indexing in-memory
    token_index = build_index(token_nodes, embed_model)
    semantic_index = build_index(semantic_nodes, embed_model)
    sentence_window_index = build_index(sentence_window_nodes,embed_model)

    # Testing
    print("\nFirst token node:")
    print(token_nodes[0].get_content()[:300])

    print("\nFirst semantic node:")
    print(semantic_nodes[0].get_content()[:300])

    print("\nFirst sentence-window node:")
    print(sentence_window_nodes[0].metadata["original_text"])
    print(sentence_window_nodes[0].metadata["window"])

    # Retrieval-only test
    # Load questions from questions.yaml
    with open(QUESTIONS_PATH, "r", encoding="utf-8") as file:
        questions = yaml.safe_load(file)

    k = 3

    # Run every question through all three techniques (token, semantic, retriever)
    for question in questions:
        qid = question["id"]
        query = question["question"]

        retriever_helper(token_index, "Token", query, k, embed_model, qid)
        retriever_helper(semantic_index, "Semantic", query, k, embed_model, qid)
        retriever_helper(sentence_window_index, "Sentence-window", query, k, embed_model, qid)


if __name__ == "__main__":
    main()

