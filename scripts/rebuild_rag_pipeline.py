"""
Rebuild RAG Pipeline
====================
Re-parses reviews, rebuilds FAISS indexes, and reports chunk counts.
"""

import json
import os
import subprocess
import sys

def run_command(cmd, description):
    """Run a command and print results."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.stdout:
        print(result.stdout)
    if result.stderr and result.returncode != 0:
        print(f"ERROR: {result.stderr}", file=sys.stderr)
    return result.returncode == 0

def get_chunk_counts():
    """Read chunk counts from metadata files."""
    print(f"\n{'='*60}")
    print("CHUNK COUNTS")
    print(f"{'='*60}")
    
    products = ["ps5", "stanley", "jordans"]
    for product_id in products:
        meta_path = f"rag_pipeline/faiss_indexes/{product_id}_meta.json"
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            if isinstance(metadata, list):
                chunk_count = len(metadata)
            elif isinstance(metadata, dict) and 'chunks' in metadata:
                chunk_count = len(metadata['chunks'])
            else:
                chunk_count = 0
            print(f"{product_id:12s}: {chunk_count:3d} chunks")
        else:
            print(f"{product_id:12s}: No index found")

def get_review_counts():
    """Read review counts from processed JSON files."""
    print(f"\n{'='*60}")
    print("REVIEW COUNTS")
    print(f"{'='*60}")
    
    products = [
        ("ps5", "B0CL61F39H"),
        ("stanley", "B0CJZMP7L1"),
        ("jordans", "B0DJ9SVTB6"),
    ]
    
    for slug, asin in products:
        json_path = f"data/processed/reviews_{slug}_{asin}.json"
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                reviews = json.load(f)
            print(f"{slug:12s}: {len(reviews):3d} reviews")
        else:
            print(f"{slug:12s}: No reviews file found")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("REBUILDING RAG PIPELINE")
    print("="*60)
    
    # Step 1: Re-parse reviews (with duplicate detection)
    success = run_command(
        "python parse_saved_amazon_reviews.py --html-dir data/raw --output-dir data/processed",
        "Step 1: Parsing reviews (with duplicate detection)"
    )
    
    if not success:
        print("\n[ERROR] Failed to parse reviews. Stopping.")
        sys.exit(1)
    
    # Step 2: Show review counts
    get_review_counts()
    
    # Step 3: Rebuild FAISS indexes
    success = run_command(
        "python -m rag_pipeline.embedder",
        "Step 2: Rebuilding FAISS indexes"
    )
    
    if not success:
        print("\n[ERROR] Failed to build indexes. Stopping.")
        sys.exit(1)
    
    # Step 4: Show chunk counts
    get_chunk_counts()
    
    print(f"\n{'='*60}")
    print("REBUILD COMPLETE!")
    print(f"{'='*60}\n")


