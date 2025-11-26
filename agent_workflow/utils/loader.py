"""
Data Loader Utilities for Agent Workflow
Functions to load various data types needed by agents.
"""

import json
import os
from typing import Dict, List, Optional


def load_product_data(product_id: str, data_dir: str = "data") -> Dict:
    """
    Load product data from JSON file.
    
    Args:
        product_id: Product ID
        data_dir: Data directory
        
    Returns:
        Product data dictionary
    """
    product_path = os.path.join(data_dir, "raw", f"{product_id}_product.json")
    if not os.path.exists(product_path):
        raise FileNotFoundError(f"Product data not found: {product_path}")
    
    with open(product_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_processed_reviews(product_id: str, data_dir: str = "data") -> List[Dict]:
    """
    Load processed reviews from JSON file.
    
    Args:
        product_id: Product ID
        data_dir: Data directory
        
    Returns:
        List of review dictionaries
    """
    reviews_path = os.path.join(data_dir, "processed", f"{product_id}_reviews_processed.json")
    if not os.path.exists(reviews_path):
        raise FileNotFoundError(f"Processed reviews not found: {reviews_path}")
    
    with open(reviews_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_faiss_index_path(product_id: str, index_dir: str = "rag_pipeline/faiss_indexes") -> str:
    """
    Get path to FAISS index for product.
    
    Args:
        product_id: Product ID
        index_dir: Index directory
        
    Returns:
        Path to index file
    """
    index_path = os.path.join(index_dir, f"{product_id}.index")
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"FAISS index not found: {index_path}")
    
    return index_path


def load_analysis_json(product_id: str, analysis_dir: str = "analysis") -> Dict:
    """
    Load analysis JSON for product.
    
    Args:
        product_id: Product ID
        analysis_dir: Analysis directory
        
    Returns:
        Analysis dictionary
    """
    analysis_path = os.path.join(analysis_dir, f"{product_id}_analysis.json")
    if not os.path.exists(analysis_path):
        raise FileNotFoundError(f"Analysis not found: {analysis_path}")
    
    with open(analysis_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_prompts(product_id: str, prompts_dir: str = "image_generation") -> List[Dict]:
    """
    Load prompts for product.
    
    Args:
        product_id: Product ID
        prompts_dir: Prompts directory
        
    Returns:
        List of prompt dictionaries
    """
    prompts_path = os.path.join(prompts_dir, f"{product_id}_prompts.json")
    if not os.path.exists(prompts_path):
        raise FileNotFoundError(f"Prompts not found: {prompts_path}")
    
    with open(prompts_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('prompts', [])


def load_image_paths(product_id: str, model: str, output_dir: str = "image_generation/outputs") -> List[str]:
    """
    Load paths to generated images.
    
    Args:
        product_id: Product ID
        model: Model name (dalle or sdxl)
        output_dir: Output directory
        
    Returns:
        List of image file paths
    """
    model_dir = os.path.join(output_dir, model, product_id)
    if not os.path.exists(model_dir):
        return []
    
    image_paths = []
    for filename in os.listdir(model_dir):
        if filename.endswith('.png') and not filename.startswith('metadata'):
            image_paths.append(os.path.join(model_dir, filename))
    
    return sorted(image_paths)


