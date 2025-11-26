"""
Image Comparison Module
Compares generated images vs ground truth using CLIP, color histograms, and SSIM.
"""

import os
import json
import numpy as np
from typing import List, Dict, Tuple
from PIL import Image
import requests
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

try:
    from sentence_transformers import SentenceTransformer
    CLIP_AVAILABLE = True
except ImportError:
    CLIP_AVAILABLE = False
    print("Warning: sentence-transformers not available. CLIP comparison will be skipped.")

try:
    from skimage.metrics import structural_similarity as ssim
    SSIM_AVAILABLE = True
except ImportError:
    SSIM_AVAILABLE = False
    print("Warning: scikit-image not available. SSIM comparison will be skipped.")


def load_image(image_path: str) -> np.ndarray:
    """
    Load image from file path or URL.
    
    Args:
        image_path: Path to image file or URL
        
    Returns:
        Image as numpy array
    """
    if image_path.startswith('http'):
        response = requests.get(image_path)
        img = Image.open(BytesIO(response.content))
    else:
        img = Image.open(image_path)
    
    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    return np.array(img)


def clip_similarity(img1: np.ndarray, img2: np.ndarray) -> float:
    """
    Compute CLIP embedding cosine similarity between two images.
    
    Args:
        img1: First image as numpy array
        img2: Second image as numpy array
        
    Returns:
        Cosine similarity score (0-1)
    """
    if not CLIP_AVAILABLE:
        return 0.0
    
    try:
        model = SentenceTransformer('clip-ViT-B-32')
        
        # Resize images to reasonable size for CLIP
        img1_pil = Image.fromarray(img1).resize((224, 224))
        img2_pil = Image.fromarray(img2).resize((224, 224))
        
        # Get embeddings
        emb1 = model.encode(img1_pil)
        emb2 = model.encode(img2_pil)
        
        # Compute cosine similarity
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        
        return float(similarity)
    except Exception as e:
        print(f"Error computing CLIP similarity: {e}")
        return 0.0


def color_histogram_similarity(img1: np.ndarray, img2: np.ndarray, bins: int = 256) -> float:
    """
    Compute color histogram similarity using correlation.
    
    Args:
        img1: First image as numpy array
        img2: Second image as numpy array
        bins: Number of histogram bins
        
    Returns:
        Correlation coefficient (0-1)
    """
    try:
        # Compute histograms for each channel
        hist1_r = np.histogram(img1[:, :, 0], bins=bins, range=(0, 256))[0]
        hist1_g = np.histogram(img1[:, :, 1], bins=bins, range=(0, 256))[0]
        hist1_b = np.histogram(img1[:, :, 2], bins=bins, range=(0, 256))[0]
        
        hist2_r = np.histogram(img2[:, :, 0], bins=bins, range=(0, 256))[0]
        hist2_g = np.histogram(img2[:, :, 1], bins=bins, range=(0, 256))[0]
        hist2_b = np.histogram(img2[:, :, 2], bins=bins, range=(0, 256))[0]
        
        # Normalize histograms
        hist1_r = hist1_r / (hist1_r.sum() + 1e-10)
        hist1_g = hist1_g / (hist1_g.sum() + 1e-10)
        hist1_b = hist1_b / (hist1_b.sum() + 1e-10)
        
        hist2_r = hist2_r / (hist2_r.sum() + 1e-10)
        hist2_g = hist2_g / (hist2_g.sum() + 1e-10)
        hist2_b = hist2_b / (hist2_b.sum() + 1e-10)
        
        # Compute correlation for each channel
        corr_r = np.corrcoef(hist1_r, hist2_r)[0, 1]
        corr_g = np.corrcoef(hist1_g, hist2_g)[0, 1]
        corr_b = np.corrcoef(hist1_b, hist2_b)[0, 1]
        
        # Average correlation
        avg_corr = (corr_r + corr_g + corr_b) / 3.0
        
        # Normalize to 0-1 range
        return float(max(0.0, min(1.0, (avg_corr + 1) / 2)))
    except Exception as e:
        print(f"Error computing color histogram similarity: {e}")
        return 0.0


