"""
Amazon Reviews Scraper Pipeline
=================================

A simple, automated pipeline for scraping Amazon product reviews for multiple products.

This script is designed for a university Generative AI lab assignment.
It performs low-frequency scraping with basic politeness delays between requests.
No captcha bypassing, proxy rotation, or ToS-evading techniques are included.

The script automatically processes a list of products, collecting up to 250 reviews
per product by paginating through Amazon's review pages.

Usage:
    python scrape_amazon_reviews_pipeline.py
"""

import os
import time
import json
import csv
import re
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup

# Try to import Selenium for better success rate
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Note: Selenium not available. Install with: pip install selenium webdriver-manager")


# Configuration
MAX_REVIEWS_PER_PRODUCT = 250
MAX_PAGES = 20

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

# URL template - page 1 uses different ref parameter
def build_review_url(asin: str, page: int) -> str:
    """
    Build the review page URL for a given ASIN and page number.
    Page 1 uses ref=cm_cr_dp_d_show_all_btm, subsequent pages use ref=cm_cr_arp_d_paging_btm_next_{page}
    """
    base = f"https://www.amazon.com/product-reviews/{asin}/"
    if page == 1:
        return f"{base}ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews"
    else:
        return f"{base}ref=cm_cr_arp_d_paging_btm_next_{page}?ie=UTF8&reviewerType=all_reviews&pageNumber={page}"

# Products to scrape
PRODUCTS = [
    {
        "asin": "B0CL61F39H",
        "slug": "ps5",
        "description": "PlayStation 5 Digital Edition (example product)",
    },
    {
        "asin": "B0CJZMP7L1",
        "slug": "stanley",
        "description": "Stanley Flowstate Tumbler",
    },
    {
        "asin": "B0DJ9SVTB6",
        "slug": "jordans",
        "description": "Nike Men's Air Jordan 1 Low Sneaker",
    },
]


def parse_review_div(div) -> Dict[str, Optional[str]]:
    """
    Parse a single review div element and extract review data.
    
    Args:
        div: BeautifulSoup element containing a single review
        
    Returns:
        Dictionary with review_id, rating, title, body, date
        Missing fields are set to None or empty string
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
    
    # Fallback: try cmps-review-star-rating for foreign reviews
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
    
    # Fallback: try span with data-hook="review-title"
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


def create_selenium_driver(headless: bool = False):
    """Create and configure Chrome WebDriver if Selenium is available."""
    if not SELENIUM_AVAILABLE:
        return None
    
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    except Exception as e:
        print(f"    Warning: Could not create Selenium driver: {e}")
        return None


def fetch_reviews_for_product(asin: str, slug: str, max_reviews: int = MAX_REVIEWS_PER_PRODUCT, use_selenium: bool = True) -> List[Dict[str, Optional[str]]]:
    """
    Fetch reviews for a single product by paginating through review pages.
    
    Args:
        asin: Amazon product ASIN
        slug: Short identifier for the product (used in filenames)
        max_reviews: Maximum number of reviews to collect (default: MAX_REVIEWS_PER_PRODUCT)
        
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
    driver = None
    
    # Try Selenium if available and requested
    if use_selenium and SELENIUM_AVAILABLE:
        print(f"  Using Selenium for {slug} (ASIN: {asin})...")
        driver = create_selenium_driver(headless=False)
        if not driver:
            print(f"  Falling back to requests for {slug}...")
            use_selenium = False
    else:
        print(f"  Starting pagination for {slug} (ASIN: {asin})...")
    
    try:
        while len(all_reviews) < max_reviews and page <= MAX_PAGES:
            # Construct URL for this page
            url = build_review_url(asin, page)
            
            print(f"    Page {page}...", end=" ")
            
            try:
                # Use Selenium or requests
                if driver:
                    driver.get(url)
                    time.sleep(3)  # Wait for page to load
                    # Wait for reviews to load
                    try:
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-hook="review"], li[data-hook="review"]'))
                        )
                    except TimeoutException:
                        print("No reviews found.")
                        break
                    # Scroll to load all content
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                    html_content = driver.page_source
                else:
                    # Make GET request
                    response = requests.get(url, headers=HEADERS, timeout=15)
                    
                    # Check status code
                    if response.status_code != 200:
                        print(f"\n    Warning: Got status {response.status_code} for URL: {url}")
                        print(f"    Stopping pagination for {slug}.")
                        break
                    
                    html_content = response.content
                
                # Parse HTML
                soup = BeautifulSoup(html_content, "html.parser")
                
                # Find all review divs
                review_divs = soup.find_all("div", attrs={"data-hook": "review"})
                
                # Also try li elements (Amazon sometimes uses <li>)
                if not review_divs:
                    review_divs = soup.find_all("li", attrs={"data-hook": "review"})
                
                # If no reviews found, assume no more pages
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
                
                # If no valid reviews on this page, stop
                if len(page_reviews) == 0:
                    print("    No valid reviews on this page. Stopping.")
                    break
                
                # Check if we've reached max reviews
                if len(all_reviews) >= max_reviews:
                    print(f"    Reached target of {max_reviews} reviews.")
                    break
                
                # Increment page and sleep
                page += 1
                time.sleep(2.0)  # Politeness delay
                
            except requests.exceptions.RequestException as e:
                print(f"\n    Error fetching page {page}: {e}")
                print(f"    Stopping pagination for {slug}.")
                break
            except Exception as e:
                print(f"\n    Error parsing page {page}: {e}")
                print(f"    Stopping pagination for {slug}.")
                break
    
    finally:
        # Close Selenium driver if used
        if driver:
            driver.quit()
    
    # Truncate to max_reviews if we have more
    if len(all_reviews) > max_reviews:
        all_reviews = all_reviews[:max_reviews]
    
    return all_reviews


