"""
Q3 Image Generation Pipeline
Generates product images with DALL·E 3 and SDXL (HTTP API) and writes reports.
"""

from __future__ import annotations

import base64
import json
import os
import time
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import requests
from dotenv import load_dotenv
from openai import OpenAI

from analysis.q3_prompt_builder import ImagePrompt, build_all_prompts
from rag_pipeline.corpus import PRODUCTS

load_dotenv()

BASE_OUTPUT_DIR = Path("images/q3")
MANIFEST_PATH = BASE_OUTPUT_DIR / "q3_image_manifest.json"
DALLE_SUBDIR = "dalle3"
SDXL_SUBDIR = "sdxl"

REPORT_DIR = Path("report")
REPORT_IMAGE_GEN = REPORT_DIR / "q3_image_generation.md"
REPORT_AI_VS_REAL = REPORT_DIR / "q3_ai_vs_real.md"

STABILITY_API_URL = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"

# Assignment-aligned image counts
IMAGES_PER_PROMPT_PER_MODEL = 1
PROMPTS_PER_PRODUCT = 3

# SDXL retry configuration - fail fast on rate limits
SDXL_MAX_RETRIES = 2  # Reduced from 5 to fail fast


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _save_json(path: Path, data: Dict | List) -> None:
    _ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _save_prompts_to_output(product_id: str, prompts: List[ImagePrompt]) -> None:
    """Save prompts to output directory for reference."""
    prompts_path = BASE_OUTPUT_DIR / product_id / "prompts.json"
    prompts_data = [
        {
            "product_id": p.product_id,
            "model": p.model,
            "variant_id": p.variant_id,
            "text": p.text,
            "guidance_notes": p.guidance_notes,
        }
        for p in prompts
    ]
    _save_json(prompts_path, {"product_id": product_id, "prompts": prompts_data})


def _cleanup_old_images(product_id: str, model: str, only_if_success: bool = False) -> None:
    """
    Clean up old images for a specific product/model.
    
    Args:
        product_id: Product ID
        model: Model name ("dalle3" or "sdxl")
        only_if_success: If True, only archive if at least one new image was generated (for SDXL)
    """
    model_dir = BASE_OUTPUT_DIR / product_id / model
    if not model_dir.exists():
        return
    
    # For DALL·E: always archive at start (existing behavior)
    # For SDXL: only_if_success flag is checked by caller before invoking this function
    # This function just performs the archiving
    
    # Move old images to archive subfolder instead of deleting
    archive_dir = model_dir / "archive"
    archive_dir.mkdir(exist_ok=True)
    
    # Move all PNG files to archive with timestamp
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    archived_count = 0
    for png_file in model_dir.rglob("*.png"):
        if png_file.parent.name != "archive":  # Don't move archived files
            archive_name = archive_dir / f"{timestamp}_{png_file.name}"
            try:
                png_file.rename(archive_name)
                archived_count += 1
            except Exception as e:
                print(f"  [Cleanup] Warning: Could not archive {png_file.name}: {e}")
    
    if archived_count > 0:
        print(f"  [Cleanup] Archived {archived_count} old {model} image(s)")