def ssim_similarity(img1: np.ndarray, img2: np.ndarray) -> float:
    """
    Compute Structural Similarity Index (SSIM) between two images.
    
    Args:
        img1: First image as numpy array
        img2: Second image as numpy array
        
    Returns:
        SSIM score (0-1)
    """
    if not SSIM_AVAILABLE:
        return 0.0
    
    try:
        # Resize images to same size
        img1_pil = Image.fromarray(img1)
        img2_pil = Image.fromarray(img2)
        
        target_size = (256, 256)
        img1_resized = np.array(img1_pil.resize(target_size))
        img2_resized = np.array(img2_pil.resize(target_size))
        
        # Convert to grayscale for SSIM
        if len(img1_resized.shape) == 3:
            img1_gray = np.mean(img1_resized, axis=2)
        else:
            img1_gray = img1_resized
        
        if len(img2_resized.shape) == 3:
            img2_gray = np.mean(img2_resized, axis=2)
        else:
            img2_gray = img2_resized
        
        # Compute SSIM
        score = ssim(img1_gray, img2_gray, data_range=255)
        
        return float(score)
    except Exception as e:
        print(f"Error computing SSIM: {e}")
        return 0.0


def compare_image_pair(img1_path: str, img2_path: str) -> Dict:
    """
    Compare two images using all available metrics.
    
    Args:
        img1_path: Path to first image
        img2_path: Path to second image
        
    Returns:
        Dictionary with similarity scores
    """
    try:
        img1 = load_image(img1_path)
        img2 = load_image(img2_path)
        
        results = {
            "img1": img1_path,
            "img2": img2_path,
            "clip_similarity": clip_similarity(img1, img2),
            "color_histogram_similarity": color_histogram_similarity(img1, img2),
            "ssim": ssim_similarity(img1, img2)
        }
        
        # Compute average similarity
        similarities = [
            results["clip_similarity"],
            results["color_histogram_similarity"],
            results["ssim"]
        ]
        results["average_similarity"] = float(np.mean([s for s in similarities if s > 0]))
        
        return results
    except Exception as e:
        print(f"Error comparing images {img1_path} and {img2_path}: {e}")
        return {
            "img1": img1_path,
            "img2": img2_path,
            "clip_similarity": 0.0,
            "color_histogram_similarity": 0.0,
            "ssim": 0.0,
            "average_similarity": 0.0,
            "error": str(e)
        }


