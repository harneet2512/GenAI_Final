"""
Agent nodes wrapping existing Q1-Q3 logic.
All nodes are idempotent - skip if outputs already exist.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any

from .state import PipelineState, ProductId
from agent_app.core.paths import raw_reviews_path
from agent_app.core.reviews_parser import build_reviews_json

# Import existing modules
from rag_pipeline import corpus as corpus_mod
from rag_pipeline.chunker import chunk_corpus
from rag_pipeline.embedder import build_faiss_index
from analysis import llm_analysis
from analysis import q3_image_generation
from analysis import validate_q2_outputs


def _copy_reviews_to_processed(product_id: ProductId, source_path: Path) -> None:
    """
    Copy reviews JSON to data/processed/ so existing corpus builder can find it.
    Tries multiple naming conventions that corpus.py expects.
    """
    from rag_pipeline.corpus import PRODUCTS
    
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Get ASIN from PRODUCTS list
    product_info = next((p for p in PRODUCTS if p["id"] == product_id), None)
    asin = product_info["asin"] if product_info else None
    
    # Try multiple naming conventions that corpus.py looks for
    target_names = [
        f"reviews_{product_id}.json",
        f"reviews_{product_id}_{asin}.json" if asin else None,
    ]
    
    # Also try ASIN-based names
    if asin:
        target_names.extend([
            f"reviews_{asin}.json",
            f"{asin}_reviews_processed.json",
            f"{asin}_reviews_raw.json",
        ])
    
    # Copy to all target names so corpus.py can find it regardless of which one it checks first
    for target_name in target_names:
        if target_name:
            target_path = processed_dir / target_name
            shutil.copy2(source_path, target_path)


def data_preparation_agent(state: PipelineState) -> PipelineState:
    """Parse HTML reviews and create reviews JSON."""
    pid: ProductId = state["product_id"]
    logs = state.get("logs", [])
    input_changed = state.get("input_changed", False)
    logs.append(f"[data_prep] Starting for {pid}")

    out_path = raw_reviews_path(pid)
    
    if input_changed:
        # HTML changed - rebuild reviews JSON
        try:
            out_path = build_reviews_json(pid)
            logs.append(f"[data_prep] HTML changed – rebuilt raw reviews JSON → {out_path}")
        except FileNotFoundError as e:
            logs.append(f"[data_prep] ERROR: {e}")
            state["logs"] = logs
            return state
    else:
        # HTML unchanged - reuse existing if available
        if out_path.exists():
            logs.append(f"[data_prep] HTML unchanged – reusing existing raw reviews JSON at {out_path}")
        else:
            # No existing JSON, need to build it
            try:
                out_path = build_reviews_json(pid)
                logs.append(f"[data_prep] No existing JSON found – built raw reviews JSON → {out_path}")
            except FileNotFoundError as e:
                logs.append(f"[data_prep] ERROR: {e}")
                state["logs"] = logs
                return state

    # Copy to data/processed/ so existing corpus builder can find it
    try:
        _copy_reviews_to_processed(pid, out_path)
        logs.append(f"[data_prep] Copied reviews to data/processed/ for corpus builder")
    except Exception as e:
        logs.append(f"[data_prep] WARNING: Could not copy reviews: {e}")

    state["raw_data_paths"] = {"raw_reviews": str(out_path)}
    state["logs"] = logs
    return state


def corpus_and_index_agent(state: PipelineState) -> PipelineState:
    """Build corpus, chunks, embeddings, and FAISS index."""
    pid: ProductId = state["product_id"]
    logs = state.get("logs", [])
    input_changed = state.get("input_changed", False)

    index_path = Path(f"rag_pipeline/faiss_indexes/{pid}.index")
    
    if input_changed:
        # Input changed - always rebuild
        logs.append(f"[corpus_index] Input changed – rebuilding corpus + index for {pid}")
        try:
            # Build corpus (this will use the reviews we copied to data/processed/)
            corpus = corpus_mod.build_corpus(pid)
            logs.append(f"[corpus_index] Built corpus with {len(corpus)} documents")

            # Build chunks
            chunks = chunk_corpus(pid)
            logs.append(f"[corpus_index] Created {len(chunks)} chunks")

            # Build FAISS index
            build_faiss_index(pid)
            logs.append(f"[corpus_index] Built FAISS index")

            state["corpus_built"] = True
            state["index_built"] = True
            logs.append(f"[corpus_index] Completed corpus + index for {pid}")
        except Exception as e:
            logs.append(f"[corpus_index] ERROR: {e}")
            state["logs"] = logs
            return state
    else:
        # Input unchanged - only rebuild if outputs are missing
        if index_path.exists():
            logs.append(f"[corpus_index] Input unchanged and index exists – skipped (up to date)")
            state["corpus_built"] = True
            state["index_built"] = True
        else:
            # Index missing - need to build
            logs.append(f"[corpus_index] Input unchanged but index missing – building corpus + index for {pid}")
            try:
                corpus = corpus_mod.build_corpus(pid)
                logs.append(f"[corpus_index] Built corpus with {len(corpus)} documents")
                chunks = chunk_corpus(pid)
                logs.append(f"[corpus_index] Created {len(chunks)} chunks")
                build_faiss_index(pid)
                logs.append(f"[corpus_index] Built FAISS index")
                state["corpus_built"] = True
                state["index_built"] = True
            except Exception as e:
                logs.append(f"[corpus_index] ERROR: {e}")
                state["logs"] = logs
                return state

    state["logs"] = logs
    return state


def q2_analysis_agent(state: PipelineState) -> PipelineState:
    """Run Q2 LLM analysis."""
    pid: ProductId = state["product_id"]
    logs = state.get("logs", [])
    input_changed = state.get("input_changed", False)

    analysis_path = Path(f"analysis/{pid}_analysis.json")
    summary_path = Path(f"analysis/{pid}_summary.md")
    
    if input_changed:
        # Input changed - always re-run Q2
        logs.append(f"[q2_analysis] Input changed – running Q2 analysis for {pid}")
        try:
            results = llm_analysis.run_full_analysis(pid)
            state["q2_analysis_path"] = str(analysis_path)
            state["q2_summary_path"] = str(summary_path)
            state["q2_status"] = "success"
            logs.append(f"[q2_analysis] Wrote {analysis_path} and {summary_path}")
        except Exception as e:
            logs.append(f"[q2_analysis] ERROR: {e}")
            state["q2_status"] = "failed"
            state["logs"] = logs
            return state
    else:
        # Input unchanged - check if outputs exist
        if analysis_path.exists() and summary_path.exists():
            logs.append(f"[q2_analysis] Input unchanged and outputs exist – skipped (up to date)")
            state["q2_analysis_path"] = str(analysis_path)
            state["q2_summary_path"] = str(summary_path)
            state["q2_status"] = "skipped"
        else:
            # Outputs missing - need to run
            logs.append(f"[q2_analysis] Input unchanged but outputs missing – running Q2 analysis for {pid}")
            try:
                results = llm_analysis.run_full_analysis(pid)
                state["q2_analysis_path"] = str(analysis_path)
                state["q2_summary_path"] = str(summary_path)
                state["q2_status"] = "success"
                logs.append(f"[q2_analysis] Wrote {analysis_path} and {summary_path}")
            except Exception as e:
                logs.append(f"[q2_analysis] ERROR: {e}")
                state["q2_status"] = "failed"
                state["logs"] = logs
                return state

    state["logs"] = logs
    return state


def q2_validation_agent(state: PipelineState) -> PipelineState:
    """Run Q2 validation."""
    pid: ProductId = state["product_id"]
    logs = state.get("logs", [])

    logs.append(f"[q2_validation] Validating Q2 outputs for {pid}")

    try:
        # The existing validator runs for all products via main()
        # We'll run it and capture output
        result = subprocess.run(
            [sys.executable, "-m", "analysis.validate_q2_outputs"],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        
        validation_report = result.stdout + result.stderr
        state["q2_validation_report"] = validation_report
        
        if result.returncode == 0:
            logs.append("[q2_validation] Validation passed.")
        else:
            logs.append("[q2_validation] Validation found issues (see report).")
    except Exception as e:
        logs.append(f"[q2_validation] ERROR: {e}")
        state["logs"] = logs
        return state

    logs.append("[q2_validation] Validation completed.")
    state["logs"] = logs
    return state


def q3_agent(state: PipelineState) -> PipelineState:
    """Run Q3 image generation."""
    from datetime import datetime, UTC
    
    pid: ProductId = state["product_id"]
    run_id = state.get("run_id", datetime.now(UTC).isoformat())
    run_started_at = run_id
    logs = state.get("logs", [])
    input_changed = state.get("input_changed", False)

    product_manifest_path = Path(f"images/q3/{pid}/manifest.json")
    report_path = Path("report/q3_image_generation.md")
    ai_vs_real_path = Path("report/q3_ai_vs_real.md")
    
    # Check if Q2 succeeded (required for Q3)
    q2_status = state.get("q2_status", "pending")
    if q2_status == "failed":
        logs.append(f"[q3] Q2 analysis failed – skipping Q3 image generation")
        state["q3_status"] = "skipped"
        state["q3_error_reason"] = "Q2 analysis failed - missing visual attributes"
        state["q3_manifest_path"] = str(product_manifest_path) if product_manifest_path.exists() else None
        state["logs"] = logs
        return state
    
    if input_changed:
        # Input changed - always re-run Q3
        logs.append(f"[q3] Input changed – running Q3 image generation for {pid}")
        try:
            run_manifest, manifest_path_result, returned_run_id, result_dict = q3_image_generation.run_q3_for_product(
                pid, run_id, run_started_at
            )
            state["q3_manifest_path"] = str(manifest_path_result)
            
            # Extract status from result_dict
            overall_status = result_dict.get("overall_status", "unknown")
            dalle3_status = result_dict.get("dalle3_status", {})
            sdxl_status = result_dict.get("sdxl_status", {})
            
            state["q3_status"] = overall_status
            state["q3_success_count"] = dalle3_status.get("num_images", 0) + sdxl_status.get("num_images", 0)
            state["q3_failed_count"] = 0  # Failed count is now in model statuses
            
            # Store per-model statuses in state
            state["q3_dalle3_status"] = dalle3_status
            state["q3_sdxl_status"] = sdxl_status
            
            # Set error reason if SDXL failed
            if sdxl_status.get("status") == "failed":
                state["q3_error_reason"] = sdxl_status.get("message", "SDXL generation failed")
            elif overall_status == "failed":
                state["q3_error_reason"] = "All image generation failed"
            elif overall_status == "partial":
                state["q3_error_reason"] = f"DALL·E: {dalle3_status.get('status')}, SDXL: {sdxl_status.get('status')}"
            
            if report_path.exists():
                state["q3_report_path"] = str(report_path)
            if ai_vs_real_path.exists():
                state["q3_ai_vs_real_path"] = str(ai_vs_real_path)
            logs.append(f"[q3] Q3 completed for {pid}: {overall_status} (DALL·E: {dalle3_status.get('num_images', 0)}, SDXL: {sdxl_status.get('num_images', 0)})")
        except Exception as e:
            error_msg = str(e)[:200]
            logs.append(f"[q3] ERROR: {e}")
            state["q3_status"] = "failed"
            state["q3_error_reason"] = error_msg
            state["q3_success_count"] = 0
            state["q3_failed_count"] = 0
            state["logs"] = logs
            return state
    else:
        # Input unchanged - check if outputs exist
        if product_manifest_path.exists():
            logs.append(f"[q3] Input unchanged and manifest exists – skipped (up to date)")
            state["q3_status"] = "skipped"
            state["q3_error_reason"] = "Input unchanged and images already exist"
            state["q3_manifest_path"] = str(product_manifest_path)
            state["q3_success_count"] = 0
            state["q3_failed_count"] = 0
            if report_path.exists():
                state["q3_report_path"] = str(report_path)
            if ai_vs_real_path.exists():
                state["q3_ai_vs_real_path"] = str(ai_vs_real_path)
        else:
            # Manifest missing - need to run
            logs.append(f"[q3] Input unchanged but manifest missing – running Q3 image generation for {pid}")
            try:
                run_manifest, manifest_path_result, returned_run_id, result_dict = q3_image_generation.run_q3_for_product(
                    pid, run_id, run_started_at
                )
                state["q3_manifest_path"] = str(manifest_path_result)
                
                # Extract status from result_dict
                overall_status = result_dict.get("overall_status", "unknown")
                dalle3_status = result_dict.get("dalle3_status", {})
                sdxl_status = result_dict.get("sdxl_status", {})
                
                state["q3_status"] = overall_status
                state["q3_success_count"] = dalle3_status.get("num_images", 0) + sdxl_status.get("num_images", 0)
                state["q3_failed_count"] = 0
                
                # Store per-model statuses in state
                state["q3_dalle3_status"] = dalle3_status
                state["q3_sdxl_status"] = sdxl_status
                
                # Set error reason if SDXL failed
                if sdxl_status.get("status") == "failed":
                    state["q3_error_reason"] = sdxl_status.get("message", "SDXL generation failed")
                elif overall_status == "failed":
                    state["q3_error_reason"] = "All image generation failed"
                elif overall_status == "partial":
                    state["q3_error_reason"] = f"DALL·E: {dalle3_status.get('status')}, SDXL: {sdxl_status.get('status')}"
                
                if report_path.exists():
                    state["q3_report_path"] = str(report_path)
                if ai_vs_real_path.exists():
                    state["q3_ai_vs_real_path"] = str(ai_vs_real_path)
                logs.append(f"[q3] Q3 completed for {pid}: {overall_status} (DALL·E: {dalle3_status.get('num_images', 0)}, SDXL: {sdxl_status.get('num_images', 0)})")
            except Exception as e:
                error_msg = str(e)[:200]
                logs.append(f"[q3] ERROR: {e}")
                state["q3_status"] = "failed"
                state["q3_error_reason"] = error_msg
                state["q3_success_count"] = 0
                state["q3_failed_count"] = 0
                state["logs"] = logs
                return state

    state["logs"] = logs
    return state

