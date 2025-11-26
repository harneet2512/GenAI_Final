"""
Amazon Reviews Scraper
======================

A simple, reusable script for scraping Amazon product reviews by ASIN.

This script is designed for a university Generative AI lab project.
It performs low-frequency scraping with basic politeness delays.
No captcha bypassing, proxy rotation, or ToS-evading techniques are included.

Usage:
    python scrape_amazon_reviews.py <ASIN> [max_reviews]

Example:
    python scrape_amazon_reviews.py B0CL61F39H 250
"""

import sys
import json
import csv
import os
import time
import re
from typing import List, Dict, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


# Base URL template - try multiple patterns as Amazon may require different formats
def build_review_url(asin: str, page: int, pattern: int = 0) -> str:
    """
    Build the review page URL for a given ASIN and page number.
    Tries multiple URL patterns as Amazon may require different formats.
    
    Args:
        asin: Amazon product ASIN
        page: Page number (1-indexed)
        pattern: URL pattern to use (0=with ref, 1=simple)
        
    Returns:
        Complete URL for the review page
    """
    base = f"https://www.amazon.com/product-reviews/{asin}/"
    
    if pattern == 0:
        # Pattern with ref parameters (as provided by user)
        if page == 1:
            return f"{base}ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews"
        else:
            return f"{base}ref=cm_cr_arp_d_paging_btm_next_{page}?ie=UTF8&reviewerType=all_reviews&pageNumber={page}"
    else:
        # Simple pattern (fallback)
        return f"{base}?ie=UTF8&reviewerType=all_reviews&pageNumber={page}"


def parse_review_div(div) -> Dict[str, Optional[str]]:
    """
    Parse a single review div element and extract review data.
    
    Args:
        div: BeautifulSoup element containing a single review
        
    Returns:
        Dictionary with review_id, rating, title, body, date
    """
    review = {
        "review_id": None,
        "rating": None,
        "title": None,
        "body": None,
        "date": None
    }
    
    # Extract review_id from div id attribute
    review_id = div.get("id", "")
    if review_id:
        review["review_id"] = review_id.strip()
    
    # Extract rating from i[data-hook="review-star-rating"] span
    rating_elem = div.find("i", attrs={"data-hook": "review-star-rating"})
    if rating_elem:
        alt_span = rating_elem.find("span", class_=re.compile("a-icon-alt"))
        if alt_span:
            rating_text = alt_span.get_text(strip=True)
            # Extract number from "5.0 out of 5 stars"
            rating_match = re.search(r"(\d+)\.?\d*", rating_text)
            if rating_match:
                review["rating"] = rating_match.group(1).strip()
    
    # Alternative: try cmps-review-star-rating for foreign reviews
    if not review["rating"]:
        rating_elem = div.find("i", attrs={"data-hook": "cmps-review-star-rating"})
        if rating_elem:
            alt_span = rating_elem.find("span", class_=re.compile("a-icon-alt"))
            if alt_span:
                rating_text = alt_span.get_text(strip=True)
                rating_match = re.search(r"(\d+)\.?\d*", rating_text)
                if rating_match:
                    review["rating"] = rating_match.group(1).strip()
    
    # Extract title from a[data-hook="review-title"] span
    title_elem = div.find("a", attrs={"data-hook": "review-title"})
    if title_elem:
        # Title might be in a span inside the link
        title_span = title_elem.find("span")
        if title_span:
            review["title"] = title_span.get_text(strip=True)
        else:
            # Get all text and clean it
            title_text = title_elem.get_text(strip=True)
            # Remove rating text if present
            title_text = re.sub(r"\d+\.\d+\s+out\s+of\s+5\s+stars", "", title_text, flags=re.IGNORECASE).strip()
            review["title"] = title_text
    
    # Alternative: try span with data-hook="review-title"
    if not review["title"]:
        title_elem = div.find("span", attrs={"data-hook": "review-title"})
        if title_elem:
            review["title"] = title_elem.get_text(strip=True)
    
    # Extract body from span[data-hook="review-body"]
    body_elem = div.find("span", attrs={"data-hook": "review-body"})
    if body_elem:
        # The review text might be in a collapsed expander
        collapsed_elem = body_elem.find("div", attrs={"data-hook": "review-collapsed"})
        if collapsed_elem:
            review["body"] = collapsed_elem.get_text(strip=True)
        else:
            # Remove script tags and expander controls
            for script in body_elem.find_all("script"):
                script.decompose()
            for expander in body_elem.find_all(["a", "div"], attrs={"data-hook": re.compile("expand|collapse")}):
                expander.decompose()
            review["body"] = body_elem.get_text(strip=True)
    
    # Extract date from span[data-hook="review-date"]
    date_elem = div.find("span", attrs={"data-hook": "review-date"})
    if date_elem:
        review["date"] = date_elem.get_text(strip=True)
    
    return review


