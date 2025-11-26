"""
Evaluation Agent
Compares generated images vs ground truth.
"""

from typing import Dict
from agent_workflow.utils.state import WorkflowState
from image_generation.compare_images import compare_product_images


def evaluation_node(state: WorkflowState) -> WorkflowState:
    """
    LangGraph node that evaluates generated images.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with evaluation results
    """
    product_id = state["product_id"]
    
    try:
        print(f"[Evaluation] Evaluating images for product {product_id}...")
        
        evaluation_results = {
            "dalle": {},
            "sdxl": {}
        }
        
        # Evaluate DALL·E images
        if state.get("generated_images_dalle"):
            print("  Evaluating DALL·E images...")
            dalle_results = compare_product_images(product_id, model="dalle")
            evaluation_results["dalle"] = dalle_results
        
        # Evaluate SDXL images
        if state.get("generated_images_sdxl"):
            print("  Evaluating SDXL images...")
            try:
                sdxl_results = compare_product_images(product_id, model="sdxl")
                evaluation_results["sdxl"] = sdxl_results
            except Exception as e:
                print(f"  Warning: SDXL evaluation failed: {e}")
                evaluation_results["sdxl"] = {}
                state["errors"].append(f"SDXL evaluation error: {str(e)}")
        
        # Update state
        state["evaluation_results"] = evaluation_results
        
        print(f"[Evaluation] [OK] Evaluation complete")
        
    except Exception as e:
        error_msg = f"Evaluation error: {str(e)}"
        print(f"[Evaluation] [ERROR] {error_msg}")
        state["errors"].append(error_msg)
    
    return state

