"""Verify Q3 image generation outputs."""
import json
import os

manifest_path = 'images/q3/q3_image_manifest.json'
if os.path.exists(manifest_path):
    with open(manifest_path, encoding='utf-8') as f:
        m = json.load(f)
    images = m.get("images", [])
    print(f"Manifest: {len(images)} images")
    products = set(img["product_id"] for img in images)
    models = set(img["model"] for img in images)
    print(f"Products: {products}")
    print(f"Models: {models}")
    
    # Count by product and model
    for product in products:
        for model in models:
            count = sum(1 for img in images if img["product_id"] == product and img["model"] == model)
            print(f"  {product} ({model}): {count} images")
else:
    print("Manifest not found")