def fetch_reviews(asin: str, max_reviews: int = 250) -> List[Dict[str, Optional[str]]]:
    """
    Fetch up to max_reviews reviews for the given ASIN from Amazon's
    product reviews pages by paginating pageNumber.
    
    Args:
        asin: Amazon product ASIN (e.g., "B0CL61F39H")
        max_reviews: Maximum number of reviews to fetch (default: 250)
        
    Returns:
        List of review dictionaries, each containing:
        - review_id: str or None
        - rating: str or None
        - title: str or None
        - body: str or None
        - date: str or None
    """
    all_reviews: List[Dict[str, Optional[str]]] = []
    page = 1
    url_pattern = 0  # Start with ref-based pattern
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    print(f"Fetching reviews for ASIN: {asin}")
    print(f"Target: {max_reviews} reviews")
    print("\nNote: If you get 404 errors, Amazon may be blocking automated requests.")
    print("      You may need to use Selenium (see scrape_reviews_selenium.py) or")
    print("      ensure you have proper session cookies.\n")
    
    while len(all_reviews) < max_reviews:
        # Build URL for this page
        url = build_review_url(asin, page, url_pattern)
        
        print(f"  Fetching page {page}...", end=" ")
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                # Try fallback pattern if first attempt fails
                if url_pattern == 0 and page == 1:
                    print(f"\n  Got status {response.status_code}, trying simple URL pattern...")
                    url_pattern = 1
                    url = build_review_url(asin, page, url_pattern)
                    response = requests.get(url, headers=headers, timeout=30)
                
                if response.status_code != 200:
                    print(f"\n  Warning: Got status {response.status_code} for URL: {url}")
                    print("  Stopping pagination.")
                    break
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Find all review divs
            review_divs = soup.find_all("div", attrs={"data-hook": "review"})
            
            # Also try li elements (Amazon sometimes uses <li>)
            if not review_divs:
                review_divs = soup.find_all("li", attrs={"data-hook": "review"})
            
            if not review_divs:
                print("No reviews found.")
                break
            
            # Parse each review
            page_reviews = []
            for div in review_divs:
                if len(all_reviews) >= max_reviews:
                    break
                
                review = parse_review_div(div)
                # Only add if we have at least a body
                if review.get("body") and len(review["body"]) > 10:
                    page_reviews.append(review)
                    all_reviews.append(review)
            
            print(f"Found {len(page_reviews)} reviews (Total: {len(all_reviews)})")
            
            if len(page_reviews) == 0:
                print("  No valid reviews on this page. Stopping.")
                break
            
            page += 1
            time.sleep(1.5)  # Politeness delay between requests
            
        except requests.exceptions.RequestException as e:
            print(f"\n  Error fetching page {page}: {e}")
            print("  Stopping pagination.")
            break
        except Exception as e:
            print(f"\n  Error parsing page {page}: {e}")
            print("  Stopping pagination.")
            break
    
    # Truncate to max_reviews if we have more
    if len(all_reviews) > max_reviews:
        all_reviews = all_reviews[:max_reviews]
    
    print(f"\n[OK] Collected {len(all_reviews)} reviews for ASIN {asin}")
    
    return all_reviews


def save_reviews(asin: str, reviews: List[Dict[str, Optional[str]]], output_dir: str = "data/raw"):
    """
    Save reviews to JSON and CSV files.
    
    Args:
        asin: Amazon product ASIN
        reviews: List of review dictionaries
        output_dir: Directory to save files (default: "data/raw")
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Save JSON
    json_path = os.path.join(output_dir, f"reviews_{asin}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(reviews, f, indent=2, ensure_ascii=False)
    print(f"  Saved JSON: {json_path}")
    
    # Save CSV
    if reviews:
        csv_path = os.path.join(output_dir, f"reviews_{asin}.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["review_id", "rating", "title", "body", "date"])
            writer.writeheader()
            writer.writerows(reviews)
        print(f"  Saved CSV: {csv_path}")


def main():
    """CLI entrypoint for the scraper."""
    if len(sys.argv) < 2:
        print("Usage: python scrape_amazon_reviews.py <ASIN> [max_reviews]")
        print("Example: python scrape_amazon_reviews.py B0CL61F39H 250")
        sys.exit(1)
    
    asin = sys.argv[1].strip()
    
    # Parse max_reviews (optional, default 250)
    max_reviews = 250
    if len(sys.argv) >= 3:
        try:
            max_reviews = int(sys.argv[2])
        except ValueError:
            print(f"Warning: Invalid max_reviews value '{sys.argv[2]}', using default 250")
            max_reviews = 250
    
    # Fetch reviews
    reviews = fetch_reviews(asin, max_reviews)
    
    # Save to files
    if reviews:
        save_reviews(asin, reviews)
    else:
        print("No reviews collected. Nothing to save.")


if __name__ == "__main__":
    main()

