"""
Generate remaining SDXL images using a new API key.
"""

import sys
import time
import requests
import base64
import json
from pathlib import Path

# New API key
NEW_SDXL_API_KEY = "sk-uxa85GHAaGx757vjvTZQ0B8dRrBijMygHJFwZzWvJtyBXeYV"
STABILITY_API_URL = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"

def find_missing_images():
    """Find all missing SDXL images."""
    missing = []
    products = ["stanley", "jordans"]
    variants = ["v1", "v2", "v3"]
    
    for product_id in products:
        for variant_id in variants:
            for img_idx in [1, 2]:
                filepath = Path(f"images/q3/{product_id}/sdxl/{variant_id}/{variant_id}_{img_idx}.png")
                if not filepath.exists():
                    missing.append((product_id, variant_id, img_idx))
    return missing

def get_prompt(product_id, variant_id):
    """Get the prompt for a product/variant."""
    prompts_path = Path(f"images/q3/{product_id}/prompts.json")
    if not prompts_path.exists():
        return None
    
    with open(prompts_path, encoding='utf-8') as f:
        data = json.load(f)
    
    for p in data.get("prompts", []):
        if p.get("model") == "sdxl" and p.get("variant_id") == variant_id:
            return p.get("text")
    return None

def generate_image(product_id, variant_id, img_idx, api_key):
    """Generate one SDXL image."""
    prompt_text = get_prompt(product_id, variant_id)
    if not prompt_text:
        print(f"  [ERROR] Could not find prompt for {product_id}/{variant_id}")
        return False
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    
    payload = {
        "text_prompts": [{"text": prompt_text}],
        "cfg_scale": 7,
        "width": 1024,
        "height": 1024,
        "samples": 1,
        "steps": 30,
    }
    
    filepath = Path(f"images/q3/{product_id}/sdxl/{variant_id}/{variant_id}_{img_idx}.png")
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        resp = requests.post(STABILITY_API_URL, headers=headers, json=payload, timeout=90)
        
        if resp.status_code == 429:
            print(f"  [RATE LIMITED] Status 429")
            return False
        
        resp.raise_for_status()
        data = resp.json()
        
        artifacts = data.get("artifacts", [])
        if not artifacts or not artifacts[0].get("base64"):
            print(f"  [ERROR] No image data returned")
            return False
        
        image_bytes = base64.b64decode(artifacts[0]["base64"])
        with filepath.open("wb") as f:
            f.write(image_bytes)
        
        print(f"  [OK] Saved {filepath}")
        return True
        
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False

def main():
    print("=" * 60)
    print("Generating Remaining SDXL Images with New API Key")
    print("=" * 60)
    
    missing = find_missing_images()
    
    if not missing:
        print("\n[OK] All SDXL images are already generated!")
        return
    
    print(f"\nFound {len(missing)} missing images:")
    for product_id, variant_id, img_idx in missing:
        print(f"  - {product_id}/{variant_id}_{img_idx}.png")
    
    print(f"\nGenerating with 5 second delays between requests...\n")
    
    success_count = 0
    for i, (product_id, variant_id, img_idx) in enumerate(missing, 1):
        print(f"[{i}/{len(missing)}] {product_id}/{variant_id}_{img_idx}.png")
        
        if generate_image(product_id, variant_id, img_idx, NEW_SDXL_API_KEY):
            success_count += 1
        
        # Wait between requests (except last one)
        if i < len(missing):
            time.sleep(5)
    
    print("\n" + "=" * 60)
    print(f"[OK] Generated {success_count}/{len(missing)} images")
    print("=" * 60)
    
    if success_count == len(missing):
        print("\nAll missing images generated! Run 'python -m analysis.q3_run' to update manifest.")
    else:
        print(f"\n{len(missing) - success_count} images failed. Check errors above.")

if __name__ == "__main__":
    main()


