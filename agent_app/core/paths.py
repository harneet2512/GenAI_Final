"""
Path utilities for agent_app.
Standardized paths for HTML files and raw review data.
"""

from pathlib import Path
from typing import Literal

ProductId = Literal["ps5", "stanley", "jordans"]

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # go up from agent_app/core


def html_dir(product_id: ProductId) -> Path:
    """Get the HTML directory path for a product."""
    return PROJECT_ROOT / "agent_app" / "data" / "html" / product_id


def raw_reviews_path(product_id: ProductId) -> Path:
    """Get the path for raw reviews JSON output."""
    return PROJECT_ROOT / "agent_app" / "data" / "raw" / f"{product_id}_reviews.json"

