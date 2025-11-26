"""
LangGraph Workflow Definition
Orchestrates the full agentic pipeline for product image generation.
"""

from typing import Dict
from langgraph.graph import StateGraph, END
from agent_workflow.utils.state import WorkflowState, create_initial_state
from agent_workflow.agents.review_analyzer_agent import review_analyzer_node
from agent_workflow.agents.prompt_constructor_agent import prompt_constructor_node
from agent_workflow.agents.image_generator_agent import image_generator_node
from agent_workflow.agents.evaluation_agent import evaluation_node
from agent_workflow.agents.report_agent import report_node


def create_workflow_graph() -> StateGraph:
    """
    Create the LangGraph workflow graph.
    
    Returns:
        Compiled StateGraph
    """
    # Create graph
    workflow = StateGraph(WorkflowState)
    
    # Add nodes
    workflow.add_node("review_analyzer", review_analyzer_node)
    workflow.add_node("prompt_constructor", prompt_constructor_node)
    workflow.add_node("image_generator", image_generator_node)
    workflow.add_node("evaluation", evaluation_node)
    workflow.add_node("report", report_node)
    
    # Define edges
    workflow.set_entry_point("review_analyzer")
    workflow.add_edge("review_analyzer", "prompt_constructor")
    workflow.add_edge("prompt_constructor", "image_generator")
    workflow.add_edge("image_generator", "evaluation")
    workflow.add_edge("evaluation", "report")
    workflow.add_edge("report", END)
    
    # Compile graph
    return workflow.compile()


def run_full_workflow(product_id: str) -> Dict:
    """
    Orchestrate the full agentic pipeline for a single product.
    
    Args:
        product_id: Product ID (ASIN)
        
    Returns:
        Final workflow state
    """
    print(f"\n{'='*60}")
    print(f"Starting workflow for product: {product_id}")
    print(f"{'='*60}\n")
    
    # Create initial state
    initial_state = create_initial_state(product_id)
    
    # Create and run graph
    graph = create_workflow_graph()
    
    try:
        # Run workflow
        final_state = graph.invoke(initial_state)
        
        print(f"\n{'='*60}")
        print(f"Workflow complete for product: {product_id}")
        print(f"{'='*60}\n")
        
        if final_state.get("errors"):
            print(f"Errors encountered: {len(final_state['errors'])}")
            for error in final_state["errors"]:
                print(f"  - {error}")
        
        return final_state
        
    except Exception as e:
        print(f"\n[ERROR] Workflow failed: {e}")
        initial_state["errors"].append(f"Workflow execution error: {str(e)}")
        return initial_state


if __name__ == "__main__":
    # Test workflow with provided products
    test_products = ["B0CKZGY5B6", "B0CJZMP7L1", "B0DJ9SVTB6"]
    
    for product_id in test_products:
        try:
            run_full_workflow(product_id)
        except Exception as e:
            print(f"Error running workflow for {product_id}: {e}")

