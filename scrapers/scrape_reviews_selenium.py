"""
Amazon Reviews Scraper using Selenium
Scrapes customer reviews from Amazon product pages with pagination support.
Uses Selenium to handle JavaScript-rendered content and avoid bot detection.
"""

import json
import csv
import re
import os
import time
from typing import Dict, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from scrapers.scrape_product import extract_product_id
from scrapers.scrape_reviews import _parse_review_container


def create_driver(headless: bool = False):
    """
    Create and configure Chrome WebDriver.
    
    Args:
        headless: Whether to run browser in headless mode
        
    Returns:
        Configured WebDriver instance
    """
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument('--headless')
    
    # Add options to avoid detection
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Set user agent
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Execute script to hide webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    except Exception as e:
        print(f"Error creating Chrome driver: {e}")
        print("Make sure Chrome browser is installed on your system.")
        raise


def scrape_reviews_selenium(url: str, max_reviews: int = 250, output_dir: str = "data/raw", headless: bool = False) -> List[Dict]:
    """
    Scrape reviews from Amazon product page using Selenium.
    
    Args:
        url: Amazon product URL
        max_reviews: Maximum number of reviews to scrape
        output_dir: Directory to save output files
        headless: Whether to run browser in headless mode
        
    Returns:
        List of review dictionaries
    """
    product_id = extract_product_id(url)
    reviews = []
    seen_review_ids = set()
    
    # Extract base URL
    from urllib.parse import urlparse
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    print(f"Scraping reviews for product {product_id} using Selenium...")
    
    driver = None
    try:
        # Create driver
        print("  Initializing Chrome browser...")
        driver = create_driver(headless=headless)
        
        # First, get reviews from product page
        print("  Fetching product page...")
        driver.get(url)
        time.sleep(3)  # Wait for page to load
        
        # Scroll to reviews section
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(2)
        
        # Get page source and parse
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        review_containers = soup.find_all('li', {'data-hook': 'review'})
        
        if review_containers:
            print(f"  Found {len(review_containers)} reviews on product page")
            for container in review_containers:
                if len(reviews) >= max_reviews:
                    break
                review = _parse_review_container(container, len(reviews))
                if review and review.get('body') and len(review.get('body', '')) > 10:
                    review_id = review.get('review_id', '')
                    if review_id and review_id not in seen_review_ids:
                        reviews.append(review)
                        seen_review_ids.add(review_id)
            
            print(f"  Extracted {len(reviews)} reviews from product page")
        
        # Now scrape from dedicated review pages
        if len(reviews) < max_reviews:
            print("  Scraping from review pages...")
            
            page = 1
            consecutive_empty = 0
            
            while len(reviews) < max_reviews and consecutive_empty < 3:
                try:
                    # Construct review page URL
                    if page == 1:
                        review_url = f"{base_url}/product-reviews/{product_id}/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews"
                    else:
                        review_url = f"{base_url}/product-reviews/{product_id}/ref=cm_cr_arp_d_paging_btm_next_{page}?ie=UTF8&reviewerType=all_reviews&pageNumber={page}"
                    
                    print(f"    Fetching review page {page}...")
                    driver.get(review_url)
                    time.sleep(3)  # Wait for page to load
                    
                    # Wait for reviews to load
                    try:
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'li[data-hook="review"]'))
                        )
                    except TimeoutException:
                        print(f"    No reviews found on page {page}")
                        consecutive_empty += 1
                        if consecutive_empty >= 3:
                            print("    No reviews found on last 3 pages. Stopping...")
                            break
                        page += 1
                        continue
                    
                    # Scroll to load all reviews
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    
                    # Parse page
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    review_containers = soup.find_all('li', {'data-hook': 'review'})
                    
                    if not review_containers:
                        consecutive_empty += 1
                        if consecutive_empty >= 3:
                            print("    No reviews found on last 3 pages. Stopping...")
                            break
                        page += 1
                        continue
                    
                    # Extract reviews
                    page_reviews = []
                    for container in review_containers:
                        if len(reviews) >= max_reviews:
                            break
                        
                        review = _parse_review_container(container, len(reviews))
                        if review and review.get('body') and len(review.get('body', '')) > 10:
                            review_id = review.get('review_id', '')
                            if review_id and review_id not in seen_review_ids:
                                page_reviews.append(review)
                                reviews.append(review)
                                seen_review_ids.add(review_id)
                    
                    print(f"    Page {page}: Found {len(page_reviews)} new reviews (Total: {len(reviews)})")
                    
                    if len(page_reviews) == 0:
                        consecutive_empty += 1
                        if consecutive_empty >= 3:
                            print("    No new reviews found on last 3 pages. Stopping...")
                            break
                    else:
                        consecutive_empty = 0
                    
                    page += 1
                    time.sleep(2)  # Be respectful with requests
                    
                except Exception as e:
                    print(f"    Error on page {page}: {e}")
                    consecutive_empty += 1
                    if consecutive_empty >= 3:
                        break
                    page += 1
                    time.sleep(2)
        
    except Exception as e:
        print(f"Error during scraping: {e}")
    finally:
        if driver:
            driver.quit()
            print("  Browser closed")
    
    # Save to JSON
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, f"{product_id}_reviews_raw.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(reviews, f, indent=2, ensure_ascii=False)
    
    # Save to CSV
    csv_path = os.path.join(output_dir, f"{product_id}_reviews_raw.csv")
    if reviews:
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=reviews[0].keys())
            writer.writeheader()
            writer.writerows(reviews)
    
    print(f"[OK] Scraped {len(reviews)} reviews")
    print(f"  Saved to: {json_path} and {csv_path}")
    
    return reviews


if __name__ == "__main__":
    # Test with provided URLs
    products = [
        "https://www.amazon.com/PlayStation%C2%AE5-console-slim-PlayStation-5/dp/B0CL61F39H",
        "https://www.amazon.com/STANLEY-Flowstate-3-Position-Compatible-Insulated/dp/B0CJZMP7L1",
        "https://www.amazon.com/Jordan-Shoes-553558-092-Black-Medium/dp/B0DJ9SVTB6"
    ]
    
    for url in products:
        try:
            reviews = scrape_reviews_selenium(url, max_reviews=250, headless=False)
            print(f"\n[OK] Collected {len(reviews)} reviews for {extract_product_id(url)}\n")
            time.sleep(5)
        except Exception as e:
            print(f"Failed to scrape reviews for {url}: {e}")


