"""
State Management for LangGraph Workflow
Defines the shared state structure for the agentic pipeline.
"""

from typing import Dict, List, Optional, Any
from typing_extensions import TypedDict, Annotated
import operator


class WorkflowState(TypedDict):
    """
    Shared state for the LangGraph workflow.
    """
    product_id: str
    product_data: Optional[Dict[str, Any]]
    processed_reviews: Optional[List[Dict[str, Any]]]
    faiss_index_path: Optional[str]
    summary: Optional[str]
    structured_attributes: Optional[Dict[str, Any]]
    sentiment_features: Optional[Dict[str, Any]]
    prompts: Optional[List[Dict[str, Any]]]
    generated_images_dalle: Optional[List[Dict[str, Any]]]
    generated_images_sdxl: Optional[List[Dict[str, Any]]]
    evaluation_results: Optional[Dict[str, Any]]
    report_snippet: Optional[str]
    errors: Annotated[List[str], operator.add]


def create_initial_state(product_id: str) -> WorkflowState:
    """
    Create initial state for workflow.
    
    Args:
        product_id: Product ID
        
    Returns:
        Initial workflow state
    """
    return {
        "product_id": product_id,
        "product_data": None,
        "processed_reviews": None,
        "faiss_index_path": None,
        "summary": None,
        "structured_attributes": None,
        "sentiment_features": None,
        "prompts": None,
        "generated_images_dalle": None,
        "generated_images_sdxl": None,
        "evaluation_results": None,
        "report_snippet": None,
        "errors": []
    }

