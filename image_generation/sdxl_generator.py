"""
Stable Diffusion XL (SDXL) Image Generator
Generates images using SDXL API (Stability AI or compatible).
"""

import os
import json
import requests
from typing import List, Dict
from dotenv import load_dotenv
from image_generation.prompt_builder import build_prompts

load_dotenv()


def generate_sdxl_images(product_id: str, prompts: List[Dict], images_per_prompt: int = 5, output_dir: str = "image_generation/outputs/sdxl") -> List[Dict]:
    """
    Generate images using SDXL API.
    
    Args:
        product_id: Product ID
        prompts: List of prompt dictionaries
        images_per_prompt: Number of images to generate per prompt
        output_dir: Output directory
        
    Returns:
        List of image metadata dictionaries
    """
    api_key = os.getenv("SDXL_API_KEY")
    if not api_key:
        raise ValueError("SDXL_API_KEY not found in environment variables")
    
    # Try Stability AI API first
    api_url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
    
    all_metadata = []
    product_output_dir = os.path.join(output_dir, product_id)
    os.makedirs(product_output_dir, exist_ok=True)
    
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    print(f"Generating SDXL images for product {product_id}...")
    
    for prompt_data in prompts:
        prompt_id = prompt_data['prompt_id']
        prompt_text = prompt_data['text']
        
        print(f"  Prompt {prompt_id}: Generating {images_per_prompt} images...")
        
        for i in range(images_per_prompt):
            try:
                # SDXL API call (Stability AI format)
                payload = {
                    "text_prompts": [
                        {
                            "text": prompt_text,
                            "weight": 1.0
                        }
                    ],
                    "cfg_scale": 7,
                    "height": 1024,
                    "width": 1024,
                    "samples": 1,
                    "steps": 30
                }
                
                response = requests.post(api_url, headers=headers, json=payload, timeout=60)
                response.raise_for_status()
                
                result = response.json()
                
                # Extract image (Stability AI returns base64)
                if "artifacts" in result and len(result["artifacts"]) > 0:
                    import base64
                    image_data = base64.b64decode(result["artifacts"][0]["base64"])
                    
                    # Save image
                    filename = f"{prompt_id}_{i+1}.png"
                    filepath = os.path.join(product_output_dir, filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(image_data)
                    
                    # Store metadata
                    metadata = {
                        "product_id": product_id,
                        "prompt_id": prompt_id,
                        "image_index": i + 1,
                        "filepath": filepath,
                        "prompt": prompt_text,
                        "model": "sdxl",
                        "size": "1024x1024",
                        "cfg_scale": 7,
                        "steps": 30
                    }
                    all_metadata.append(metadata)
                    
                    print(f"    [OK] Saved: {filename}")
                else:
                    print(f"    [ERROR] No image in response")
                    
            except requests.exceptions.RequestException as e:
                print(f"    [ERROR] API error: {e}")
                # Fallback: try alternative SDXL API endpoint or format
                try:
                    # Alternative: Replicate API or other SDXL provider
                    print(f"    Trying alternative SDXL endpoint...")
                    # You can add alternative API implementations here
                except Exception as e2:
                    print(f"    [ERROR] Alternative also failed: {e2}")
                continue
            except Exception as e:
                print(f"    [ERROR] Error generating image {i+1}: {e}")
                continue
    
    # Save metadata
    if all_metadata:
        metadata_path = os.path.join(product_output_dir, "metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(all_metadata, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Generated {len(all_metadata)} SDXL images")
    print(f"  Saved to: {product_output_dir}")
    
    return all_metadata


def generate_for_product(product_id: str, images_per_prompt: int = 5) -> List[Dict]:
    """
    Convenience function to generate images for a product.
    
    Args:
        product_id: Product ID
        images_per_prompt: Number of images per prompt
        
    Returns:
        List of image metadata
    """
    # Build prompts
    prompts = build_prompts(product_id, num_variants=3)
    
    # Generate images
    return generate_sdxl_images(product_id, prompts, images_per_prompt=images_per_prompt)


if __name__ == "__main__":
    # Test generation
    test_products = ["B0CKZGY5B6", "B0CJZMP7L1", "B0DJ9SVTB6"]
    
    for product_id in test_products:
        try:
            generate_for_product(product_id, images_per_prompt=5)
        except Exception as e:
            print(f"Error generating images for {product_id}: {e}")

