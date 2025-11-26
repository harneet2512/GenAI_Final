"""
CLI entry point for the agentic pipeline.
"""

import argparse
from .state import ProductId
from .workflow import run_agentic_pipeline


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run agentic pipeline for product review → image generation"
    )
    parser.add_argument(
        "--product",
        required=True,
        choices=["ps5", "stanley", "jordans"],
        help="Product ID to process",
    )
    args = parser.parse_args()
    pid: ProductId = args.product  # type: ignore

    print(f"\n{'='*60}")
    print(f"Running agentic pipeline for: {pid}")
    print(f"{'='*60}\n")

    final_state = run_agentic_pipeline(pid)
    
    print("\n" + "="*60)
    print("Pipeline completed!")
    print("="*60)
    print("\nFinal state summary:")
    print(f"  Product ID: {final_state.get('product_id')}")
    print(f"  Corpus built: {final_state.get('corpus_built', False)}")
    print(f"  Index built: {final_state.get('index_built', False)}")
    print(f"  Q2 analysis: {final_state.get('q2_analysis_path', 'N/A')}")
    print(f"  Q2 summary: {final_state.get('q2_summary_path', 'N/A')}")
    print(f"  Q3 manifest: {final_state.get('q3_manifest_path', 'N/A')}")
    print(f"\nTotal logs: {len(final_state.get('logs', []))}")
    print("\nLast 10 log entries:")
    for log in final_state.get("logs", [])[-10:]:
        print(f"  {log}")


if __name__ == "__main__":
    main()

