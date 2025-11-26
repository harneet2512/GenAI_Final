"""
Amazon Reviews Scraper
Scrapes customer reviews from Amazon product pages with pagination support.
"""

import json
import csv
import re
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, urlencode
from typing import Dict, List, Optional
import time
from datetime import datetime
from scrapers.scrape_product import extract_product_id


def _parse_review_container(container, review_index: int) -> Optional[Dict]:
    """
    Parse a single review container element and extract review data.
    
    Args:
        container: BeautifulSoup element containing review data
        review_index: Index for generating fallback review ID
        
    Returns:
        Dictionary with review data or None if parsing fails
    """
    try:
        # Extract review ID
        review_id = container.get('id', '')
        if not review_id:
            review_id = container.get('data-review-id', '')
        if not review_id:
            review_id = f"review_{review_index}"
        
        # Extract rating - try multiple patterns
        rating = None
        # Pattern 1: review-star-rating (standard reviews)
        rating_elem = container.find('i', {'data-hook': 'review-star-rating'})
        if not rating_elem:
            # Pattern 2: cmps-review-star-rating (foreign reviews)
            rating_elem = container.find('i', {'data-hook': 'cmps-review-star-rating'})
        
        if rating_elem:
            # Get rating from a-icon-alt span inside the i element
            alt_span = rating_elem.find('span', class_=re.compile('a-icon-alt'))
            if alt_span:
                rating_text = alt_span.get_text()
                rating_match = re.search(r'(\d+)\.?\d*', rating_text)
                if rating_match:
                    rating = int(float(rating_match.group(1)))
        
        # Alternative: try to extract from class name (e.g., a-star-5)
        if not rating:
            rating_elem = container.find('i', class_=re.compile('a-star-'))
            if rating_elem:
                class_attr = rating_elem.get('class', [])
                for cls in class_attr:
                    star_match = re.search(r'a-star-(\d+)', cls)
                    if star_match:
                        rating = int(star_match.group(1))
                        break
        
        # Extract review title
        title = ""
        title_elem = container.find('a', {'data-hook': 'review-title'})
        if title_elem:
            # The title is usually in a span that's NOT part of the rating icon
            # Find all spans and exclude those inside the rating icon
            rating_icon = title_elem.find('i', {'data-hook': re.compile('review-star-rating|cmps-review-star-rating')})
            if rating_icon:
                # Get all text, then remove the rating icon's text
                rating_text = rating_icon.get_text(strip=True)
                all_text = title_elem.get_text(strip=True)
                # Remove rating text and clean up
                title = all_text.replace(rating_text, '').strip()
                # Remove any remaining rating patterns
                title = re.sub(r'\d+\.\d+\s+out\s+of\s+5\s+stars', '', title, flags=re.IGNORECASE).strip()
                # Remove separators and extra spaces
                title = re.sub(r'^\s*[|\-\s]+\s*', '', title).strip()
                title = ' '.join(title.split())  # Normalize whitespace
            else:
                # No rating icon, just get the text
                title = title_elem.get_text(strip=True)
        else:
            # Alternative: try span with data-hook="review-title"
            title_elem = container.find('span', {'data-hook': 'review-title'})
            if title_elem:
                title = title_elem.get_text(strip=True)
        
        # Extract review body
        body = ""
        body_elem = container.find('span', {'data-hook': 'review-body'})
        if body_elem:
            # The review text might be in a collapsed expander
            collapsed_elem = body_elem.find('div', {'data-hook': 'review-collapsed'})
            if collapsed_elem:
                # Get text from the collapsed content
                body = collapsed_elem.get_text(strip=True)
            else:
                # Try to get all text from the review-body span, excluding expander controls
                # Remove script tags and expander controls
                for script in body_elem.find_all('script'):
                    script.decompose()
                for expander in body_elem.find_all(['a', 'div'], {'data-hook': re.compile('expand|collapse')}):
                    expander.decompose()
                body = body_elem.get_text(strip=True)
            
            # Clean up the body text
            if body:
                # Remove extra whitespace
                body = ' '.join(body.split())
        
        # Extract date
        date = ""
        date_elem = container.find('span', {'data-hook': 'review-date'})
        if date_elem:
            date = date_elem.get_text(strip=True)
        
        # Extract variant (color/size) - Amazon uses format-strip-linkless span
        variant = ""
        variant_elem = container.find('span', {'data-hook': 'format-strip-linkless'})
        if variant_elem:
            variant = variant_elem.get_text(strip=True)
        else:
            # Fallback to format-strip link
            variant_elem = container.find('a', {'data-hook': 'format-strip'})
            if variant_elem:
                variant = variant_elem.get_text(strip=True)
        
        return {
            "review_id": review_id,
            "rating": rating,
            "title": title,
            "body": body,
            "date": date,
            "variant": variant
        }
    except Exception as e:
        return None


