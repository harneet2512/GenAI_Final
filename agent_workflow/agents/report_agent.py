"""
Report Agent
Assembles final report snippet for the product.
"""

import os
from typing import Dict
from agent_workflow.utils.state import WorkflowState


def report_node(state: WorkflowState) -> WorkflowState:
    """
    LangGraph node that generates report snippet.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with report snippet
    """
    product_id = state["product_id"]
    
    try:
        print(f"[Report] Generating report snippet for product {product_id}...")
        
        # Extract data from state
        product_name = state.get("product_data", {}).get("title", "Unknown Product")
        structured_attrs = state.get("structured_attributes", {})
        sentiment_features = state.get("sentiment_features", {})
        prompts = state.get("prompts", [])
        eval_results = state.get("evaluation_results", {})
        
        # Build report snippet
        snippet = f"""# Product: {product_name}

**Product ID:** {product_id}

## Key Visual Attributes

- **Shape:** {structured_attrs.get('shape', 'N/A')}
- **Material:** {structured_attrs.get('material', 'N/A')}
- **Color Palette:** {', '.join(structured_attrs.get('color_palette', [])) or 'N/A'}
- **Branding Elements:** {', '.join(structured_attrs.get('branding_elements', [])) or 'N/A'}
- **Distinctive Features:** {', '.join(structured_attrs.get('distinctive_features', [])) or 'N/A'}

## Prompt Design

Generated {len(prompts)} prompt variants:
"""
        
        for prompt in prompts:
            snippet += f"\n### {prompt.get('prompt_id', 'Unknown')} ({prompt.get('variant', 'base')})\n\n"
            snippet += f"{prompt.get('text', '')[:200]}...\n"
        
        # Model comparison
        snippet += "\n## Model Comparison\n\n"
        
        dalle_eval = eval_results.get("dalle", {})
        sdxl_eval = eval_results.get("sdxl", {})
        
        if dalle_eval:
            snippet += f"### DALL·E 3\n"
            snippet += f"- Average CLIP Similarity: {dalle_eval.get('average_clip_similarity', 0):.3f}\n"
            snippet += f"- Average Color Similarity: {dalle_eval.get('average_color_similarity', 0):.3f}\n"
            snippet += f"- Average SSIM: {dalle_eval.get('average_ssim', 0):.3f}\n"
            snippet += f"- Overall Average: {dalle_eval.get('average_overall', 0):.3f}\n\n"
        
        if sdxl_eval:
            snippet += f"### SDXL\n"
            snippet += f"- Average CLIP Similarity: {sdxl_eval.get('average_clip_similarity', 0):.3f}\n"
            snippet += f"- Average Color Similarity: {sdxl_eval.get('average_color_similarity', 0):.3f}\n"
            snippet += f"- Average SSIM: {sdxl_eval.get('average_ssim', 0):.3f}\n"
            snippet += f"- Overall Average: {sdxl_eval.get('average_overall', 0):.3f}\n\n"
        
        # Determine better model
        if dalle_eval and sdxl_eval:
            dalle_score = dalle_eval.get('average_overall', 0)
            sdxl_score = sdxl_eval.get('average_overall', 0)
            
            if dalle_score > sdxl_score:
                snippet += f"**Better Model:** DALL·E 3 (score: {dalle_score:.3f} vs {sdxl_score:.3f})\n\n"
            elif sdxl_score > dalle_score:
                snippet += f"**Better Model:** SDXL (score: {sdxl_score:.3f} vs {dalle_score:.3f})\n\n"
            else:
                snippet += "**Better Model:** Tie\n\n"
        
        # Notable findings
        snippet += "## Notable Findings\n\n"
        
        positive_features = sentiment_features.get("positive_visual_features", [])
        negative_features = sentiment_features.get("negative_visual_features", [])
        
        if positive_features:
            snippet += "### Positive Visual Themes\n"
            for feat in positive_features[:3]:
                snippet += f"- {feat.get('feature', 'N/A')}: {feat.get('mentions', 'N/A')}\n"
            snippet += "\n"
        
        if negative_features:
            snippet += "### Negative Visual Themes\n"
            for feat in negative_features[:3]:
                snippet += f"- {feat.get('feature', 'N/A')}: {feat.get('mentions', 'N/A')}\n"
            snippet += "\n"
        
        # Hallucinations/mismatches
        snippet += "## Potential Hallucinations/Mismatches\n\n"
        snippet += "Review generated images against ground truth to identify:\n"
        snippet += "- Color discrepancies\n"
        snippet += "- Shape/form differences\n"
        snippet += "- Missing branding elements\n"
        snippet += "- Incorrect material representation\n"
        
        # Save snippet
        os.makedirs("report/workflow_outputs", exist_ok=True)
        snippet_path = f"report/workflow_outputs/{product_id}_snippet.md"
        with open(snippet_path, 'w', encoding='utf-8') as f:
            f.write(snippet)
        
        # Update state
        state["report_snippet"] = snippet
        
        print(f"[Report] [OK] Report snippet saved to {snippet_path}")
        
    except Exception as e:
        error_msg = f"Report generation error: {str(e)}"
        print(f"[Report] [ERROR] {error_msg}")
        state["errors"].append(error_msg)
    
    return state

