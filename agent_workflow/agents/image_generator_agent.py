"""
Image Generator Agent
Generates images using DALL·E 3 and SDXL.
"""

from typing import Dict
from agent_workflow.utils.state import WorkflowState
from image_generation.dalle_generator import generate_dalle_images
from image_generation.sdxl_generator import generate_sdxl_images


def image_generator_node(state: WorkflowState) -> WorkflowState:
    """
    LangGraph node that generates images using both models.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with generated image metadata
    """
    product_id = state["product_id"]
    prompts = state.get("prompts", [])
    
    if not prompts:
        error_msg = "No prompts available for image generation"
        print(f"[Image Generator] ✗ {error_msg}")
        state["errors"].append(error_msg)
        return state
    
    try:
        print(f"[Image Generator] Generating images for product {product_id}...")
        
        # Generate DALL·E images
        print("  Generating DALL·E 3 images...")
        dalle_images = generate_dalle_images(product_id, prompts, images_per_prompt=5)
        state["generated_images_dalle"] = dalle_images
        
        # Generate SDXL images
        print("  Generating SDXL images...")
        try:
            sdxl_images = generate_sdxl_images(product_id, prompts, images_per_prompt=5)
            state["generated_images_sdxl"] = sdxl_images
        except Exception as e:
            print(f"  Warning: SDXL generation failed: {e}")
            state["generated_images_sdxl"] = []
            state["errors"].append(f"SDXL generation error: {str(e)}")
        
        print(f"[Image Generator] [OK] Generated images")
        print(f"  DALL·E: {len(dalle_images)} images")
        print(f"  SDXL: {len(state.get('generated_images_sdxl', []))} images")
        
    except Exception as e:
        error_msg = f"Image generator error: {str(e)}"
        print(f"[Image Generator] ✗ {error_msg}")
        state["errors"].append(error_msg)
    
    return state

