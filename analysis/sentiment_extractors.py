"""
Visual sentiment extraction using RAG + gpt-5.
"""

import json
from typing import Dict, List

from dotenv import load_dotenv
from openai import OpenAI

from rag_pipeline.corpus import PRODUCTS
from rag_pipeline.retriever import retrieve_chunks

load_dotenv()

_client = OpenAI()


def _get_product_constraints(product_id: str) -> str:
    """Get product-specific constraints for prompts."""
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        return ""
    
    display_name = product.get("display_name", "")
    constraints = []
    
    if product_id == "ps5":
        constraints.append(f'The product is "{display_name}".')
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


def _collect_sentiment_context(product_id: str) -> str:
    queries = [
        "From customer reviews, which visual aspects of this product are praised?",
        "Which visual or appearance aspects draw complaints or negative sentiment?",
    ]
    snippets: List[str] = []
    seen = set()
    for query in queries:
        for chunk in retrieve_chunks(product_id, query, top_k=8):
            if chunk["chunk_id"] not in seen:
                snippets.append(chunk["text"])
                seen.add(chunk["chunk_id"])
    return "\n\n---\n\n".join(snippets[:20])


def extract_visual_sentiment(product_id: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Use RAG + gpt-4o to map visual features to positive/negative sentiment with product-specific constraints.
    """
    context = _collect_sentiment_context(product_id)
    product_constraints = _get_product_constraints(product_id)
    
    prompt = f"""
Analyze the visual/appearance themes in the customer review context below. Identify
which visual attributes are spoken about positively vs negatively. When you make a
claim, reference how customers talk about it (brief quote or paraphrase). Classify
frequency qualitatively (high/medium/low).

{product_constraints}

Focus only on visual appearance: shape, proportions, materials, color, visible branding, and how the product looks (e.g., clean, cheap, premium, scratched).
Ignore packaging condition, shipping, customer service, box damage, comfort, durability, and stiffness; these should not be treated as visual features.

Context:
{context}

Return JSON:
{{
  "positive_visual_features": [
    {{"feature": "...", "mentions": "...", "frequency": "high/medium/low"}}
  ],
  "negative_visual_features": [
    {{"feature": "...", "mentions": "...", "frequency": "high/medium/low"}}
  ]
}}

Focus on visual attributes only. Return ONLY valid JSON.
"""

    try:
        # Try gpt-4o first (gpt-5 may not be available)
        try:
            response = _client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a sentiment analyst specializing in visual product features. Always return valid JSON.",
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
                        "content": "You are a sentiment analyst specializing in visual product features. Always return valid JSON.",
                    },
                    {"role": "user", "content": prompt.strip()},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
        result_text = response.choices[0].message.content
        data = json.loads(result_text)
    except Exception as exc:
        print(f"[Sentiment Extractor] Error: {exc}")
        data = {}

    if "positive_visual_features" not in data:
        data["positive_visual_features"] = []
    if "negative_visual_features" not in data:
        data["negative_visual_features"] = []
    return data

