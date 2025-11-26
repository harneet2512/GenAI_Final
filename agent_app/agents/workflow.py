"""
LangGraph workflow for the agentic pipeline.
"""

from langgraph.graph import StateGraph, END

from .state import PipelineState, ProductId
from .nodes import (
    data_preparation_agent,
    corpus_and_index_agent,
    q2_analysis_agent,
    q2_validation_agent,
    q3_agent,
)
from agent_app.core.fingerprint import (
    compute_html_fingerprint,
    load_input_state,
    save_input_state,
)


def build_pipeline_graph():
    """Build and compile the LangGraph workflow."""
    graph = StateGraph(PipelineState)
    
    # Add nodes
    graph.add_node("data_prep", data_preparation_agent)
    graph.add_node("corpus_index", corpus_and_index_agent)
    graph.add_node("q2_analysis", q2_analysis_agent)
    graph.add_node("q2_validation", q2_validation_agent)
    graph.add_node("q3", q3_agent)
    
    # Define edges
    graph.set_entry_point("data_prep")
    graph.add_edge("data_prep", "corpus_index")
    graph.add_edge("corpus_index", "q2_analysis")
    graph.add_edge("q2_analysis", "q2_validation")
    graph.add_edge("q2_validation", "q3")
    graph.add_edge("q3", END)
    
    return graph.compile()


def run_agentic_pipeline(product_id: ProductId) -> PipelineState:
    """
    Run the full agentic pipeline for a product.
    
    Args:
        product_id: Product identifier (ps5, stanley, jordans)
        
    Returns:
        Final pipeline state
    """
    from datetime import datetime, UTC
    
    # Generate run_id
    run_id = datetime.now(UTC).isoformat()
    
    # Compute current HTML fingerprint
    current_fingerprint = compute_html_fingerprint(product_id)
    
    # Load previous state
    previous_state = load_input_state(product_id)
    previous_fingerprint = previous_state.get("html_fingerprint") if previous_state else None
    
    # Determine if input changed
    input_changed = (current_fingerprint != previous_fingerprint)
    
    # Create initial state
    initial_state: PipelineState = {
        "product_id": product_id,
        "run_id": run_id,
        "html_fingerprint": current_fingerprint,
        "previous_html_fingerprint": previous_fingerprint,
        "input_changed": input_changed,
        "q2_status": "pending",
        "q3_status": "pending",
        "q3_success_count": 0,
        "q3_failed_count": 0,
        "logs": [],
    }
    
    if input_changed:
        initial_state["logs"].append(f"[workflow] HTML input changed (fingerprint: {current_fingerprint[:16]}...)")
    else:
        initial_state["logs"].append(f"[workflow] HTML input unchanged (fingerprint: {current_fingerprint[:16]}...)")
    
    initial_state["logs"].append(f"[workflow] Run ID: {run_id}")
    
    # Run workflow
    workflow = build_pipeline_graph()
    final_state = workflow.invoke(initial_state)
    
    # Persist new fingerprint
    save_input_state(product_id, current_fingerprint)
    final_state["logs"].append(f"[workflow] Saved input state fingerprint")
    
    return final_state