def generate_dalle3_images(
    product_id: str,
    prompts: List[ImagePrompt],
    run_id: str,
    run_started_at: str,
    images_per_prompt: Optional[int] = None,
) -> Tuple[List[Dict], int, int, Dict]:
    """
    Generate images with DALL·E 3 using the OpenAI Images API.
    
    Returns:
        Tuple of (metadata list, success count, failed count, model_status dict)
    """
    if images_per_prompt is None:
        images_per_prompt = IMAGES_PER_PROMPT_PER_MODEL
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[DALL·E] OPENAI_API_KEY not set, skipping DALL·E generation.")
        model_status = {
            "status": "failed",
            "reason": "api_key_missing",
            "message": "OPENAI_API_KEY not set",
            "num_images": 0
        }
        return [], 0, 0, model_status

    # Filter to only DALL·E prompts, limit to PROMPTS_PER_PRODUCT
    dalle_prompts = [p for p in prompts if p.model == "dalle3"][:PROMPTS_PER_PRODUCT]
    if not dalle_prompts:
        model_status = {
            "status": "skipped",
            "reason": "no_prompts",
            "message": "No DALL·E prompts available",
            "num_images": 0
        }
        return [], 0, 0, model_status

    # Clean up old DALL·E images at start (existing behavior)
    _cleanup_old_images(product_id, DALLE_SUBDIR, only_if_success=False)

    client = OpenAI(api_key=api_key)
    product_dir = BASE_OUTPUT_DIR / product_id / DALLE_SUBDIR
    _ensure_dir(product_dir)

    metadata: List[Dict] = []
    success_count = 0
    failed_count = 0
    print(f"[DALL·E] Generating {images_per_prompt} image(s) per prompt for {product_id} ({len(dalle_prompts)} prompts) ...")

    for prompt in dalle_prompts:
        variant_dir = product_dir / prompt.variant_id
        _ensure_dir(variant_dir)

        for idx in range(images_per_prompt):
            filename = f"{prompt.variant_id}_{idx + 1}.png"
            filepath = variant_dir / filename
            
            try:
                response = client.images.generate(
                    model="dall-e-3",
                    prompt=prompt.text,
                    size="1024x1024",
                    quality="standard",
                    n=1,
                )
                image_url = response.data[0].url
                img_resp = requests.get(image_url, timeout=60)
                img_resp.raise_for_status()

                with filepath.open("wb") as f:
                    f.write(img_resp.content)

                metadata.append(
                    {
                        "product_id": product_id,
                        "model": "dalle3",
                        "prompt_id": prompt.variant_id,
                        "prompt_text": prompt.text,
                        "output_path": str(filepath.relative_to(BASE_OUTPUT_DIR)),
                        "run_id": run_id,
                        "run_started_at": run_started_at,
                        "run_finished_at": datetime.now(UTC).isoformat(),
                        "status": "success",
                        "image_index": idx + 1,
                        "filepath": str(filepath),
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                )
                success_count += 1
                print(f"  [DALL·E] Saved {filepath}")
            except Exception as exc:
                error_msg = str(exc)[:200]  # Truncate long error messages
                metadata.append(
                    {
                        "product_id": product_id,
                        "model": "dalle3",
                        "prompt_id": prompt.variant_id,
                        "prompt_text": prompt.text,
                        "output_path": None,
                        "run_id": run_id,
                        "run_started_at": run_started_at,
                        "run_finished_at": datetime.now(UTC).isoformat(),
                        "status": "failed",
                        "error": error_msg,
                        "image_index": idx + 1,
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                )
                failed_count += 1
                print(f"  [DALL·E] Error generating {prompt.variant_id} #{idx + 1}: {exc}")

    # Determine model status
    if success_count > 0 and failed_count == 0:
        model_status = {
            "status": "success",
            "reason": None,
            "message": f"Successfully generated {success_count} image(s)",
            "num_images": success_count
        }
    elif success_count > 0:
        model_status = {
            "status": "partial",
            "reason": "some_failed",
            "message": f"Generated {success_count} image(s), {failed_count} failed",
            "num_images": success_count
        }
    else:
        model_status = {
            "status": "failed",
            "reason": "generation_failed",
            "message": f"All {failed_count} image generation attempt(s) failed",
            "num_images": 0
        }

    return metadata, success_count, failed_count, model_status


def generate_sdxl_images(
    product_id: str,
    prompts: List[ImagePrompt],
    run_id: str,
    run_started_at: str,
    images_per_prompt: Optional[int] = None,
    delay_between_requests: float = 8.0,
    max_retries: Optional[int] = None,
) -> Tuple[List[Dict], int, int, Dict]:
    """
    Generate images using SDXL HTTP API (Stability AI compatible).
    
    Args:
        product_id: Product ID
        prompts: List of ImagePrompt objects
        run_id: Unique run identifier
        run_started_at: ISO timestamp when run started
        images_per_prompt: Number of images per prompt variant (defaults to IMAGES_PER_PROMPT_PER_MODEL)
        delay_between_requests: Delay in seconds between API requests (default 8.0)
        max_retries: Maximum number of retries for rate limit errors (defaults to SDXL_MAX_RETRIES)
    
    Returns:
        Tuple of (metadata list, success count, failed count, model_status dict)
    """
    if images_per_prompt is None:
        images_per_prompt = IMAGES_PER_PROMPT_PER_MODEL
    if max_retries is None:
        max_retries = SDXL_MAX_RETRIES
    
    api_key = os.getenv("SDXL_API_KEY")
    if not api_key:
        print("[SDXL] SDXL_API_KEY not set, skipping SDXL generation.")
        model_status = {
            "status": "failed",
            "reason": "api_key_missing",
            "message": "SDXL_API_KEY not set",
            "num_images": 0
        }
        return [], 0, 0, model_status

    # Filter to only SDXL prompts, limit to PROMPTS_PER_PRODUCT
    sdxl_prompts = [p for p in prompts if p.model == "sdxl"][:PROMPTS_PER_PRODUCT]
    if not sdxl_prompts:
        model_status = {
            "status": "skipped",
            "reason": "no_prompts",
            "message": "No SDXL prompts available",
            "num_images": 0
        }
        return [], 0, 0, model_status

    # Do NOT clean up old SDXL images at start - only after successful generation
    # _cleanup_old_images(product_id, SDXL_SUBDIR)  # Removed - will call after success

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    product_dir = BASE_OUTPUT_DIR / product_id / SDXL_SUBDIR
    _ensure_dir(product_dir)

    metadata: List[Dict] = []
    success_count = 0
    failed_count = 0
    rate_limit_failures = 0
    print(f"[SDXL] Generating {images_per_prompt} image(s) per prompt for {product_id} ({len(sdxl_prompts)} prompts) ...")
    print(f"[SDXL] Using {delay_between_requests}s delay between requests, max {max_retries} retries per image")

    for prompt in sdxl_prompts:
        variant_dir = product_dir / prompt.variant_id
        _ensure_dir(variant_dir)

        for idx in range(images_per_prompt):
            filename = f"{prompt.variant_id}_{idx + 1}.png"
            filepath = variant_dir / filename

            payload = {
                "text_prompts": [{"text": prompt.text}],
                "cfg_scale": 7,
                "width": 1024,
                "height": 1024,
                "samples": 1,
                "steps": 30,
            }

            # Retry logic with exponential backoff
            retry_count = 0
            success = False
            
            while retry_count <= max_retries and not success:
                try:
                    # Add delay before request (except first attempt)
                    if retry_count > 0:
                        wait_time = (2 ** retry_count) * delay_between_requests
                        print(f"  [SDXL] Retry {retry_count}/{max_retries} after {wait_time:.1f}s...")
                        time.sleep(wait_time)
                    elif idx > 0 or (prompt != sdxl_prompts[0] and idx == 0):
                        # Add delay between requests (but not before first request)
                        time.sleep(delay_between_requests)

                    resp = requests.post(
                        STABILITY_API_URL,
                        headers=headers,
                        json=payload,
                        timeout=90,
                    )
                    
                    # Handle rate limit errors
                    if resp.status_code == 429:
                        retry_after = int(resp.headers.get("Retry-After", delay_between_requests * (2 ** retry_count)))
                        if retry_count < max_retries:
                            print(f"  [SDXL] Rate limited (429). Waiting {retry_after}s before retry...")
                            time.sleep(retry_after)
                            retry_count += 1
                            continue
                        else:
                            raise requests.exceptions.HTTPError(
                                f"Rate limit exceeded after {max_retries} retries"
                            )
                    
                    resp.raise_for_status()
                    data = resp.json()

                    artifacts = data.get("artifacts", [])
                    if not artifacts:
                        print("  [SDXL] No artifacts returned.")
                        break

                    artifact = artifacts[0]
                    if not artifact.get("base64"):
                        print("  [SDXL] Artifact missing base64 data.")
                        break

                    image_bytes = base64.b64decode(artifact["base64"])
                    with filepath.open("wb") as f:
                        f.write(image_bytes)

                    metadata.append(
                        {
                            "product_id": product_id,
                            "model": "sdxl",
                            "prompt_id": prompt.variant_id,
                            "prompt_text": prompt.text,
                            "output_path": str(filepath.relative_to(BASE_OUTPUT_DIR)),
                            "run_id": run_id,
                            "run_started_at": run_started_at,
                            "run_finished_at": datetime.now(UTC).isoformat(),
                            "status": "success",
                            "image_index": idx + 1,
                            "filepath": str(filepath),
                            "timestamp": datetime.now(UTC).isoformat(),
                        }
                    )
                    success_count += 1
                    print(f"  [SDXL] Saved {filepath}")
                    success = True
                    
                except requests.exceptions.HTTPError as exc:
                    is_rate_limit = exc.response and exc.response.status_code == 429
                    if is_rate_limit:
                        rate_limit_failures += 1
                        if retry_count < max_retries:
                            retry_count += 1
                            continue
                        # Max retries reached for rate limit
                        error_msg = f"Rate limit exceeded after {max_retries} retries"
                        error_type = "rate_limit"
                    else:
                        error_msg = str(exc)[:200]
                        error_type = "http_error"
                    
                    metadata.append(
                        {
                            "product_id": product_id,
                            "model": "sdxl",
                            "prompt_id": prompt.variant_id,
                            "prompt_text": prompt.text,
                            "output_path": None,
                            "run_id": run_id,
                            "run_started_at": run_started_at,
                            "run_finished_at": datetime.now(UTC).isoformat(),
                            "status": "failed",
                            "error": error_type,
                            "error_message": error_msg,
                            "image_index": idx + 1,
                            "timestamp": datetime.now(UTC).isoformat(),
                        }
                    )
                    failed_count += 1
                    if is_rate_limit:
                        print(f"  [SDXL] Rate limit exceeded for {prompt.variant_id} #{idx + 1} after {max_retries} retries")
                    else:
                        print(f"  [SDXL] Error generating {prompt.variant_id} #{idx + 1}: {exc}")
                    break
                except Exception as exc:
                    error_msg = str(exc)[:200]
                    metadata.append(
                        {
                            "product_id": product_id,
                            "model": "sdxl",
                            "prompt_id": prompt.variant_id,
                            "prompt_text": prompt.text,
                            "output_path": None,
                            "run_id": run_id,
                            "run_started_at": run_started_at,
                            "run_finished_at": datetime.now(UTC).isoformat(),
                            "status": "failed",
                            "error": "exception",
                            "error_message": error_msg,
                            "image_index": idx + 1,
                            "timestamp": datetime.now(UTC).isoformat(),
                        }
                    )
                    failed_count += 1
                    print(f"  [SDXL] Error generating {prompt.variant_id} #{idx + 1}: {exc}")
                    break

    # Only cleanup old SDXL images if at least one new image was successfully generated
    if success_count > 0:
        _cleanup_old_images(product_id, SDXL_SUBDIR, only_if_success=True)
        print(f"  [SDXL] Archived old images after {success_count} successful generation(s)")
    else:
        print(f"  [SDXL] No successful images generated - preserving old images")
    
    # Determine model status
    if success_count > 0 and failed_count == 0:
        model_status = {
            "status": "success",
            "reason": None,
            "message": f"Successfully generated {success_count} image(s)",
            "num_images": success_count
        }
    elif success_count > 0:
        model_status = {
            "status": "partial",
            "reason": "some_failed",
            "message": f"Generated {success_count} image(s), {failed_count} failed",
            "num_images": success_count
        }
    elif rate_limit_failures > 0:
        model_status = {
            "status": "failed",
            "reason": "rate_limit",
            "message": f"Rate limit exceeded after {max_retries} retries. {failed_count} image(s) failed.",
            "num_images": 0
        }
        print(f"[SDXL] Giving up for {product_id}: Rate limit exceeded after {max_retries} retries")
    else:
        model_status = {
            "status": "failed",
            "reason": "generation_failed",
            "message": f"All {failed_count} image generation attempt(s) failed",
            "num_images": 0
        }

    return metadata, success_count, failed_count, model_status


def _summarize_manifest(manifest: List[Dict]) -> Dict[str, Dict[str, int]]:
    summary: Dict[str, Dict[str, int]] = {}
    for record in manifest:
        product = record["product_id"]
        model = record["model"]
        summary.setdefault(product, {}).setdefault(model, 0)
        summary[product][model] += 1
    return summary


def _write_reports(manifest: List[Dict]) -> None:
    summary = _summarize_manifest(manifest)
    _ensure_dir(REPORT_DIR)

    # Image generation report
    lines = [
        "# Q3 – Image Generation Report",
        "",
        f"_Generated on {datetime.now(UTC).isoformat()}_",
        "",
        "| Product | DALL·E 3 Images | SDXL Images |",
        "| --- | ---: | ---: |",
    ]
    for product in summary:
        dalle_count = summary[product].get("dalle3", 0)
        sdxl_count = summary[product].get("sdxl", 0)
        lines.append(f"| {product} | {dalle_count} | {sdxl_count} |")

    lines.append("")
    lines.append("Artifacts saved under `images/q3/<product_id>/{dalle3,sdxl}/`.")
    REPORT_IMAGE_GEN.write_text("\n".join(lines), encoding="utf-8")

    # AI vs real placeholder report
    ai_vs_real_lines = [
        "# Q3 – AI vs Real Image Summary",
        "",
        "This document tracks AI-generated assets vs. ground-truth product imagery.",
        "",
        "## Generated Assets",
    ]
    for product in summary:
        dalle_count = summary[product].get("dalle3", 0)
        sdxl_count = summary[product].get("sdxl", 0)
        ai_vs_real_lines.append(
            f"- `{product}` → DALL·E 3: {dalle_count} images, SDXL: {sdxl_count} images"
        )
    ai_vs_real_lines.extend(
        [
            "",
            "## Next Steps",
            "- Compare AI outputs against ground-truth imagery (`report/q3_image_comparison.md`).",
            "- Document qualitative differences and alignment with customer reviews.",
        ]
    )
    REPORT_AI_VS_REAL.write_text("\n".join(ai_vs_real_lines), encoding="utf-8")


def run_q3_for_product(
    product_id: str,
    run_id: Optional[str] = None,
    run_started_at: Optional[str] = None,
) -> Tuple[List[Dict], Path, str, Dict]:
    """
    Run Q3 image generation pipeline for a single product.
    
    Args:
        product_id: Product ID
        run_id: Optional run ID (generates one if not provided)
        run_started_at: Optional run start timestamp (uses current time if not provided)
        
    Returns:
        Tuple of (manifest entries for this run, product manifest path, run_id, result_dict)
        result_dict contains: overall_status, dalle3_status, sdxl_status
    """
    BASE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate run_id if not provided
    if run_id is None:
        run_id = datetime.now(UTC).isoformat()
    if run_started_at is None:
        run_started_at = datetime.now(UTC).isoformat()

    # Build prompts for this product
    print(f"[Q3] Building prompts from Q2 analysis for {product_id}...")
    try:
        prompts_by_product = build_all_prompts()
    except Exception as exc:
        raise RuntimeError(f"Failed to build prompts: {exc}")
    
    if product_id not in prompts_by_product:
        raise ValueError(f"No prompts found for {product_id}")
    
    prompts = prompts_by_product[product_id]
    
    # Save prompts to output directory
    _save_prompts_to_output(product_id, prompts)

    print(f"\n=== Q3 Image Generation: {product_id} (run_id: {run_id}) ===")

    # Generate images
    dalle_meta, dalle_success, dalle_failed, dalle_status = generate_dalle3_images(
        product_id, prompts, run_id, run_started_at
    )
    sdxl_meta, sdxl_success, sdxl_failed, sdxl_status = generate_sdxl_images(
        product_id, prompts, run_id, run_started_at
    )

    run_manifest = dalle_meta + sdxl_meta
    
    # Determine overall status
    if dalle_status["status"] == "success" and sdxl_status["status"] == "success":
        overall_status = "success"
    elif dalle_status["status"] == "success" and sdxl_status["status"] in ["failed", "partial"]:
        overall_status = "partial"
    elif dalle_status["status"] in ["failed", "partial"] and sdxl_status["status"] == "success":
        overall_status = "partial"
    elif dalle_status["status"] == "success":
        overall_status = "partial"  # DALL·E succeeded but SDXL failed
    else:
        overall_status = "failed"
    
    result_dict = {
        "overall_status": overall_status,
        "dalle3_status": dalle_status,
        "sdxl_status": sdxl_status,
    }

    # Load existing manifest or create new
    product_manifest_path = BASE_OUTPUT_DIR / product_id / "manifest.json"
    if product_manifest_path.exists():
        with product_manifest_path.open("r", encoding="utf-8") as f:
            existing_data = json.load(f)
            existing_images = existing_data.get("images", [])
    else:
        existing_images = []
    
    # Append new entries (don't overwrite)
    all_images = existing_images + run_manifest
    
    # Save updated per-product manifest
    _save_json(product_manifest_path, {
        "product_id": product_id,
        "last_updated": datetime.now(UTC).isoformat(),
        "images": all_images
    })
    print(f"[Q3] Per-product manifest updated: {product_manifest_path} ({len(run_manifest)} new entries)")
    print(f"[Q3] Overall status: {overall_status} (DALL·E: {dalle_status['status']}, SDXL: {sdxl_status['status']})")

    return run_manifest, product_manifest_path, run_id, result_dict


def run_q3(
    products: List[str] | None = None,
    images_per_prompt: int = 2,
) -> Tuple[List[Dict], Path]:
    """
    Run Q3 image generation pipeline across all products (legacy function for compatibility).
    
    Args:
        products: List of product IDs (defaults to all from PRODUCTS)
        images_per_prompt: Number of images per prompt variant (ignored, uses IMAGES_PER_PROMPT_PER_MODEL)
        
    Returns:
        Tuple of (manifest list, manifest path)
    """
    BASE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    products = products or [p["id"] for p in PRODUCTS]

    run_id = datetime.now(UTC).isoformat()
    run_started_at = run_id
    all_manifest: List[Dict] = []

    for product_id in products:
        try:
            run_manifest, _, _, _, _ = run_q3_for_product(product_id, run_id, run_started_at)
            all_manifest.extend(run_manifest)
            
            # Add delay between products to avoid rate limits
            if product_id != products[-1]:
                print(f"[Q3] Waiting 10 seconds before next product...")
                time.sleep(10)
        except Exception as exc:
            print(f"[Q3] Error processing {product_id}: {exc}")

    # Save global manifest (for compatibility)
    _save_json(MANIFEST_PATH, {"generated_at": datetime.now(UTC).isoformat(), "images": all_manifest})
    
    _write_reports(all_manifest)
    print(f"\n[Q3] Global manifest written to {MANIFEST_PATH}")
    print(f"[Q3] Reports updated: {REPORT_IMAGE_GEN}, {REPORT_AI_VS_REAL}")
    return all_manifest, MANIFEST_PATH


if __name__ == "__main__":
    run_q3()

