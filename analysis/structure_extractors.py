"""
Structured visual attribute extraction using RAG + gpt-5.
"""

import json
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI

from rag_pipeline.corpus import PRODUCTS, load_description
from rag_pipeline.retriever import retrieve_chunks, get_description_chunks

load_dotenv()

_client = OpenAI()

ATTRIBUTE_FIELDS = [
    "product_name",
    "shape",
    "dimensions_or_size_impression",
    "materials",
    "color_palette",
    "branding_elements",
    "distinctive_features",
    "usage_contexts",
    "positive_visual_themes",
    "negative_visual_themes",
]

NON_VISUAL_KEYWORDS = [
    "box",
    "packaging",
    "shipping",
    "customer service",
    "support",
    "stiffness",
    "comfort",
    "durability",
]


def _get_product_constraints(product_id: str) -> str:
    """Get product-specific constraints for prompts."""
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        return ""
    
    display_name = product.get("display_name", "")
    constraints = []
    
    if product_id == "ps5":
        constraints.append(
            f'You are extracting visual attributes for the product "{display_name} – Marvel\'s Spider-Man 2 Bundle".'
        )
        constraints.append(
            "Use the product description text as the primary source for shape, materials, colors, and distinctive physical features."
        )
        constraints.append(
            "Use customer reviews only for high-level visual impressions such as 'premium appearance' or 'clean look'."
        )
        constraints.append(
            "If a detail is not mentioned in the description (for example a specific LED color or exact material), leave that field as 'unknown' or omit it."
        )
        constraints.append(
            "Do not invent details that are not in the description or reviews."
        )
        constraints.append(
            "Focus strictly on visual aspects: shape, proportions, materials, color palette, visible branding, and how the product looks under a TV or in a living room."
        )
        constraints.append('It is not PS5 Pro; avoid "PS5 Pro", "PSSR", "2TB" and any Pro-only features.')
        constraints.append("Only use details that appear in the provided context.")
    elif product_id == "jordans":
        constraints.append(
            "The product is exactly 'Nike Men's Court Vision Mid Next Nature Shoes', "
            "a mid-top retro basketball-style sneaker made with some recycled materials."
        )
        constraints.append(
            "Do not describe it as 'Low', 'Low Sneaker', 'Air Jordan 1', or 'Jordan 1 Low'."
        )
        constraints.append(
            "If the context mentions Air Jordan or Court Vision Low, treat those as noisy or unrelated."
        )
        constraints.append("Describe only the Court Vision Mid Next Nature shoe.")
        constraints.append("Only use details that appear in the provided context.")
    elif product_id == "stanley":
        constraints.append(f'The product is "{display_name}".')
        constraints.append("Only use details that appear in the provided context.")
    
    return "\n".join(constraints)


def _build_context(product_id: str) -> str:
    """
    Build context for visual attribute extraction.
    For PS5, always includes description chunks first.
    """
    snippets: List[str] = []
    seen = set()
    
    # For PS5, always include all description chunks first
    if product_id == "ps5":
        description_chunks = get_description_chunks(product_id)
        for chunk in description_chunks:
            if chunk["chunk_id"] not in seen:
                snippets.append(f"[Product Description]\n{chunk['text']}")
                seen.add(chunk["chunk_id"])
    
    # Then retrieve review-based chunks
    queries = [
        "How do customers describe the appearance, shape, and size of this product?",
        "What do reviews mention about materials, finish, and build quality?",
        "Summarize the colors, branding, and distinctive visuals of this product.",
    ]
    
    for query in queries:
        for chunk in retrieve_chunks(product_id, query, top_k=6):
            if chunk["chunk_id"] not in seen:
                snippets.append(chunk["text"])
                seen.add(chunk["chunk_id"])
    
    return "\n\n---\n\n".join(snippets[:20])  # Increased limit to accommodate description


def extract_visual_attributes(product_id: str) -> Dict[str, Any]:
    """
    Use RAG + gpt-4o to extract structured visual attributes with product-specific constraints.
    """
    context = _build_context(product_id)
    product_constraints = _get_product_constraints(product_id)
    
    prompt = f"""
You are an expert product analyst. Using ONLY the context below, extract structured visual attributes
for the product. When information is missing, use "N/A" for strings and [] for lists.

{product_constraints}

Focus only on visual appearance: shape, proportions, materials, color, visible branding, and how the product looks (e.g., clean, cheap, premium, scratched).
Ignore packaging condition, shipping, customer service, box damage, comfort, durability, and stiffness; these should not be treated as visual features.

Context:
{context}

Return a JSON object with the following schema:
{{
  "product_name": "string",
  "shape": "string",
  "dimensions_or_size_impression": "string",
  "materials": "string",
  "color_palette": ["list of colors"],
  "branding_elements": ["logos or brand marks"],
  "distinctive_features": ["unique visual traits"],
  "usage_contexts": ["notable usage scenarios"],
  "positive_visual_themes": ["what customers like visually"],
  "negative_visual_themes": ["visual complaints"]
}}

Return ONLY valid JSON. Do not include explanations.
"""

    try:
        # Try gpt-4o first (gpt-5 may not be available)
        try:
            response = _client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise product analyst that extracts structured data from product reviews. Always return valid JSON.",
                    },
                    {"role": "user", "content": prompt.strip()},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
        except Exception:
            # Fallback to gpt-4-turbo if gpt-4o fails
            response = _client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise product analyst that extracts structured data from product reviews. Always return valid JSON.",
                    },
                    {"role": "user", "content": prompt.strip()},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
        content = response.choices[0].message.content
        data = json.loads(content)
    except Exception as exc:
        print(f"[Structure Extractor] Error: {exc}")
        data = {}

    for field in ATTRIBUTE_FIELDS:
        if field not in data:
            if field.endswith("_themes") or field.endswith("_elements") or field.endswith("_features") or field.endswith("_contexts") or field == "color_palette":
                data[field] = []
            else:
                data[field] = "N/A"

    return data

