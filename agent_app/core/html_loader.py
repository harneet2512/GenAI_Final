"""
HTML loader for local HTML files.
No network IO allowed - all HTML must be local.
"""

from pathlib import Path
from typing import List

from .paths import ProductId, html_dir


def get_html_paths(product_id: ProductId) -> List[Path]:
    """
    Get all HTML file paths for a product.
    
    Raises:
        FileNotFoundError: If directory doesn't exist or no HTML files found
    """
    base = html_dir(product_id)
    if not base.exists():
        raise FileNotFoundError(f"No HTML directory for {product_id}: {base}")
    
    paths = sorted(p for p in base.glob("*.html") if p.is_file())
    if not paths:
        raise FileNotFoundError(f"No HTML files found for {product_id} in {base}")
    
    return paths


def load_html_contents(product_id: ProductId) -> List[str]:
    """
    Load all HTML file contents for a product.
    
    Returns:
        List of HTML content strings (one per file)
    """
    contents: List[str] = []
    for p in get_html_paths(product_id):
        contents.append(p.read_text(encoding="utf-8", errors="ignore"))
    return contents

