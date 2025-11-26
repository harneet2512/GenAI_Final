"""
HTML fingerprinting to track input changes.
"""

import hashlib
import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional

from .paths import ProductId, PROJECT_ROOT


def compute_html_fingerprint(product_id: ProductId) -> str:
    """
    Compute a deterministic fingerprint for all HTML files for a product.
    
    Args:
        product_id: Product identifier
        
    Returns:
        SHA-256 hex digest of the fingerprint
    """
    from .html_loader import get_html_paths
    
    try:
        html_paths = get_html_paths(product_id)
    except FileNotFoundError:
        # No HTML files - return empty fingerprint
        return hashlib.sha256(b"").hexdigest()
    
    # Collect metadata for each file
    file_metadata = []
    for html_path in sorted(html_paths):
        stat = html_path.stat()
        file_metadata.append({
            "filename": html_path.name,
            "size": stat.st_size,
            "mtime": stat.st_mtime,
        })
    
    # Create deterministic string representation
    metadata_str = json.dumps(file_metadata, sort_keys=True)
    
    # Hash it
    return hashlib.sha256(metadata_str.encode("utf-8")).hexdigest()


def get_state_path(product_id: ProductId) -> Path:
    """Get path to state file for a product."""
    state_dir = PROJECT_ROOT / "agent_app" / "data" / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / f"{product_id}_input.json"


def load_input_state(product_id: ProductId) -> Optional[dict]:
    """
    Load previous input state for a product.
    
    Returns:
        Dict with html_fingerprint and last_run_at, or None if not found
    """
    state_path = get_state_path(product_id)
    if not state_path.exists():
        return None
    
    try:
        with state_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_input_state(product_id: ProductId, html_fingerprint: str) -> None:
    """Save input state for a product."""
    state_path = get_state_path(product_id)
    state = {
        "html_fingerprint": html_fingerprint,
        "last_run_at": datetime.now(UTC).isoformat(),
    }
    with state_path.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

