"""
Prompt Builder for Image Generation
Constructs prompts from analysis data for DALL·E 3 and SDXL.
"""

import json
import os
from typing import List, Dict


def load_analysis(product_id: str, analysis_dir: str = "analysis") -> Dict:
    """
    Load analysis JSON for a product.
    
    Args:
        product_id: Product ID
        analysis_dir: Directory containing analysis files
        
    Returns:
        Analysis dictionary
    """
    analysis_path = os.path.join(analysis_dir, f"{product_id}_analysis.json")
    if not os.path.exists(analysis_path):
        raise FileNotFoundError(f"Analysis not found: {analysis_path}")
    
    with open(analysis_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_prompts(product_id: str, analysis_dir: str = "analysis", num_variants: int = 3) -> List[Dict]:
    """
    Build image generation prompts from analysis data.
    
    Args:
        product_id: Product ID
        analysis_dir: Directory containing analysis files
        num_variants: Number of prompt variants to generate
        
    Returns:
        List of prompt dictionaries
    """
    analysis = load_analysis(product_id, analysis_dir)
    attributes = analysis.get('structured_attributes', {})
    
    product_name = attributes.get('product_name', analysis.get('product_name', 'Unknown Product'))
    shape = attributes.get('shape', 'N/A')
    material = attributes.get('material', 'N/A')
    color_palette = attributes.get('color_palette', [])
    branding = attributes.get('branding_elements', [])
    features = attributes.get('distinctive_features', [])
    contexts = attributes.get('usage_contexts', [])
    
    # Format lists as strings
    color_str = ", ".join(color_palette) if color_palette else "N/A"
    branding_str = ", ".join(branding) if branding else "N/A"
    features_str = ", ".join(features) if features else "N/A"
    contexts_str = ", ".join(contexts) if contexts else "N/A"
    
    prompts = []
    
    # Base prompt variant
    base_prompt = f"""Generate a high-resolution, realistic studio-style product image of {product_name}.

Shape: {shape}.
Material: {material}.
Color palette: {color_str}.
Branding and logos: {branding_str}.
Distinctive features: {features_str}.
Usage context: {contexts_str}.

Focus on accurately reflecting how customers describe its appearance. Professional product photography style, clean white background, studio lighting."""
    
    prompts.append({
        "prompt_id": "p1",
        "text": base_prompt,
        "variant": "base"
    })
    
    # Detailed variant
    if num_variants >= 2:
        detailed_prompt = f"""Create a professional product photograph of {product_name} with the following specifications:

Visual Characteristics:
- Shape and Form: {shape}
- Materials: {material}
- Colors: {color_str}
- Branding Elements: {branding_str}
- Key Features: {features_str}

Context: {contexts_str}

Style: High-end e-commerce product photography, white background, even lighting, sharp focus, accurate color representation. Show the product exactly as customers would see it, emphasizing the visual qualities they appreciate."""
        
        prompts.append({
            "prompt_id": "p2",
            "text": detailed_prompt,
            "variant": "detailed"
        })
    
    # Customer-focused variant
    if num_variants >= 3:
        customer_prompt = f"""Generate a realistic product image of {product_name} that matches customer descriptions:

Product Details:
- Appearance: {shape}, made of {material}
- Color Scheme: {color_str}
- Branding: {branding_str}
- Notable Features: {features_str}
- Typical Use: {contexts_str}

Photography Style: Clean, professional product shot on white background. The image should accurately represent the product's visual appearance as described by customers in reviews. Focus on clarity, accurate colors, and showing all distinctive visual elements."""
        
        prompts.append({
            "prompt_id": "p3",
            "text": customer_prompt,
            "variant": "customer_focused"
        })
    
    return prompts


def save_prompts(product_id: str, prompts: List[Dict], output_dir: str = "image_generation") -> str:
    """
    Save prompts to JSON file.
    
    Args:
        product_id: Product ID
        prompts: List of prompt dictionaries
        output_dir: Output directory
        
    Returns:
        Path to saved file
    """
    os.makedirs(output_dir, exist_ok=True)
    prompts_path = os.path.join(output_dir, f"{product_id}_prompts.json")
    
    with open(prompts_path, 'w', encoding='utf-8') as f:
        json.dump({
            "product_id": product_id,
            "prompts": prompts
        }, f, indent=2, ensure_ascii=False)
    
    return prompts_path


if __name__ == "__main__":
    # Test prompt building
    test_products = ["B0CKZGY5B6", "B0CJZMP7L1", "B0DJ9SVTB6"]
    
    for product_id in test_products:
        try:
            prompts = build_prompts(product_id, num_variants=3)
            save_prompts(product_id, prompts)
            
            print(f"\nProduct {product_id}: Generated {len(prompts)} prompts")
            for prompt in prompts:
                print(f"  {prompt['prompt_id']}: {prompt['text'][:100]}...")
        except Exception as e:
            print(f"Error building prompts for {product_id}: {e}")


