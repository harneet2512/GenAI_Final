"""
Review Analyzer Agent
Analyzes product reviews and descriptions using RAG + LLM.
"""

from typing import Dict
from agent_workflow.utils.state import WorkflowState
from agent_workflow.utils.loader import load_product_data, load_processed_reviews, load_faiss_index_path
from rag_pipeline.retriever import Retriever
from analysis.llm_analysis import run_full_analysis


def review_analyzer_node(state: WorkflowState) -> WorkflowState:
    """
    LangGraph node that analyzes reviews and product description.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with summary and structured attributes
    """
    product_id = state["product_id"]
    
    try:
        print(f"[Review Analyzer] Processing product {product_id}...")
        
        # Load data
        product_data = load_product_data(product_id)
        processed_reviews = load_processed_reviews(product_id)
        faiss_index_path = load_faiss_index_path(product_id)
        
        # Run full analysis
        analysis_results = run_full_analysis(product_id)
        
        # Update state
        state["product_data"] = product_data
        state["processed_reviews"] = processed_reviews
        state["faiss_index_path"] = faiss_index_path
        state["summary"] = analysis_results.get("self_refined_summary", "")
        state["structured_attributes"] = analysis_results.get("structured_attributes", {})
        state["sentiment_features"] = analysis_results.get("sentiment_features", {})
        
        print(f"[Review Analyzer] [OK] Analysis complete")
        
    except Exception as e:
        error_msg = f"Review analyzer error: {str(e)}"
        print(f"[Review Analyzer] [ERROR] {error_msg}")
        state["errors"].append(error_msg)
    
    return state