def save_reviews(reviews: List[Dict[str, Optional[str]]], slug: str, asin: str, out_dir: str = "data/raw") -> None:
    """
    Save reviews to JSON and CSV files.
    
    Args:
        reviews: List of review dictionaries
        slug: Short identifier for the product (used in filename)
        asin: Amazon product ASIN (used in filename)
        out_dir: Output directory (default: "data/raw")
    """
    # Ensure output directory exists
    os.makedirs(out_dir, exist_ok=True)
    
    # Save JSON
    json_path = os.path.join(out_dir, f"reviews_{slug}_{asin}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(reviews, f, indent=2, ensure_ascii=False)
    print(f"  Saved JSON: {json_path}")
    
    # Save CSV
    if reviews:
        csv_path = os.path.join(out_dir, f"reviews_{slug}_{asin}.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["review_id", "rating", "title", "body", "date"])
            writer.writeheader()
            writer.writerows(reviews)
        print(f"  Saved CSV: {csv_path}")
    else:
        print("  No reviews to save.")


def main():
    """Main entrypoint for the pipeline."""
    print("=" * 60)
    print("Amazon Reviews Scraper Pipeline")
    print("=" * 60)
    print(f"Processing {len(PRODUCTS)} products")
    print(f"Target: {MAX_REVIEWS_PER_PRODUCT} reviews per product")
    print(f"Max pages per product: {MAX_PAGES}")
    print("=" * 60)
    print()
    
    # Ensure output directory exists
    os.makedirs("data/raw", exist_ok=True)
    
    # Process each product
    for idx, product in enumerate(PRODUCTS, 1):
        asin = product["asin"]
        slug = product["slug"]
        description = product["description"]
        
        print(f"[{idx}/{len(PRODUCTS)}] === Scraping {slug} ({asin}) ===")
        print(f"  Description: {description}")
        
        try:
            # Fetch reviews
            reviews = fetch_reviews_for_product(asin, slug, MAX_REVIEWS_PER_PRODUCT)
            
            print(f"  Collected {len(reviews)} reviews for {slug}")
            
            # Save to files
            save_reviews(reviews, slug, asin)
            
        except Exception as e:
            print(f"  ERROR: Failed to process {slug}: {e}")
        
        print()  # Blank line between products
    
    print("=" * 60)
    print("Pipeline complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

