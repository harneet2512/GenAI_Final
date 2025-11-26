"""
Pipeline state definition for the agentic workflow.
"""

from typing import TypedDict, Literal, Optional, Dict, Any, List

ProductId = Literal["ps5", "stanley", "jordans"]


class PipelineState(TypedDict, total=False):
    """State for the agentic pipeline."""
    product_id: ProductId
    run_id: str
    html_fingerprint: str
    previous_html_fingerprint: Optional[str]
    input_changed: bool
    raw_data_paths: Dict[str, str]   # e.g. {"raw_reviews": "..."}
    corpus_built: bool
    index_built: bool
    q2_analysis_path: Optional[str]
    q2_summary_path: Optional[str]
    q2_status: str  # "success", "failed", "skipped"
    q2_validation_report: Optional[str]
    q3_manifest_path: Optional[str]
    q3_report_path: Optional[str]
    q3_ai_vs_real_path: Optional[str]
    q3_status: str  # "success", "partial", "skipped", "failed"
    q3_error_reason: Optional[str]
    q3_success_count: int
    q3_failed_count: int
    q3_dalle3_status: Optional[Dict[str, Any]]  # Per-model status
    q3_sdxl_status: Optional[Dict[str, Any]]  # Per-model status
    logs: List[str]

