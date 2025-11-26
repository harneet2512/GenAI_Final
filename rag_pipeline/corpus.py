"""
Corpus utilities for the RAG pipeline.

Loads product descriptions and parsed reviews to create unified corpora
for downstream chunking, embedding, and retrieval.
"""

import json
import os
from typing import Dict, List, Optional

PRODUCTS: List[Dict[str, str]] = [
    {
        "id": "ps5",
        "asin": "B0CL61F39H",
        "display_name": "PlayStation®5 Digital Edition (Slim)",
    },
    {
        "id": "stanley",
        "asin": "B0CJZMP7L1",
        "display_name": "STANLEY Quencher H2.0 Tumbler",
    },
    {
        "id": "jordans",
        "asin": "B0DJ9SVTB6",
        "display_name": "Nike Men's Court Vision Mid Next Nature Shoes",
    },
]

DATA_PROCESSED_DIR = os.path.join("data", "processed")
DESCRIPTION_DIR = os.path.join("data", "descriptions")


def _product_from_id(product_id: str) -> Dict[str, str]:
    for product in PRODUCTS:
        if product["id"] == product_id:
            return product
    raise ValueError(f"Unknown product_id: {product_id}")


def _load_file(path: str) -> Optional[str]:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return None


def load_description(product_id: str) -> str:
    """
    Load the textual product description for a given product.
    """
    product = _product_from_id(product_id)
    potential_files = [
        os.path.join(DESCRIPTION_DIR, f"{product_id}.txt"),
        os.path.join(DESCRIPTION_DIR, f"{product['asin']}.txt"),
    ]
    for path in potential_files:
        text = _load_file(path)
        if text:
            return text.strip()
    raise FileNotFoundError(
        f"Description file not found for product '{product_id}'."
        f" Looked in: {potential_files}"
    )


def _load_reviews_json(path: str) -> Optional[List[Dict]]:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def load_reviews(product_id: str) -> List[Dict]:
    """
    Load parsed reviews for a product from the processed data directory.
    Supports multiple filename conventions.
    """
    product = _product_from_id(product_id)
    asin = product["asin"]
    candidate_files = [
        os.path.join(DATA_PROCESSED_DIR, f"reviews_{product_id}.json"),
        os.path.join(DATA_PROCESSED_DIR, f"reviews_{asin}.json"),
        os.path.join(DATA_PROCESSED_DIR, f"reviews_{product_id}_{asin}.json"),
        os.path.join(DATA_PROCESSED_DIR, f"{asin}_reviews_processed.json"),
        os.path.join(DATA_PROCESSED_DIR, f"{asin}_reviews_raw.json"),
    ]

    for path in candidate_files:
        reviews = _load_reviews_json(path)
        if reviews:
            return reviews

    raise FileNotFoundError(
        f"Reviews file not found for product '{product_id}'."
        f" Looked in: {candidate_files}"
    )


def build_corpus(product_id: str) -> List[Dict]:
    """
    Build a flattened corpus containing description and review documents.

    Returns a list of dictionaries:
        {
            "type": "description" | "review",
            "source_type": "description" | "review",  # Alias for consistency
            "text": "...",
            "rating": Optional[int],
            "meta": {...}
        }
    """
    corpus: List[Dict] = []

    description_text = load_description(product_id)
    if description_text:
        corpus.append(
            {
                "type": "description",
                "source_type": "description",  # Explicit source_type for consistency
                "text": description_text,
                "rating": None,
                "meta": {"source": "description", "source_type": "description"},
            }
        )

    reviews = load_reviews(product_id)
    for review in reviews:
        body = review.get("body") or review.get("text") or ""
        if not body.strip():
            continue
        rating = review.get("rating")
        if isinstance(rating, str):
            try:
                rating = int(float(rating))
            except ValueError:
                rating = None
        corpus.append(
            {
                "type": "review",
                "source_type": "review",  # Explicit source_type for consistency
                "text": body.strip(),
                "rating": rating,
                "meta": {
                    "source": "review",
                    "source_type": "review",
                    "title": review.get("title"),
                    "date": review.get("date"),
                    "variant": review.get("variant"),
                },
            }
        )

    return corpus


if __name__ == "__main__":
    for product in PRODUCTS:
        pid = product["id"]
        try:
            docs = build_corpus(pid)
            print(f"{pid}: {len(docs)} documents in corpus")
        except FileNotFoundError as exc:
            print(exc)

