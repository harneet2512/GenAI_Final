"""
Prompt Constructor Agent
Builds image generation prompts from analysis data.
"""

from typing import Dict
from agent_workflow.utils.state import WorkflowState
from image_generation.prompt_builder import build_prompts, save_prompts


def prompt_constructor_node(state: WorkflowState) -> WorkflowState:
    """
    LangGraph node that constructs image generation prompts.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with prompts
    """
    product_id = state["product_id"]
    
    try:
        print(f"[Prompt Constructor] Building prompts for product {product_id}...")
        
        # Build prompts
        prompts = build_prompts(product_id, num_variants=3)
        save_prompts(product_id, prompts)
        
        # Update state
        state["prompts"] = prompts
        
        print(f"[Prompt Constructor] [OK] Generated {len(prompts)} prompts")
        
    except Exception as e:
        error_msg = f"Prompt constructor error: {str(e)}"
        print(f"[Prompt Constructor] [ERROR] {error_msg}")
        state["errors"].append(error_msg)
    
    return state

