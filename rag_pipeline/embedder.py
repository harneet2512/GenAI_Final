"""
Embedding + FAISS index utilities for the RAG pipeline.
"""

import json
import os
from typing import Dict, List, Tuple

import faiss
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

from rag_pipeline.chunker import chunk_corpus

load_dotenv()

INDEX_DIR = os.path.join("rag_pipeline", "faiss_indexes")
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIM = 3072


def _get_client() -> OpenAI:
    return OpenAI()


def _embed_texts(texts: List[str]) -> np.ndarray:
    client = _get_client()
    embeddings: List[np.ndarray] = []
    for i in range(0, len(texts), 50):
        batch = texts[i : i + 50]
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        for item in response.data:
            embeddings.append(np.array(item.embedding, dtype=np.float32))
    return np.vstack(embeddings)


def build_faiss_index(product_id: str) -> None:
    """
    Chunk corpus, embed chunks, and persist FAISS index + metadata.
    """
    chunks = chunk_corpus(product_id)
    if not chunks:
        raise ValueError(f"No chunks generated for product {product_id}")

    texts = [chunk["text"] for chunk in chunks]
    print(f"[Embedder] Embedding {len(texts)} chunks for {product_id}...")
    embeddings = _embed_texts(texts)
    faiss.normalize_L2(embeddings)

    index = faiss.IndexFlatIP(EMBEDDING_DIM)
    index.add(embeddings)

    os.makedirs(INDEX_DIR, exist_ok=True)
    index_path = os.path.join(INDEX_DIR, f"{product_id}.index")
    meta_path = os.path.join(INDEX_DIR, f"{product_id}_meta.json")

    faiss.write_index(index, index_path)

    metadata_records = []
    for chunk in chunks:
        metadata_records.append(
            {
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "source_types": chunk["source_types"],
                "meta": chunk["meta"],
            }
        )

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata_records, f, ensure_ascii=False, indent=2)

    print(f"[Embedder] Saved index to {index_path}")
    print(f"[Embedder] Saved metadata to {meta_path}")


def load_faiss_index(product_id: str) -> Tuple[faiss.Index, List[Dict]]:
    """
    Load FAISS index and metadata for a product.
    """
    index_path = os.path.join(INDEX_DIR, f"{product_id}.index")
    meta_path = os.path.join(INDEX_DIR, f"{product_id}_meta.json")

    if not os.path.exists(index_path) or not os.path.exists(meta_path):
        raise FileNotFoundError(
            f"Missing index/metadata for product '{product_id}'. "
            f"Expected files: {index_path}, {meta_path}"
        )

    index = faiss.read_index(index_path)
    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    return index, metadata


if __name__ == "__main__":
    for pid in ["ps5", "stanley", "jordans"]:
        try:
            build_faiss_index(pid)
        except Exception as exc:
            print(f"Failed to build index for {pid}: {exc}")

