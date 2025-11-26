"""
Corpus chunker for the RAG pipeline.

Creates overlapping multi-source chunks combining descriptions and reviews.
"""

from typing import Dict, List

from rag_pipeline.corpus import build_corpus


def estimate_tokens(text: str) -> int:
    """
    Rough token estimate (1 token ≈ 4 characters).
    """
    return max(1, len(text) // 4)


def chunk_corpus(
    product_id: str,
    target_tokens: int = 900,
    overlap_tokens: int = 100,
) -> List[Dict]:
    """
    Chunk joined description + reviews into overlapping segments.

    Returns:
        List of chunk dictionaries.
    """
    docs = build_corpus(product_id)
    chunks: List[Dict] = []

    current_texts: List[str] = []
    current_tokens = 0
    current_source_types: set = set()
    rating_counts = {str(i): 0 for i in range(1, 6)}
    chunk_index = 0

    def flush_chunk():
        nonlocal current_texts, current_tokens, current_source_types, rating_counts, chunk_index
        if not current_texts:
            return
        chunk_text = "\n\n".join(current_texts).strip()
        chunk = {
            "product_id": product_id,
            "chunk_id": f"{product_id}_chunk_{chunk_index:04d}",
            "source_types": sorted(list(current_source_types)),
            "texts": current_texts.copy(),
            "text": chunk_text,
            "meta": {
                "rating_counts": rating_counts.copy(),
                "doc_count": len(current_texts),
            },
        }
        chunks.append(chunk)
        chunk_index += 1

        if overlap_tokens > 0 and chunk_text:
            approx_chars = overlap_tokens * 4
            overlap_text = chunk_text[-approx_chars:]
            current_texts = [overlap_text]
            current_tokens = estimate_tokens(overlap_text)
            current_source_types = set()
            rating_counts = {str(i): 0 for i in range(1, 6)}
        else:
            current_texts = []
            current_tokens = 0
            current_source_types = set()
            rating_counts = {str(i): 0 for i in range(1, 6)}

    for doc in docs:
        text = doc["text"].strip()
        if not text:
            continue
        doc_tokens = estimate_tokens(text)

        if current_tokens + doc_tokens > target_tokens and current_texts:
            flush_chunk()

        current_texts.append(text)
        current_tokens += doc_tokens
        current_source_types.add(doc["type"])

        rating = doc.get("rating")
        if rating:
            str_rating = str(int(rating))
            if str_rating in rating_counts:
                rating_counts[str_rating] += 1

    flush_chunk()
    return chunks


if __name__ == "__main__":
    for product in ["ps5", "stanley", "jordans"]:
        product_chunks = chunk_corpus(product)
        print(f"{product}: {len(product_chunks)} chunks")
        if product_chunks:
            first = product_chunks[0]
            print(
                f"  Sample chunk {first['chunk_id']} "
                f"(sources={first['source_types']}, len={len(first['text'])} chars)"
            )

