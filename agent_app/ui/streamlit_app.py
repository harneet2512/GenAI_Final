"""
Streamlit UI for visualizing agentic pipeline outputs.
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv
import streamlit as st

# Add project root to Python path
project_root = Path(__file__).resolve().parents[2]  # Go up from agent_app/ui/streamlit_app.py
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agent_app.agents.workflow import run_agentic_pipeline
from agent_app.agents.state import ProductId

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="Product Review → Image Agentic Pipeline",
    page_icon="🖼️",
    layout="wide",
)

# Check API keys
openai_key = os.getenv("OPENAI_API_KEY")
sdxl_key = os.getenv("SDXL_API_KEY")

if not openai_key:
    st.error("⚠️ OPENAI_API_KEY not found in environment. Please set it in .env file.")
    st.stop()

if not sdxl_key:
    st.error("⚠️ SDXL_API_KEY not found in environment. Please set it in .env file.")
    st.stop()

# Sidebar
st.sidebar.title("Configuration")

product_label_to_id = {
    "PS5 – PlayStation®5 Digital Edition (Slim)": "ps5",
    "Stanley – STANLEY Quencher H2.0 Tumbler": "stanley",
    "Jordans – Nike Court Vision Mid Next Nature": "jordans",
}

selected_label = st.sidebar.selectbox(
    "Select Product",
    options=list(product_label_to_id.keys()),
    index=0,
)

selected_product_id: ProductId = product_label_to_id[selected_label]  # type: ignore

run_button = st.sidebar.button("🚀 Run Pipeline", type="primary")

# Main content
st.title("Product Review → Image Agentic Pipeline")
st.markdown(f"### Product: `{selected_product_id}`")

# Initialize session state
if "pipeline_state" not in st.session_state:
    st.session_state.pipeline_state = None
if "pipeline_running" not in st.session_state:
    st.session_state.pipeline_running = False
if "last_run_product" not in st.session_state:
    st.session_state.last_run_product = None


# Helper functions (defined before use)
def _render_model_images(
    all_images: List[Dict],
    product_id: str,
    current_run_id: Optional[str],
    model: str,
    model_status: Dict,
    model_display_name: str
) -> None:
    """Render images for a specific model, handling fallback to previous runs if needed."""
    model_images = [img for img in all_images if img.get("model") == model]
    
    if not model_images:
        st.markdown(f"### {model_display_name}")
        st.info(f"No {model_display_name} images available for this product.")
        return
    
    status = model_status.get("status", "unknown") if model_status else "unknown"
    num_images = model_status.get("num_images", 0) if model_status else 0
    reason = model_status.get("reason") if model_status else None
    message = model_status.get("message", "") if model_status else ""
    
    st.markdown(f"### {model_display_name}")
    
    # Get current run images (if run_id exists)
    current_run_images = []
    if current_run_id:
        current_run_images = [
            img for img in model_images
            if img.get("run_id") == current_run_id and img.get("status") == "success"
        ]
    
    # Case 1: Current run succeeded
    if status == "success" and current_run_id and num_images > 0:
        if current_run_images:
            st.success(f"✅ Showing {len(current_run_images)} image(s) from current run")
            _display_images_by_model_variant(current_run_images, product_id)
        else:
            # Fallback if current run images not found
            _display_fallback_for_model(model_images, product_id, current_run_id, model_display_name)
    
    # Case 2: Current run failed or partial with 0 images
    elif status in ["failed", "partial"] and num_images == 0:
        # Show message about why it failed
        if reason == "rate_limit":
            st.warning(f"⚠️ {model_display_name} image generation skipped – using previous images because of rate limits.")
        else:
            st.warning(f"⚠️ {model_display_name} images were not generated in this run because: {message}")
        
        # Fallback to previous successful run
        _display_fallback_for_model(model_images, product_id, current_run_id, model_display_name)
    
    # Case 3: Partial success (some images generated)
    elif status == "partial" and num_images > 0:
        st.info(f"⚠️ Partial success: {message}")
        if current_run_images:
            st.text(f"Showing {len(current_run_images)} successful image(s) from current run:")
            _display_images_by_model_variant(current_run_images, product_id)
    
    # Case 4: Unknown status or empty model_status - try to show current run images if they exist
    else:
        if current_run_images:
            # If we have current run images, show them even if status is unknown
            st.info(f"Showing {len(current_run_images)} image(s) from current run (run_id: {current_run_id[:19] if current_run_id else 'unknown'}...)")
            _display_images_by_model_variant(current_run_images, product_id)
        else:
            # No current run images - fallback to previous
            _display_fallback_for_model(model_images, product_id, current_run_id, model_display_name)


def _display_fallback_for_model(
    model_images: List[Dict],
    product_id: str,
    exclude_run_id: Optional[str],
    model_display_name: str
) -> None:
    """Display images from the most recent previous successful run for a specific model."""
    # Filter to successful images, excluding current run
    successful_images = [
        img for img in model_images
        if img.get("status") == "success" and img.get("run_id") != exclude_run_id
    ]
    
    if not successful_images:
        st.info(f"No previous successful {model_display_name} images found.")
        return
    
    # Find latest run_id by run_finished_at
    run_times = {}
    for img in successful_images:
        run_id = img.get("run_id")
        finished_at = img.get("run_finished_at")
        if run_id and finished_at:
            if run_id not in run_times or finished_at > run_times[run_id]:
                run_times[run_id] = finished_at
    
    if not run_times:
        st.info(f"No previous successful {model_display_name} runs found.")
        return
    
    # Get latest run_id
    latest_run_id = max(run_times.keys(), key=lambda rid: run_times[rid])
    latest_timestamp = run_times[latest_run_id]
    
    # Filter to latest run
    latest_run_images = [
        img for img in successful_images
        if img.get("run_id") == latest_run_id
    ]
    
    if latest_run_images:
        st.info(f"📸 Showing {model_display_name} images from previous successful run at {latest_timestamp[:19]}")
        _display_images_by_model_variant(latest_run_images, product_id)
    else:
        st.info(f"No {model_display_name} images found in latest previous run.")


def _display_images_by_model_variant(images: List[Dict], product_id: str) -> None:
    """Helper to display images grouped by variant (images are already filtered by model)."""
    if not images:
        return
    
    # Get model from first image (all should be same model)
    model = images[0].get("model", "unknown")
    
    # Group by variant
    images_by_variant = {}
    for img in images:
        variant = img.get("prompt_id", "unknown")
        if variant not in images_by_variant:
            images_by_variant[variant] = []
        images_by_variant[variant].append(img)
    
    for variant_id in sorted(images_by_variant.keys()):
        variant_images = images_by_variant[variant_id]
        st.markdown(f"**Variant: {variant_id}**")
        
        # Display images
        cols = st.columns(min(3, len(variant_images)))
        for i, img_data in enumerate(variant_images):
            output_path = img_data.get("output_path")
            filepath = img_data.get("filepath")
            
            # Try multiple path sources
            full_path = None
            if filepath:
                # Use filepath from manifest (handles Windows/Unix paths)
                full_path = Path(filepath)
            elif output_path:
                # Normalize path separators (handle Windows backslashes)
                normalized_path = output_path.replace("\\", "/")
                full_path = Path("images/q3") / normalized_path
            else:
                # Fallback path construction
                full_path = Path("images/q3") / product_id / model / variant_id / f"{variant_id}_{img_data.get('image_index', i+1)}.png"
            
            with cols[i % len(cols)]:
                if full_path and full_path.exists():
                    try:
                        st.image(str(full_path), use_column_width=True, caption=f"{variant_id} #{img_data.get('image_index', i+1)}")
                    except Exception as e:
                        st.error(f"Error loading image: {e}")
                else:
                    # Try alternative path if first attempt failed
                    alt_path = Path("images/q3") / product_id / model / variant_id / f"{variant_id}_{img_data.get('image_index', i+1)}.png"
                    if alt_path.exists():
                        try:
                            st.image(str(alt_path), use_column_width=True, caption=f"{variant_id} #{img_data.get('image_index', i+1)}")
                        except Exception as e:
                            st.error(f"Error loading image: {e}")
                    else:
                        st.warning(f"Image not found: {full_path or alt_path}")


# Run pipeline
if run_button and not st.session_state.pipeline_running:
    st.session_state.pipeline_running = True
    st.session_state.last_run_product = selected_product_id
    
    with st.spinner("Running agentic pipeline... This may take several minutes."):
        try:
            state = run_agentic_pipeline(selected_product_id)
            st.session_state.pipeline_state = state
            st.success("✅ Pipeline completed successfully!")
        except Exception as e:
            st.error(f"❌ Pipeline failed: {e}")
            st.session_state.pipeline_state = None
        finally:
            st.session_state.pipeline_running = False
            st.rerun()

# Display results
state = st.session_state.pipeline_state

if state and st.session_state.last_run_product == selected_product_id:
    # Show pipeline status
    st.markdown("---")
    st.subheader("📊 Run Summary")
    
    run_id = state.get("run_id", "unknown")
    input_changed = state.get("input_changed", False)
    q2_status = state.get("q2_status", "unknown")
    q3_status = state.get("q3_status", "unknown")
    q3_error_reason = state.get("q3_error_reason")
    q3_success_count = state.get("q3_success_count", 0)
    q3_failed_count = state.get("q3_failed_count", 0)
    
    # Run ID
    st.text(f"Run ID: {run_id}")
    
    # Input status
    if input_changed:
        st.info(f"🔄 Input changed: HTML review files were modified. Pipeline re-ran all steps.")
    else:
        st.info(f"✓ Input unchanged: HTML review files are the same. Pipeline skipped up-to-date steps.")
    
    # Q2 Status
    q2_status_emoji = {"success": "✅", "failed": "❌", "skipped": "⏭️"}.get(q2_status, "❓")
    st.text(f"Q2 Analysis: {q2_status_emoji} {q2_status.upper()}")
    
    # Q3 Status
    q3_status_emoji = {"success": "✅", "partial": "⚠️", "failed": "❌", "skipped": "⏭️"}.get(q3_status, "❓")
    q3_status_text = f"Q3 Image Generation: {q3_status_emoji} {q3_status.upper()}"
    if q3_status in ["success", "partial"]:
        q3_status_text += f" ({q3_success_count} success"
        if q3_failed_count > 0:
            q3_status_text += f", {q3_failed_count} failed"
        q3_status_text += ")"
    if q3_error_reason:
        q3_status_text += f" - {q3_error_reason}"
    st.text(q3_status_text)
    
    # Show timestamp if available
    from agent_app.core.fingerprint import load_input_state
    input_state = load_input_state(selected_product_id)
    if input_state and "last_run_at" in input_state:
        st.caption(f"Last run: {input_state['last_run_at']}")
    
    # Execution logs
    with st.expander("📋 Execution Logs", expanded=True):
        logs = state.get("logs", [])
        if logs:
            for line in logs:
                st.text(line)
        else:
            st.text("No logs available.")

    # Q2 Summary
    q2_summary_path = state.get("q2_summary_path")
    if q2_summary_path and Path(q2_summary_path).exists():
        st.subheader("📊 Q2 – Text & Visual Analysis Summary")
        try:
            summary_text = Path(q2_summary_path).read_text(encoding="utf-8")
            st.markdown(summary_text)
        except Exception as e:
            st.error(f"Error reading summary: {e}")

    # Q3 Images - Read from manifest, filter by run_id, handle per-model status
    st.subheader("🖼️ Q3 – AI Generated Product Images")
    product_manifest_path = Path("images/q3") / selected_product_id / "manifest.json"
    
    current_run_id = state.get("run_id")
    q3_status = state.get("q3_status", "unknown")
    dalle3_status = state.get("q3_dalle3_status", {}) or {}
    sdxl_status = state.get("q3_sdxl_status", {}) or {}
    
    if product_manifest_path.exists():
        try:
            with product_manifest_path.open("r", encoding="utf-8") as f:
                manifest_data = json.load(f)
            
            all_images = manifest_data.get("images", [])
            
            # Filter to only images for the selected product (safety check)
            all_images = [img for img in all_images if img.get("product_id") == selected_product_id]
            
            # If model_status is empty but we have images in manifest, infer status from manifest
            if not dalle3_status and current_run_id:
                dalle_images_in_run = [img for img in all_images 
                                      if img.get("model") == "dalle3" 
                                      and img.get("run_id") == current_run_id 
                                      and img.get("status") == "success"]
                if dalle_images_in_run:
                    dalle3_status = {
                        "status": "success",
                        "num_images": len(dalle_images_in_run),
                        "message": f"Found {len(dalle_images_in_run)} image(s) in manifest"
                    }
            
            if not sdxl_status and current_run_id:
                sdxl_images_in_run = [img for img in all_images 
                                     if img.get("model") == "sdxl" 
                                     and img.get("run_id") == current_run_id 
                                     and img.get("status") == "success"]
                if sdxl_images_in_run:
                    sdxl_status = {
                        "status": "success",
                        "num_images": len(sdxl_images_in_run),
                        "message": f"Found {len(sdxl_images_in_run)} image(s) in manifest"
                    }
            
            # Render DALL·E images
            _render_model_images(
                all_images, selected_product_id, current_run_id,
                "dalle3", dalle3_status, "DALL·E 3"
            )
            
            # Render SDXL images with fallback logic
            _render_model_images(
                all_images, selected_product_id, current_run_id,
                "sdxl", sdxl_status, "SDXL"
            )
                    
        except Exception as e:
            st.error(f"Error reading manifest: {e}")
            import traceback
            st.code(traceback.format_exc())
    else:
        if q3_status == "failed":
            st.error(f"❌ Q3 failed: {state.get('q3_error_reason', 'Unknown error')}")
        else:
            st.warning(f"⚠️ No Q3 images generated yet for this product. Run the pipeline first.")
            st.info(f"Expected manifest at: {product_manifest_path}")

    # AI vs Real comparison - Note: This is a global report covering all products
    ai_vs_real_path = state.get("q3_ai_vs_real_path")
    if ai_vs_real_path and Path(ai_vs_real_path).exists():
        st.subheader("🔍 Q3 – AI vs Real Product Images")
        try:
            comparison_text = Path(ai_vs_real_path).read_text(encoding="utf-8")
            # Note: This report covers all products, not just the selected one
            # Filter to show only relevant section if possible
            if selected_product_id in comparison_text.lower():
                # Try to extract product-specific section
                lines = comparison_text.split('\n')
                product_section = []
                in_section = False
                for line in lines:
                    if selected_product_id in line.lower():
                        in_section = True
                    if in_section:
                        product_section.append(line)
                        # Stop at next product or end
                        if line.startswith('- `') and selected_product_id not in line.lower() and product_section:
                            break
                if product_section:
                    st.markdown('\n'.join(product_section))
                else:
                    st.markdown(comparison_text)
                    st.caption("_Note: This is a global report covering all products_")
            else:
                st.markdown(comparison_text)
                st.caption("_Note: This is a global report covering all products_")
        except Exception as e:
            st.error(f"Error reading comparison: {e}")

    # Real product images (optional)
    real_images_dir = Path("images/real") / selected_product_id
    if real_images_dir.exists():
        st.subheader("📷 Real Product Images")
        real_imgs = sorted(real_images_dir.glob("*.png"))
        if real_imgs:
            cols = st.columns(min(3, len(real_imgs)))
            for i, img_path in enumerate(real_imgs):
                with cols[i % len(cols)]:
                    try:
                        st.image(str(img_path), use_column_width=True, caption=img_path.name)
                    except Exception as e:
                        st.error(f"Error loading {img_path.name}: {e}")
        else:
            st.info("No real product images found.")

else:
    st.info("👈 Click 'Run Pipeline' in the sidebar to start the agentic workflow.")

