"""
Parse Saved Amazon Reviews
==========================

Utility script for a university Generative AI lab project.
Parses locally saved Amazon review HTML pages (no network access) to extract
structured review data. The script aggregates up to 250 reviews per product and
exports JSON/CSV files per product slug.

No captcha bypassing, proxy rotation, or ToS-evading logic is included.
"""

import csv
import json
import os
from typing import Dict, List, Optional

from bs4 import BeautifulSoup

MAX_REVIEWS_PER_PRODUCT = 250

PRODUCTS = [
    {
        "slug": "ps5",
        "asin": "B0CL61F39H",
        "keywords": ["ps5", "playstation 5"],
    },
    {
        "slug": "stanley",
        "asin": "B0CJZMP7L1",
        "keywords": ["stanley", "quencher", "tumbler"],
    },
    {
        "slug": "jordans",
        "asin": "B0DJ9SVTB6",
        "keywords": ["jordans", "jordan", "nike men", "court vision"],
    },
]


def detect_slug_from_filename(filename: str, products: List[Dict[str, str]]) -> Optional[str]:
    """
    Detect product slug based on filename substring match.

    Args:
        filename: HTML filename
        products: List of product definitions with "slug"

    Returns:
        Matching slug or None if not found
    """
    lower_name = filename.lower()
    for product in products:
        keywords = product.get("keywords", [product["slug"]])
        for keyword in keywords:
            if keyword.lower() in lower_name:
                return product["slug"]
        if product["slug"].lower() in lower_name:
            return product["slug"]
    return None


def clean_text(value: Optional[str]) -> Optional[str]:
    """Strip whitespace from text values."""
    if value is None:
        return None
    text = value.strip()
    return text if text else None


def parse_review_div(div) -> Dict[str, Optional[str]]:
    """
    Parse a single review div and extract key fields.

    Args:
        div: BeautifulSoup element representing one review

    Returns:
        Dict with review_id, rating, title, body, date
    """
    review: Dict[str, Optional[str]] = {
        "review_id": None,
        "rating": None,
        "title": None,
        "body": None,
        "date": None,
    }

    # Review ID
    review_id = div.get("id", "")
    review["review_id"] = clean_text(review_id)

    # Rating
    rating_elem = div.find("i", attrs={"data-hook": "review-star-rating"})
    if rating_elem:
        rating_span = rating_elem.find("span")
        if rating_span:
            review["rating"] = clean_text(rating_span.get_text())
    if not review["rating"]:
        rating_elem = div.find("i", attrs={"data-hook": "cmps-review-star-rating"})
        if rating_elem:
            rating_span = rating_elem.find("span")
            if rating_span:
                review["rating"] = clean_text(rating_span.get_text())

    # Title
    title_elem = div.find("a", attrs={"data-hook": "review-title"})
    if title_elem:
        title_span = title_elem.find("span")
        if title_span:
            review["title"] = clean_text(title_span.get_text())
        elif title_elem.get_text():
            review["title"] = clean_text(title_elem.get_text())

    # Body
    body_elem = div.find("span", attrs={"data-hook": "review-body"})
    if body_elem:
        body_span = body_elem.find("span")
        if body_span:
            review["body"] = clean_text(body_span.get_text())
        elif body_elem.get_text():
            review["body"] = clean_text(body_elem.get_text())

    # Date
    date_elem = div.find("span", attrs={"data-hook": "review-date"})
    if date_elem:
        review["date"] = clean_text(date_elem.get_text())

    return review


def parse_html_file(path: str, slug: str, asin: str) -> List[Dict[str, Optional[str]]]:
    """
    Parse a single HTML file and extract all reviews.

    Args:
        path: Path to HTML file
        slug: Product slug
        asin: Product ASIN

    Returns:
        List of review dictionaries
    """
    reviews: List[Dict[str, Optional[str]]] = []
    print(f"  Parsing {os.path.basename(path)}...")

    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    review_nodes = soup.find_all("div", attrs={"data-hook": "review"})
    if not review_nodes:
        review_nodes = soup.find_all("li", attrs={"data-hook": "review"})

    print(f"    Found {len(review_nodes)} review blocks")

    for div in review_nodes:
        review = parse_review_div(div)
        review["product_slug"] = slug
        review["asin"] = asin
        reviews.append(review)

    return reviews


def collect_all_reviews(html_dir: str = "data/raw") -> Dict[str, List[Dict[str, Optional[str]]]]:
    """
    Parse all HTML files under html_dir and group reviews by product slug.

    Args:
        html_dir: Directory containing saved HTML files

    Returns:
        Dict mapping slug to list of reviews
    """
    reviews_by_slug: Dict[str, List[Dict[str, Optional[str]]]] = {p["slug"]: [] for p in PRODUCTS}

    if not os.path.isdir(html_dir):
        print(f"HTML directory not found: {html_dir}")
        return reviews_by_slug

    html_files = [f for f in os.listdir(html_dir) if f.lower().endswith(".html")]
    html_files.sort()

    print(f"Found {len(html_files)} HTML files in {html_dir}")

    for filename in html_files:
        slug = detect_slug_from_filename(filename, PRODUCTS)
        if not slug:
            print(f"  Skipping {filename} (no matching slug)")
            continue

        product = next((p for p in PRODUCTS if p["slug"] == slug), None)
        if not product:
            continue

        path = os.path.join(html_dir, filename)
        product_reviews = parse_html_file(path, slug, product["asin"])

        reviews_by_slug[slug].extend(product_reviews)
        print(f"    Total for {slug}: {len(reviews_by_slug[slug])}")

    # Truncate to MAX_REVIEWS_PER_PRODUCT
    for slug, review_list in reviews_by_slug.items():
        if len(review_list) > MAX_REVIEWS_PER_PRODUCT:
            reviews_by_slug[slug] = review_list[:MAX_REVIEWS_PER_PRODUCT]
            print(f"    Truncated {slug} to {MAX_REVIEWS_PER_PRODUCT} reviews")

    return reviews_by_slug


def save_reviews(
    reviews: List[Dict[str, Optional[str]]],
    slug: str,
    asin: str,
    out_dir: str = "data/processed",
) -> None:
    """
    Save reviews to JSON and CSV formats.

    Args:
        reviews: List of review dicts
        slug: Product slug
        asin: Product ASIN
        out_dir: Output directory
    """
    os.makedirs(out_dir, exist_ok=True)

    json_path = os.path.join(out_dir, f"reviews_{slug}_{asin}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)
    print(f"  Saved JSON: {json_path}")

    csv_path = os.path.join(out_dir, f"reviews_{slug}_{asin}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "product_slug",
                "asin",
                "review_id",
                "rating",
                "title",
                "body",
                "date",
            ],
        )
        writer.writeheader()
        writer.writerows(reviews)
    print(f"  Saved CSV: {csv_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Parse cached Amazon review HTML pages.")
    parser.add_argument(
        "--html-dir",
        default="data/raw",
        help="Directory containing saved Amazon review HTML files (default: data/raw)",
    )
    parser.add_argument(
        "--output-dir",
        default="data/processed",
        help="Directory to write JSON/CSV outputs (default: data/processed)",
    )
    args = parser.parse_args()

    reviews_by_slug = collect_all_reviews(args.html_dir)

    for product in PRODUCTS:
        slug = product["slug"]
        asin = product["asin"]
        product_reviews = reviews_by_slug.get(slug, [])
        print(f"{slug}: {len(product_reviews)} reviews collected")
        save_reviews(product_reviews, slug, asin, out_dir=args.output_dir)