def scrape_reviews(url: str, max_reviews: int = 250, output_dir: str = "data/raw", use_selenium: bool = False) -> List[Dict]:
    """
    Scrape reviews from Amazon product page with pagination.
    
    Args:
        url: Amazon product URL
        max_reviews: Maximum number of reviews to scrape
        output_dir: Directory to save output files
        use_selenium: If True, use Selenium for scraping (handles JS-rendered content)
        
    Returns:
        List of review dictionaries
    """
    # Use Selenium if requested
    if use_selenium:
        try:
            from scrapers.scrape_reviews_selenium import scrape_reviews_selenium
            return scrape_reviews_selenium(url, max_reviews, output_dir, headless=False)
        except ImportError:
            print("Warning: Selenium not available, falling back to requests-based scraping")
        except Exception as e:
            print(f"Warning: Selenium scraping failed: {e}, falling back to requests-based scraping")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    }
    
    product_id = extract_product_id(url)
    reviews = []
    page = 1
    
    # Extract base URL (just the domain)
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    # Try to find "See all reviews" link on product page
    review_url_template = None
    try:
        print("  Fetching product page to find review links...")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # First, try scraping from the product page itself (reviews are embedded)
        review_containers = soup.find_all('li', {'data-hook': 'review'})
        
        if review_containers:
            print(f"  Found {len(review_containers)} reviews on product page")
            # Extract reviews from product page
            for container in review_containers:
                if len(reviews) >= max_reviews:
                    break
                review = _parse_review_container(container, len(reviews))
                if review and review.get('body') and len(review.get('body', '')) > 10:
                    reviews.append(review)
            
            if len(reviews) > 0:
                print(f"  Extracted {len(reviews)} reviews from product page")
        
        # Note: Review pages may require browser session/cookies to access
        # The URLs provided work in browser but may be blocked for automated requests
        
        # Try to find "See all reviews" or review page links for THIS product
        # Look for links that contain the product ID in the PATH (not just anywhere in URL)
        review_links = soup.find_all('a', href=re.compile(r'product-reviews|customer-reviews|/gp/customer-reviews'))
        for link in review_links:
            href = link.get('href', '')
            link_text = link.get_text(strip=True).lower()
            # Check if product ID is in the path (e.g., /product-reviews/B0CL61F39H/)
            if f'/product-reviews/{product_id}' in href or f'/gp/customer-reviews/{product_id}' in href:
                if href.startswith('http'):
                    review_url_template = href.split('?')[0]  # Remove query params for now
                elif href.startswith('/'):
                    review_url_template = f"{base_url}{href.split('?')[0]}"
                else:
                    review_url_template = urljoin(base_url, href.split('?')[0])
                print(f"  Found review page link: {review_url_template}")
                break
        
        # Also look for "See all reviews" link near the reviews section
        if not review_url_template:
            see_all_links = soup.find_all('a', string=re.compile(r'see all|view all|all reviews', re.I))
            for link in see_all_links:
                href = link.get('href', '')
                if f'/product-reviews/{product_id}' in href or f'/gp/customer-reviews/{product_id}' in href:
                    if href.startswith('http'):
                        review_url_template = href.split('?')[0]
                    elif href.startswith('/'):
                        review_url_template = f"{base_url}{href.split('?')[0]}"
                    else:
                        review_url_template = urljoin(base_url, href.split('?')[0])
                    print(f"  Found 'See all reviews' link: {review_url_template}")
                    break
        
        # If no link found, try common patterns
        if not review_url_template:
            # Try multiple URL patterns
            possible_patterns = [
                f"{base_url}/product-reviews/{product_id}",
                f"{base_url}/gp/customer-reviews/{product_id}",
                f"{base_url}/product-reviews/{product_id}/ref=cm_cr_dp_d_show_all_btm",
                f"{base_url}/product-reviews/{product_id}/ref=cm_cr_arp_d_viewopt_sr",
            ]
            for pattern in possible_patterns:
                try:
                    test_response = requests.get(pattern, headers=headers, timeout=10)
                    if test_response.status_code == 200:
                        test_soup = BeautifulSoup(test_response.content, 'html.parser')
                        if test_soup.find_all('li', {'data-hook': 'review'}):
                            review_url_template = pattern
                            print(f"  Found working review URL pattern: {pattern}")
                            break
                except:
                    continue
        
    except Exception as e:
        print(f"  Could not fetch product page: {e}")
    
    # Use the correct review page URL pattern provided by user
    # Page 1: ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews
    # Page 2+: ref=cm_cr_arp_d_paging_btm_next_{page}?ie=UTF8&reviewerType=all_reviews&pageNumber={page}
    base_review_url = f"{base_url}/product-reviews/{product_id}"
    
    print(f"Scraping reviews for product {product_id}...")
    
    # Scrape review pages with correct pagination
    page = 1
    consecutive_empty = 0
    
    while len(reviews) < max_reviews and consecutive_empty < 3:
        try:
            # Construct review page URL with correct pagination pattern
            if page == 1:
                review_url = f"{base_review_url}/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews"
            else:
                review_url = f"{base_review_url}/ref=cm_cr_arp_d_paging_btm_next_{page}?ie=UTF8&reviewerType=all_reviews&pageNumber={page}"
                
            print(f"  Fetching review page {page}...")
            response = requests.get(review_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Check if we got redirected or blocked
            if response.status_code != 200:
                print(f"  Got status {response.status_code}, stopping...")
                break
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find review containers - Amazon uses <li> elements, not <div>
            review_containers = soup.find_all('li', {'data-hook': 'review'})
            
            if not review_containers:
                # Try alternative selectors
                review_containers = soup.select('li[data-hook="review"]')
            
            if not review_containers:
                consecutive_empty += 1
                if consecutive_empty >= 3:
                    print(f"  No reviews found on last 3 pages. Stopping...")
                    break
                page += 1
                time.sleep(2)
                continue
            
            # Found reviews!
            consecutive_empty = 0
            
            page_reviews = []
            seen_review_ids = set(r.get('review_id') for r in reviews if r.get('review_id'))
            
            for container in review_containers:
                if len(reviews) >= max_reviews:
                    break
                
                review = _parse_review_container(container, len(reviews))
                if review and review.get('body') and len(review.get('body', '')) > 10:
                    # Skip duplicates
                    review_id = review.get('review_id', '')
                    if review_id and review_id in seen_review_ids:
                        continue
                    
                    page_reviews.append(review)
                    reviews.append(review)
                    if review_id:
                        seen_review_ids.add(review_id)
            
            print(f"  Page {page}: Found {len(page_reviews)} new reviews (Total: {len(reviews)})")
            
            if len(page_reviews) == 0:
                consecutive_empty += 1
                if consecutive_empty >= 3:
                    print(f"  No reviews found on last 3 pages. Stopping...")
                    break
            else:
                consecutive_empty = 0
            
            page += 1
            time.sleep(2)  # Be respectful with requests
            
        except requests.exceptions.RequestException as e:
            print(f"  Error fetching page {page}: {e}")
            consecutive_empty += 1
            if consecutive_empty >= 3:
                break
            page += 1
            time.sleep(2)
        except Exception as e:
            print(f"  Error processing page {page}: {e}")
            consecutive_empty += 1
            if consecutive_empty >= 3:
                break
            page += 1
            time.sleep(2)
    
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


def preprocess_reviews(reviews: List[Dict], max_reviews: int = 400) -> List[Dict]:
    """
    Clean and optionally sample reviews to ensure diversity.
    
    Args:
        reviews: List of raw review dictionaries
        max_reviews: Maximum number of reviews to keep
        
    Returns:
        List of cleaned review dictionaries
    """
    cleaned = []
    
    for review in reviews:
        # Clean text
        body = review.get('body', '').strip()
        title = review.get('title', '').strip()
        
        # Remove HTML tags if any
        body = re.sub(r'<[^>]+>', '', body)
        title = re.sub(r'<[^>]+>', '', title)
        
        # Normalize whitespace
        body = ' '.join(body.split())
        title = ' '.join(title.split())
        
        # Skip empty or very short reviews
        if len(body) < 20:
            continue
        
        cleaned_review = {
            **review,
            'body': body,
            'title': title
        }
        cleaned.append(cleaned_review)
    
    # If we have more than max_reviews, perform stratified sampling
    if len(cleaned) > max_reviews:
        # Group by rating
        by_rating = {}
        for review in cleaned:
            rating = review.get('rating', 0)
            if rating not in by_rating:
                by_rating[rating] = []
            by_rating[rating].append(review)
        
        # Sample proportionally
        sampled = []
        for rating, rating_reviews in by_rating.items():
            proportion = len(rating_reviews) / len(cleaned)
            sample_size = max(1, int(max_reviews * proportion))
            sampled.extend(rating_reviews[:sample_size])
        
        # If still too many, randomly sample
        if len(sampled) > max_reviews:
            import random
            random.shuffle(sampled)
            sampled = sampled[:max_reviews]
        
        cleaned = sampled
    
    return cleaned


if __name__ == "__main__":
    # Test with provided URLs
    products = [
        "https://www.amazon.com/PlayStation%C2%AE5-console-slim-PlayStation-5/dp/B0CL61F39H/ref=sr_1_1?crid=JHI54LL4IB38&dib=eyJ2IjoiMSJ9.iljGzJ9gK4edCvZ4knhV5sEzGLOp35OxhJKXWBnySFW7vKcyeB8JmjRxnm6G4wOQ8S2wptC09n-5BA49qVeMopQkWirqavNnTksuwTsxOWy21S96F9h7-ny8aTboaLdspw-1mizwv8VAXviUOWQNZzMfrEupXa7pLrq6uNT9fP2kSZHzCHwmdcfo-m0SN5f6BEsPYVnlBD2heQ-nxQdlPcKCvCN7SZnHRd7IJq-hWOo.Dn3WgFVCe7q2lXdN5vUtsGVhdVqvpWnDz4Nfc1X2IrM&dib_tag=se&keywords=playstation+5&qid=1763956660&sprefix=playstation+5+%2Caps%2C279&sr=8-1",
        "https://www.amazon.com/STANLEY-Flowstate-3-Position-Compatible-Insulated/dp/B0CJZMP7L1/ref=sr_1_1?crid=LSHECHANWYZL&dib=eyJ2IjoiMSJ9.ffe_6KF4JbPgrGr7B4C9KrXJcpNjt0IIBTQAf34vus5KvIwkouMEPzvAzY7IUtendi97bcXiSoijEnrL-3l0kQF0l5iKTLpYG6Hzvivl-grXaJILOyRsjkUdTm-zMl71cJxtJLDbr_xn5LKxe-qtDhginVwXczYd1K8w6sxVHluEjB9gWUk9T8H_GFtKE2Rc1AH44d1-_ISnCvQrccCkwU5a1MmswKdwlvcfZu8_w-6pYCbKWNDBl32XE_6PFanWFBwKwXF51S0Kc7XJmrH_-4NYsfDIfaPsHpTBS4qhlUE.s2tHK2mowp5sZEeoUe9K2_5R_ubAItI4PE5s-trQfqF&dib_tag=se&keywords=amazon%2Bstanley%2Bcup&qid=1763922923&sprefix=amazon%2Bsta%2Caps%2C112&sr=8-1&th=1",
        "https://www.amazon.com/Jordan-Shoes-553558-092-Black-Medium/dp/B0DJ9SVTB6/ref=sr_1_11?crid=32OREV6IIBCA8&dib=eyJ2IjoiMSJ9.c9IM_GWKqt2P2AWxZIQJ0lXHB8YCj-AOddwnvCxeQTBV0gCVL4hki2D7bJLxGfCSDXcmZKoIXqtwBSAfrm5ed1XJu39pf7F63VwLzmBQp_-9R4dbwfpKnv9DhbQ8YNiLaQ44fo-mr3E90IB2Ml33juTDpdlm0RENcP2GzNEoX57KdX7ahemHlJ1bjNJwMpiSHaKkhN9jzetW1SfYofwJbYgVH_JGJqHjJfvJa22PiwenKKWW9mjE9YJ61lLI0X0h_oHxAhKu_Zk6l2LNIc_cl_xVqpAHWKUVEhwlcxOCQj4.WBcto1R2ouHGlnYZICgBhxrYQ9BRLcquTrgB4QieKlE&dib_tag=se&keywords=jordan%2Bshoes%2Bfor%2Bmen&qid=1763923037&sprefix=jordan%2B%2Caps%2C114&sr=8-11&th=1&psc=1"
    ]
    
    for url in products:
        try:
            raw_reviews = scrape_reviews(url, max_reviews=400)
            processed_reviews = preprocess_reviews(raw_reviews, max_reviews=400)
            
            # Save processed reviews
            product_id = extract_product_id(url)
            os.makedirs("data/processed", exist_ok=True)
            processed_path = f"data/processed/{product_id}_reviews_processed.json"
            with open(processed_path, 'w', encoding='utf-8') as f:
                json.dump(processed_reviews, f, indent=2, ensure_ascii=False)
            
            print(f"[OK] Processed {len(processed_reviews)} reviews")
            print(f"  Saved to: {processed_path}\n")
            
            time.sleep(2)
        except Exception as e:
            print(f"Failed to scrape reviews for {url}: {e}")

