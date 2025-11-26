"""
Q3 Prompt Builder
Builds image generation prompts from Q2 analysis outputs.
"""

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

PRODUCTS = ["ps5", "stanley", "jordans"]
PROMPTS_DIR = Path("prompts")


@dataclass
class ImagePrompt:
    product_id: str
    model: str  # "dalle3" or "sdxl"
    variant_id: str  # "v1", "v2", "v3"
    text: str
    guidance_notes: str


def load_q2_analysis(product_id: str) -> dict:
    """
    Load Q2 analysis JSON for a product.
    
    Args:
        product_id: Product ID (ps5, stanley, jordans)
        
    Returns:
        Analysis dictionary with visual_attributes and visual_sentiment
    """
    analysis_path = Path("analysis") / f"{product_id}_analysis.json"
    if not analysis_path.exists():
        raise FileNotFoundError(f"Analysis not found: {analysis_path}")
    
    with open(analysis_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _clean(val) -> Optional[str]:
    """
    Clean a value: remove empty, "N/A", "unknown", etc.
    
    Returns:
        Cleaned string or None if invalid
    """
    if not val:
        return None
    v = str(val).strip()
    if not v:
        return None
    if v.lower() in {"n/a", "unknown", "none", ""}:
        return None
    return v


def _clean_list(lst: List) -> List[str]:
    """Clean a list, removing empty/unknown items."""
    if not lst:
        return []
    cleaned = []
    for item in lst:
        cleaned_item = _clean(item)
        if cleaned_item:
            cleaned.append(cleaned_item)
    return cleaned


def build_prompts_for_product(product_id: str) -> List[ImagePrompt]:
    """
    Build image generation prompts for a product from Q2 analysis.
    Ensures every prompt has: product_name, shape/form, material, color, usage_context.
    
    Args:
        product_id: Product ID (ps5, stanley, jordans)
        
    Returns:
        List of ImagePrompt objects (6 total: 3 variants × 2 models)
    """
    analysis = load_q2_analysis(product_id)
    
    va = analysis.get("visual_attributes", {})
    vs = analysis.get("visual_sentiment", {})
    
    # Clean all fields - these are REQUIRED
    product_name = _clean(va.get("product_name"))
    if not product_name:
        raise ValueError(f"product_name is missing or invalid for {product_id}")
    
    shape = _clean(va.get("shape"))
    materials = _clean(va.get("materials"))
    dimensions = _clean(va.get("dimensions_or_size_impression"))
    
    color_palette = _clean_list(va.get("color_palette", []))
    branding_elements = _clean_list(va.get("branding_elements", []))
    distinctive_features = _clean_list(va.get("distinctive_features", []))
    usage_contexts = _clean_list(va.get("usage_contexts", []))
    positive_visual_themes = _clean_list(va.get("positive_visual_themes", []))
    negative_visual_themes = _clean_list(va.get("negative_visual_themes", []))
    
    # Get visual sentiment features
    positive_features = vs.get("positive_visual_features", [])
    negative_features = vs.get("negative_visual_features", [])
    
    # Extract visual flaws from negative_visual_themes (only if visual)
    visual_flaws = []
    for theme in negative_visual_themes:
        theme_lower = theme.lower()
        # Only include if it's clearly visual (scratches, color issues, etc.)
        if any(kw in theme_lower for kw in ["scratch", "color", "wear", "dent", "mark", "stain"]):
            visual_flaws.append(theme)
    
    # VALIDATION: Ensure we have minimum required fields
    if not shape:
        # Fallback to product-specific defaults if shape is missing
        if product_id == "ps5":
            shape = "tall slim white console with curved side panels"
        elif product_id == "stanley":
            shape = "tall tumbler with handle and narrow base"
        elif product_id == "jordans":
            shape = "mid-top retro basketball-style sneaker"
        else:
            raise ValueError(f"shape is missing for {product_id} and no default available")
    
    if not materials:
        # Fallback to product-specific defaults
        if product_id == "ps5":
            materials = "white matte plastic and black accents"
        elif product_id == "stanley":
            materials = "recycled stainless steel"
        elif product_id == "jordans":
            materials = "white leather upper with synthetic materials"
        else:
            raise ValueError(f"materials is missing for {product_id} and no default available")
    
    if not color_palette:
        # Fallback to product-specific defaults
        if product_id == "ps5":
            color_palette = ["white", "black"]
        elif product_id == "stanley":
            color_palette = ["pink", "lilac", "stainless steel"]
        elif product_id == "jordans":
            color_palette = ["white", "black"]
        else:
            raise ValueError(f"color_palette is missing for {product_id} and no default available")
    
    if not usage_contexts:
        # Fallback to product-specific defaults
        if product_id == "ps5":
            usage_contexts = ["in a living room", "under a TV", "on an entertainment center"]
        elif product_id == "stanley":
            usage_contexts = ["on a desk", "in a gym", "in a car cup holder"]
        elif product_id == "jordans":
            usage_contexts = ["worn on dry sidewalk", "indoors", "on feet"]
        else:
            raise ValueError(f"usage_contexts is missing for {product_id} and no default available")
    
    prompts = []
    
    # Variant v1 - Catalog shot (MUST have: product_name, shape, material, color)
    v1_parts = [f"High-resolution studio product photograph of {product_name}"]
    v1_parts.append(f"showing a {shape}")
    v1_parts.append(f"with {materials}")
    
    if color_palette:
        colors_str = ", ".join(color_palette[:3])
        v1_parts.append(f"in {colors_str}")
    
    if branding_elements:
        branding_str = ", ".join(branding_elements[:2])
        v1_parts.append(f"featuring {branding_str}")
    
    if distinctive_features:
        features_str = ", ".join(distinctive_features[:2])
        v1_parts.append(f"with key features such as {features_str}")
    
    v1_parts.append("Clean white background, soft studio lighting, sharp focus, accurate proportions.")
    v1_text = " ".join(v1_parts)
    
    # Variant v2 - Lifestyle shot (MUST have: product_name, shape, usage_context, color)
    v2_parts = [f"Realistic lifestyle image of {product_name}"]
    v2_parts.append(f"showing a {shape}")
    
    # Use first usage context
    if usage_contexts:
        v2_parts.append(f"being used {usage_contexts[0]}")
    
    if color_palette:
        colors_str = ", ".join(color_palette[:2])
        v2_parts.append(f"in {colors_str}")
    
    if materials:
        v2_parts.append(f"with {materials} finish")
    
    v2_parts.append("showing the full product clearly while keeping the surroundings slightly blurred. Natural lighting, photographic realism.")
    v2_text = " ".join(v2_parts)
    
    # Variant v3 - Detail/realism shot (MUST have: product_name, material, branding/features)
    v3_parts = [f"Close-up product photograph of {product_name}"]
    
    detail_focus = []
    if branding_elements:
        detail_focus.append(branding_elements[0])
    if materials:
        detail_focus.append("material texture")
    if distinctive_features:
        detail_focus.append(distinctive_features[0])
    
    if detail_focus:
        focus_str = " and ".join(detail_focus[:2])
        v3_parts.append(f"focusing on {focus_str}")
    else:
        v3_parts.append(f"showing {materials} texture and surface details")
    
    if color_palette:
        colors_str = ", ".join(color_palette[:2])
        v3_parts.append(f"in {colors_str}")
    
    v3_parts.append("with realistic texture, subtle reflections")
    
    if visual_flaws:
        v3_parts.append(f"Optionally include very minor wear consistent with normal use if reviews mention {visual_flaws[0]}")
    
    v3_text = ", ".join(v3_parts) + "."
    
    # Validate prompts don't contain forbidden terms
    for variant_id, text in [("v1", v1_text), ("v2", v2_text), ("v3", v3_text)]:
        if "Unknown Product" in text or "unknown product" in text.lower():
            raise ValueError(f"Prompt {variant_id} contains 'Unknown Product': {text[:100]}...")
        if "N/A" in text or "n/a" in text.lower():
            raise ValueError(f"Prompt {variant_id} contains 'N/A': {text[:100]}...")
        if not product_name in text:
            raise ValueError(f"Prompt {variant_id} missing product_name: {text[:100]}...")
    
    # Create prompts for both models
    variants = [
        ("v1", v1_text, "Catalog-style studio shot with white background"),
        ("v2", v2_text, "Lifestyle shot showing product in use"),
        ("v3", v3_text, "Close-up detail shot with realistic textures"),
    ]
    
    for variant_id, text, guidance in variants:
        # DALL·E 3 version
        prompts.append(ImagePrompt(
            product_id=product_id,
            model="dalle3",
            variant_id=variant_id,
            text=text,
            guidance_notes=guidance
        ))
        
        # SDXL version (same text)
        prompts.append(ImagePrompt(
            product_id=product_id,
            model="sdxl",
            variant_id=variant_id,
            text=text,
            guidance_notes=guidance
        ))
    
    return prompts


def build_all_prompts() -> Dict[str, List[ImagePrompt]]:
    """
    Build prompts for all products.
    
    Saves to:
      - prompts/q3_prompts.json
      - prompts/q3_prompts.md
    
    Returns:
        Dict mapping product_id to list of ImagePrompt objects
    """
    prompts_by_product = {}
    
    for product_id in PRODUCTS:
        try:
            prompts = build_prompts_for_product(product_id)
            prompts_by_product[product_id] = prompts
        except Exception as e:
            raise RuntimeError(f"Failed to build prompts for {product_id}: {e}")
    
    # Assertions: no "Unknown Product" or "N/A"
    for product_id, prompts in prompts_by_product.items():
        for p in prompts:
            if "Unknown Product" in p.text:
                raise ValueError(f"Prompt for {product_id} contains 'Unknown Product': {p.text[:100]}...")
            if "N/A" in p.text:
                raise ValueError(f"Prompt for {product_id} contains 'N/A': {p.text[:100]}...")
    
    # Save JSON
    PROMPTS_DIR.mkdir(exist_ok=True)
    json_path = PROMPTS_DIR / "q3_prompts.json"
    
    json_data = {}
    for product_id, prompts in prompts_by_product.items():
        json_data[product_id] = [
            {
                "product_id": p.product_id,
                "model": p.model,
                "variant_id": p.variant_id,
                "text": p.text,
                "guidance_notes": p.guidance_notes,
            }
            for p in prompts
        ]
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    # Save Markdown
    md_path = PROMPTS_DIR / "q3_prompts.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# Q3 Image Generation Prompts\n\n")
        f.write("_Generated from Q2 analysis outputs_\n\n")
        
        for product_id in PRODUCTS:
            if product_id not in prompts_by_product:
                continue
            
            f.write(f"## {product_id.upper()}\n\n")
            
            # Group by variant
            for variant_id in ["v1", "v2", "v3"]:
                variant_prompts = [p for p in prompts_by_product[product_id] if p.variant_id == variant_id]
                if not variant_prompts:
                    continue
                
                f.write(f"### Variant {variant_id}\n\n")
                for p in variant_prompts:
                    f.write(f"**{p.model.upper()}:**\n")
                    f.write(f"{p.text}\n\n")
                    f.write(f"*Guidance: {p.guidance_notes}*\n\n")
            
            f.write("\n---\n\n")
    
    print(f"[Q3 Prompts] Saved to {json_path} and {md_path}")
    
    return prompts_by_product


if __name__ == "__main__":
    prompts_by_product = build_all_prompts()
    print(f"\n[Q3 Prompts] Generated {sum(len(p) for p in prompts_by_product.values())} prompts")
    for product_id, prompts in prompts_by_product.items():
        print(f"  {product_id}: {len(prompts)} prompts ({len(prompts)//2} variants × 2 models)")

