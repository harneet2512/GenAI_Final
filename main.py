"""
Main entry point for the full pipeline.
Can run individual steps or the complete workflow.
"""

import sys
import argparse
from agent_workflow.graph import run_full_workflow


def main():
    parser = argparse.ArgumentParser(description='Run the product image generation pipeline')
    parser.add_argument('--product-id', type=str, help='Product ID to process (e.g., B0CL61F39H)')
    parser.add_argument('--all', action='store_true', help='Process all three products')
    parser.add_argument('--step', type=str, choices=['scrape', 'rag', 'analyze', 'images', 'compare', 'workflow'],
                       help='Run a specific step')
    
    args = parser.parse_args()
    
    # Default products
    products = ["B0CL61F39H", "B0CJZMP7L1", "B0DJ9SVTB6"]
    
    if args.step == 'workflow' or (not args.step and not args.all):
        # Run full workflow
        if args.product_id:
            print(f"Running full workflow for product: {args.product_id}")
            run_full_workflow(args.product_id)
        elif args.all:
            print("Running full workflow for all products...")
            for product_id in products:
                try:
                    run_full_workflow(product_id)
                except Exception as e:
                    print(f"Error processing {product_id}: {e}")
        else:
            print("Running full workflow for first product (B0CL61F39H)...")
            run_full_workflow(products[0])
    
    elif args.step == 'scrape':
        print("Running scraping step...")
        from scrapers.scrape_product import scrape_product
        from scrapers.scrape_reviews import scrape_reviews, preprocess_reviews
        import json
        import os
        
        urls = [
            "https://www.amazon.com/PlayStation%C2%AE5-console-slim-PlayStation-5/dp/B0CL61F39H/ref=sr_1_1?crid=JHI54LL4IB38&dib=eyJ2IjoiMSJ9.iljGzJ9gK4edCvZ4knhV5sEzGLOp35OxhJKXWBnySFW7vKcyeB8JmjRxnm6G4wOQ8S2wptC09n-5BA49qVeMopQkWirqavNnTksuwTsxOWy21S96F9h7-ny8aTboaLdspw-1mizwv8VAXviUOWQNZzMfrEupXa7pLrq6uNT9fP2kSZHzCHwmdcfo-m0SN5f6BEsPYVnlBD2heQ-nxQdlPcKCvCN7SZnHRd7IJq-hWOo.Dn3WgFVCe7q2lXdN5vUtsGVhdVqvpWnDz4Nfc1X2IrM&dib_tag=se&keywords=playstation+5&qid=1763956660&sprefix=playstation+5+%2Caps%2C279&sr=8-1",
            "https://www.amazon.com/STANLEY-Flowstate-3-Position-Compatible-Insulated/dp/B0CJZMP7L1/ref=sr_1_1?crid=LSHECHANWYZL&dib=eyJ2IjoiMSJ9.ffe_6KF4JbPgrGr7B4C9KrXJcpNjt0IIBTQAf34vus5KvIwkouMEPzvAzY7IUtendi97bcXiSoijEnrL-3l0kQF0l5iKTLpYG6Hzvivl-grXaJILOyRsjkUdTm-zMl71cJxtJLDbr_xn5LKxe-qtDhginVwXczYd1K8w6sxVHluEjB9gWUk9T8H_GFtKE2Rc1AH44d1-_ISnCvQrccCkwU5a1MmswKdwlvcfZu8_w-6pYCbKWNDBl32XE_6PFanWFBwKwXF51S0Kc7XJmrH_-4NYsfDIfaPsHpTBS4qhlUE.s2tHK2mowp5sZEeoUe9K2_5R_ubAItI4PE5s-trQfqF&dib_tag=se&keywords=amazon%2Bstanley%2Bcup&qid=1763922923&sprefix=amazon%2Bsta%2Caps%2C112&sr=8-1&th=1",
            "https://www.amazon.com/Jordan-Shoes-553558-092-Black-Medium/dp/B0DJ9SVTB6/ref=sr_1_11?crid=32OREV6IIBCA8&dib=eyJ2IjoiMSJ9.c9IM_GWKqt2P2AWxZIQJ0lXHB8YCj-AOddwnvCxeQTBV0gCVL4hki2D7bJLxGfCSDXcmZKoIXqtwBSAfrm5ed1XJu39pf7F63VwLzmBQp_-9R4dbwfpKnv9DhbQ8YNiLaQ44fo-mr3E90IB2Ml33juTDpdlm0RENcP2GzNEoX57KdX7ahemHlJ1bjNJwMpiSHaKkhN9jzetW1SfYofwJbYgVH_JGJqHjJfvJa22PiwenKKWW9mjE9YJ61lLI0X0h_oHxAhKu_Zk6l2LNIc_cl_xVqpAHWKUVEhwlcxOCQj4.WBcto1R2ouHGlnYZICgBhxrYQ9BRLcquTrgB4QieKlE&dib_tag=se&keywords=jordan%2Bshoes%2Bfor%2Bmen&qid=1763923037&sprefix=jordan%2B%2Caps%2C114&sr=8-11&th=1&psc=1"
        ]
        
        for url in urls:
            try:
                product_data = scrape_product(url)
                product_id = product_data['product_id']
                # Use Selenium for better review collection (handles pagination better)
                raw_reviews = scrape_reviews(url, max_reviews=250, use_selenium=True)
                processed_reviews = preprocess_reviews(raw_reviews, max_reviews=250)
                
                os.makedirs("data/processed", exist_ok=True)
                with open(f"data/processed/{product_id}_reviews_processed.json", 'w', encoding='utf-8') as f:
                    json.dump(processed_reviews, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"Error scraping {url}: {e}")
    
    elif args.step == 'rag':
        print("Running RAG pipeline step...")
        from rag_pipeline.embedder import build_index_for_product
        
        for product_id in products:
            try:
                build_index_for_product(product_id)
            except Exception as e:
                print(f"Error building index for {product_id}: {e}")
    
    elif args.step == 'analyze':
        print("Running analysis step...")
        from analysis.llm_analysis import run_full_analysis
        
        for product_id in products:
            try:
                run_full_analysis(product_id)
            except Exception as e:
                print(f"Error analyzing {product_id}: {e}")
    
    elif args.step == 'images':
        print("Running image generation step...")
        from image_generation.dalle_generator import generate_for_product
        from image_generation.sdxl_generator import generate_for_product as generate_sdxl
        
        for product_id in products:
            try:
                generate_for_product(product_id, images_per_prompt=5)
                generate_sdxl(product_id, images_per_prompt=5)
            except Exception as e:
                print(f"Error generating images for {product_id}: {e}")
    
    elif args.step == 'compare':
        print("Running image comparison step...")
        from image_generation.compare_images import compare_product_images
        
        for product_id in products:
            for model in ["dalle", "sdxl"]:
                try:
                    compare_product_images(product_id, model=model)
                except Exception as e:
                    print(f"Error comparing {product_id} ({model}): {e}")
    
    print("\n[OK] Pipeline step complete")


if __name__ == "__main__":
    main()

