"""
Retriever utilities for FAISS-backed RAG.
"""

from typing import Dict, List

import faiss
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

from rag_pipeline.embedder import load_faiss_index

load_dotenv()

QUERY_MODEL = "text-embedding-3-large"


def _get_client() -> OpenAI:
    return OpenAI()


def _embed_query(text: str) -> np.ndarray:
    client = _get_client()
    response = client.embeddings.create(model=QUERY_MODEL, input=text)
    vec = np.array(response.data[0].embedding, dtype=np.float32)
    faiss.normalize_L2(vec.reshape(1, -1))
    return vec.reshape(-1)


def retrieve_chunks(product_id: str, query: str, top_k: int = 10) -> List[Dict]:
    """
    Retrieve top-k chunks for a given query.
    """
    index, metadata = load_faiss_index(product_id)
    if index.ntotal == 0:
        return []

    query_vec = _embed_query(query)
    k = min(top_k, index.ntotal)
    scores, idxs = index.search(query_vec.reshape(1, -1), k)

    results: List[Dict] = []
    for rank, (score, idx) in enumerate(zip(scores[0], idxs[0]), start=1):
        if idx < len(metadata):
            chunk_meta = metadata[idx]
            results.append(
                {
                    "chunk_id": chunk_meta["chunk_id"],
                    "score": float(score),
                    "text": chunk_meta["text"],
                    "source_types": chunk_meta["source_types"],
                    "meta": chunk_meta["meta"],
                    "rank": rank,
                }
            )
    return results


def get_all_chunks(product_id: str) -> List[Dict]:
    """
    Get all chunks for a product (for accessing description chunks).
    """
    index, metadata = load_faiss_index(product_id)
    if index.ntotal == 0:
        return []
    
    results: List[Dict] = []
    for idx, chunk_meta in enumerate(metadata):
        results.append(
            {
                "chunk_id": chunk_meta["chunk_id"],
                "text": chunk_meta["text"],
                "source_types": chunk_meta["source_types"],
                "meta": chunk_meta["meta"],
            }
        )
    return results


def get_description_chunks(product_id: str) -> List[Dict]:
    """
    Get all chunks that contain description content (source_types includes "description").
    """
    all_chunks = get_all_chunks(product_id)
    description_chunks = [
        chunk for chunk in all_chunks
        if "description" in chunk.get("source_types", [])
    ]
    return description_chunks


def retrieve_visual_chunks(product_id: str, top_k: int = 10) -> List[Dict]:
    """
    Convenience helper to retrieve chunks focused on visual/appearance themes.
    """
    queries = [
        "How do customers describe the appearance, colors, and materials of this product?",
        "What visual features stand out according to customer reviews?",
        "Summarize the look, shape, and style details mentioned for this product.",
    ]

    combined: List[Dict] = []
    seen = set()
    per_query = max(1, top_k // len(queries) + 1)

    for q in queries:
        for chunk in retrieve_chunks(product_id, q, top_k=per_query):
            if chunk["chunk_id"] not in seen:
                combined.append(chunk)
                seen.add(chunk["chunk_id"])

    combined.sort(key=lambda x: x["score"], reverse=True)
    return combined[:top_k]


if __name__ == "__main__":
    for pid in ["ps5", "stanley", "jordans"]:
        try:
            results = retrieve_visual_chunks(pid, top_k=5)
            print(f"{pid}: retrieved {len(results)} visual chunks")
            if results:
                print(f"  Top chunk -> {results[0]['chunk_id']} (score={results[0]['score']:.3f})")
        except Exception as exc:
            print(f"Failed to retrieve for {pid}: {exc}")

