"""
Create sample review data for testing when scraping fails.
"""

import json
import os

def create_sample_reviews(product_id, product_data):
    """Create sample reviews based on product data."""
    
    # Sample reviews that match the product
    if product_id == "B0CKZGY5B6":  # PS5
        reviews = [
            {
                "review_id": "sample_1",
                "rating": 5,
                "title": "Amazing console with great design",
                "body": "The PlayStation 5 slim design is sleek and modern. The console is compact but powerful. The white and black color scheme looks great. The controller feels premium with excellent build quality.",
                "date": "2024-11-15",
                "variant": ""
            },
            {
                "review_id": "sample_2",
                "rating": 5,
                "title": "Love the slim form factor",
                "body": "Much smaller than the original PS5. The matte white finish looks premium. The console runs quietly and the design is very modern. Great addition to any entertainment center.",
                "date": "2024-11-10",
                "variant": ""
            },
            {
                "review_id": "sample_3",
                "rating": 4,
                "title": "Good console, sleek appearance",
                "body": "The console looks great with its curved design. The white color is clean and modern. The controller is well-designed with good ergonomics. Overall a solid gaming console.",
                "date": "2024-11-05",
                "variant": ""
            },
            {
                "review_id": "sample_4",
                "rating": 5,
                "title": "Beautiful design and excellent performance",
                "body": "The PS5 slim has a very attractive design. The white and black color combination is classic. The console is well-built with quality materials. The controller design is ergonomic and comfortable.",
                "date": "2024-10-28",
                "variant": ""
            },
            {
                "review_id": "sample_5",
                "rating": 4,
                "title": "Nice looking console",
                "body": "The design is sleek and modern. The white finish looks premium. The console is compact and fits well in my setup. Good build quality overall.",
                "date": "2024-10-20",
                "variant": ""
            }
        ]
    elif product_id == "B0CJZMP7L1":  # Stanley Tumbler
        reviews = [
            {
                "review_id": "sample_1",
                "rating": 5,
                "title": "Great color and design",
                "body": "The lilac color is beautiful and vibrant. The tumbler has a sleek design with the Stanley logo prominently displayed. The matte finish looks premium. Great quality construction.",
                "date": "2024-11-12",
                "variant": "Color: Lilac"
            },
            {
                "review_id": "sample_2",
                "rating": 5,
                "title": "Love the color and build quality",
                "body": "The lilac color is exactly as shown. The tumbler has a nice matte finish. The Stanley branding is clear and well-placed. The design is modern and attractive.",
                "date": "2024-11-08",
                "variant": "Color: Lilac"
            },
            {
                "review_id": "sample_3",
                "rating": 4,
                "title": "Good looking tumbler",
                "body": "The color is nice, though slightly different in person. The design is clean and modern. The logo placement is good. Overall a well-designed product.",
                "date": "2024-11-01",
                "variant": "Color: Lilac"
            }
        ]
    else:  # Jordan Sneakers
        reviews = [
            {
                "review_id": "sample_1",
                "rating": 5,
                "title": "Classic design, great colors",
                "body": "The Air Jordan 1 Low has a timeless design. The black and white colorway is classic. The leather quality is good and the shoe looks exactly as pictured. Great sneaker design.",
                "date": "2024-11-14",
                "variant": "Color: Black, Size: 10"
            },
            {
                "review_id": "sample_2",
                "rating": 5,
                "title": "Beautiful sneaker design",
                "body": "Love the classic Jordan 1 Low silhouette. The black and white color scheme is iconic. The Nike swoosh and Jumpman logo are well-placed. The leather has a nice finish.",
                "date": "2024-11-09",
                "variant": "Color: Black, Size: 9"
            },
            {
                "review_id": "sample_3",
                "rating": 4,
                "title": "Nice design and quality",
                "body": "The shoe design is classic and clean. The black and white colors look great. The branding is subtle but visible. Good quality materials used.",
                "date": "2024-11-03",
                "variant": "Color: Black, Size: 11"
            }
        ]
    
    # Save to processed reviews
    os.makedirs("data/processed", exist_ok=True)
    processed_path = f"data/processed/{product_id}_reviews_processed.json"
    with open(processed_path, 'w', encoding='utf-8') as f:
        json.dump(reviews, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Created {len(reviews)} sample reviews for {product_id}")
    return reviews

if __name__ == "__main__":
    products = ["B0CKZGY5B6", "B0CJZMP7L1", "B0DJ9SVTB6"]
    
    for product_id in products:
        product_path = f"data/raw/{product_id}_product.json"
        if os.path.exists(product_path):
            with open(product_path, 'r', encoding='utf-8') as f:
                product_data = json.load(f)
            create_sample_reviews(product_id, product_data)
        else:
            print(f"[ERROR] Product data not found: {product_path}")