def download_ground_truth_images(product_id: str, product_data: Dict, output_dir: str = "image_generation/ground_truth", max_images: int = 5) -> List[str]:
    """
    Download ground truth images from product data.
    
    Args:
        product_id: Product ID
        product_data: Product data dictionary with image URLs
        output_dir: Output directory
        max_images: Maximum number of images to download
        
    Returns:
        List of downloaded image file paths
    """
    image_urls = product_data.get('main_image_urls', [])
    if not image_urls:
        print(f"No ground truth images found for product {product_id}")
        return []
    
    product_output_dir = os.path.join(output_dir, product_id)
    os.makedirs(product_output_dir, exist_ok=True)
    
    downloaded_paths = []
    
    for i, url in enumerate(image_urls[:max_images]):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            filename = f"real_{i+1}.png"
            filepath = os.path.join(product_output_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            downloaded_paths.append(filepath)
            print(f"  [OK] Downloaded: {filename}")
        except Exception as e:
            print(f"  [ERROR] Error downloading image {i+1}: {e}")
    
    return downloaded_paths


def compare_product_images(product_id: str, model: str = "dalle", report_dir: str = "report") -> Dict:
    """
    Compare all generated images vs ground truth for a product.
    
    Args:
        product_id: Product ID
        model: Model name (dalle or sdxl)
        report_dir: Report directory
        
    Returns:
        Dictionary with comparison results
    """
    # Load product data
    product_path = f"data/raw/{product_id}_product.json"
    if not os.path.exists(product_path):
        raise FileNotFoundError(f"Product data not found: {product_path}")
    
    with open(product_path, 'r', encoding='utf-8') as f:
        product_data = json.load(f)
    
    # Download ground truth images if not already present
    ground_truth_dir = "image_generation/ground_truth"
    ground_truth_paths = []
    
    gt_product_dir = os.path.join(ground_truth_dir, product_id)
    if os.path.exists(gt_product_dir):
        # Load existing ground truth images
        for filename in os.listdir(gt_product_dir):
            if filename.startswith('real_') and filename.endswith('.png'):
                ground_truth_paths.append(os.path.join(gt_product_dir, filename))
    else:
        # Download ground truth images
        ground_truth_paths = download_ground_truth_images(product_id, product_data, ground_truth_dir)
    
    if not ground_truth_paths:
        print(f"No ground truth images available for {product_id}")
        return {}
    
    # Load generated images metadata
    generated_dir = f"image_generation/outputs/{model}/{product_id}"
    metadata_path = os.path.join(generated_dir, "metadata.json")
    
    if not os.path.exists(metadata_path):
        print(f"No generated images found for {product_id} with model {model}")
        return {}
    
    with open(metadata_path, 'r', encoding='utf-8') as f:
        generated_metadata = json.load(f)
    
    # Compare each generated image with each ground truth image
    all_comparisons = []
    
    for gen_meta in generated_metadata:
        gen_path = gen_meta['filepath']
        if not os.path.exists(gen_path):
            continue
        
        for gt_path in ground_truth_paths:
            comparison = compare_image_pair(gen_path, gt_path)
            comparison['generated_image'] = gen_meta['prompt_id']
            comparison['generated_index'] = gen_meta['image_index']
            all_comparisons.append(comparison)
    
    # Aggregate statistics
    if all_comparisons:
        clip_scores = [c['clip_similarity'] for c in all_comparisons if c.get('clip_similarity', 0) > 0]
        color_scores = [c['color_histogram_similarity'] for c in all_comparisons]
        ssim_scores = [c['ssim'] for c in all_comparisons if c.get('ssim', 0) > 0]
        avg_scores = [c['average_similarity'] for c in all_comparisons]
        
        stats = {
            "product_id": product_id,
            "model": model,
            "num_generated": len(generated_metadata),
            "num_ground_truth": len(ground_truth_paths),
            "num_comparisons": len(all_comparisons),
            "average_clip_similarity": float(np.mean(clip_scores)) if clip_scores else 0.0,
            "average_color_similarity": float(np.mean(color_scores)) if color_scores else 0.0,
            "average_ssim": float(np.mean(ssim_scores)) if ssim_scores else 0.0,
            "average_overall": float(np.mean(avg_scores)) if avg_scores else 0.0,
            "max_clip_similarity": float(np.max(clip_scores)) if clip_scores else 0.0,
            "max_color_similarity": float(np.max(color_scores)) if color_scores else 0.0,
            "max_ssim": float(np.max(ssim_scores)) if ssim_scores else 0.0,
            "comparisons": all_comparisons
        }
        
        # Save results
        os.makedirs(report_dir, exist_ok=True)
        results_path = os.path.join(report_dir, f"q3_image_comparison_{product_id}_{model}.json")
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        return stats
    
    return {}


if __name__ == "__main__":
    # Test comparison
    test_products = ["B0CKZGY5B6", "B0CJZMP7L1", "B0DJ9SVTB6"]
    
    for product_id in test_products:
        for model in ["dalle", "sdxl"]:
            try:
                results = compare_product_images(product_id, model=model)
                if results:
                    print(f"\n{product_id} ({model}):")
                    print(f"  Average CLIP: {results['average_clip_similarity']:.3f}")
                    print(f"  Average Color: {results['average_color_similarity']:.3f}")
                    print(f"  Average SSIM: {results['average_ssim']:.3f}")
            except Exception as e:
                print(f"Error comparing {product_id} ({model}): {e}")

