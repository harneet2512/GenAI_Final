"""
DALL·E 3 Image Generator
Generates images using OpenAI's DALL·E 3 API.
"""

import os
import json
import requests
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv
from image_generation.prompt_builder import build_prompts, save_prompts

load_dotenv()


def generate_dalle_images(product_id: str, prompts: List[Dict], images_per_prompt: int = 5, output_dir: str = "image_generation/outputs/dalle") -> List[Dict]:
    """
    Generate images using DALL·E 3.
    
    Args:
        product_id: Product ID
        prompts: List of prompt dictionaries
        images_per_prompt: Number of images to generate per prompt
        output_dir: Output directory
        
    Returns:
        List of image metadata dictionaries
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    all_metadata = []
    product_output_dir = os.path.join(output_dir, product_id)
    os.makedirs(product_output_dir, exist_ok=True)
    
    print(f"Generating DALL·E 3 images for product {product_id}...")
    
    for prompt_data in prompts:
        prompt_id = prompt_data['prompt_id']
        prompt_text = prompt_data['text']
        
        print(f"  Prompt {prompt_id}: Generating {images_per_prompt} images...")
        
        for i in range(images_per_prompt):
            try:
                # DALL·E 3 API call
                response = client.images.generate(
                    model="dall-e-3",
                    prompt=prompt_text,
                    size="1024x1024",
                    quality="standard",
                    n=1
                )
                
                image_url = response.data[0].url
                
                # Download image
                img_response = requests.get(image_url)
                img_response.raise_for_status()
                
                # Save image
                filename = f"{prompt_id}_{i+1}.png"
                filepath = os.path.join(product_output_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(img_response.content)
                
                # Store metadata
                metadata = {
                    "product_id": product_id,
                    "prompt_id": prompt_id,
                    "image_index": i + 1,
                    "filepath": filepath,
                    "prompt": prompt_text,
                    "model": "dall-e-3",
                    "size": "1024x1024",
                    "quality": "standard"
                }
                all_metadata.append(metadata)
                
                print(f"    [OK] Saved: {filename}")
                
            except Exception as e:
                print(f"    [ERROR] Error generating image {i+1}: {e}")
                continue
    
    # Save metadata
    metadata_path = os.path.join(product_output_dir, "metadata.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(all_metadata, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Generated {len(all_metadata)} DALL·E 3 images")
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
    save_prompts(product_id, prompts)
    
    # Generate images
    return generate_dalle_images(product_id, prompts, images_per_prompt=images_per_prompt)


if __name__ == "__main__":
    # Test generation
    test_products = ["B0CKZGY5B6", "B0CJZMP7L1", "B0DJ9SVTB6"]
    
    for product_id in test_products:
        try:
            generate_for_product(product_id, images_per_prompt=5)
        except Exception as e:
            print(f"Error generating images for {product_id}: {e}")

