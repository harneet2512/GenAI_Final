"""
Amazon Product Scraper
Scrapes product title, bullet points, description, and main image URLs from Amazon product pages.
"""

import json
import re
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from typing import Dict, List, Optional
import time


def extract_product_id(url: str) -> str:
    """Extract product ID (ASIN) from Amazon URL."""
    # Try to extract ASIN from URL
    match = re.search(r'/dp/([A-Z0-9]{10})', url)
    if match:
        return match.group(1)
    
    # Alternative pattern
    match = re.search(r'/product/([A-Z0-9]{10})', url)
    if match:
        return match.group(1)
    
    # Fallback: use query parameter
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    if 'asin' in params:
        return params['asin'][0]
    
    raise ValueError(f"Could not extract product ID from URL: {url}")


def scrape_product(url: str, output_dir: str = "data/raw") -> Dict:
    """
    Scrape product information from Amazon product page.
    
    Args:
        url: Amazon product URL
        output_dir: Directory to save output JSON
        
    Returns:
        Dictionary containing product information
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        product_id = extract_product_id(url)
        
        # Extract title
        title = None
        title_selectors = [
            '#productTitle',
            'h1.a-size-large',
            'span#productTitle',
            'h1 span.a-size-large'
        ]
        for selector in title_selectors:
            elem = soup.select_one(selector)
            if elem:
                title = elem.get_text(strip=True)
                break
        
        if not title:
            # Fallback: try to find any h1
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text(strip=True)
        
        # Extract bullet points
        bullet_points = []
        bullet_selectors = [
            '#feature-bullets ul li span.a-list-item',
            'ul.a-unordered-list.a-vertical.a-spacing-mini li span',
            '#feature-bullets ul li'
        ]
        for selector in bullet_selectors:
            bullets = soup.select(selector)
            if bullets:
                for bullet in bullets:
                    text = bullet.get_text(strip=True)
                    # Filter out empty or very short bullets
                    if text and len(text) > 10 and text.lower() not in ['add to cart', 'buy now']:
                        bullet_points.append(text)
                if bullet_points:
                    break
        
        # Extract long description
        description = ""
        desc_selectors = [
            '#productDescription p',
            '#productDescription',
            '#feature-bullets_feature_div',
            '#aplus_feature_div'
        ]
        for selector in desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                description = desc_elem.get_text(separator='\n', strip=True)
                if description:
                    break
        
        # Extract main image URLs
        image_urls = []
        img_selectors = [
            '#landingImage',
            '#imgBlkFront',
            '#main-image',
            'img#landingImage',
            'div#imgTagWrapperId img'
        ]
        for selector in img_selectors:
            img = soup.select_one(selector)
            if img and img.get('src'):
                image_urls.append(img['src'])
            elif img and img.get('data-src'):
                image_urls.append(img['data-src'])
        
        # Also try to get additional images from the image carousel
        carousel_images = soup.select('#altImages ul li img')
        for img in carousel_images:
            if img.get('src') and img['src'] not in image_urls:
                # Clean up the URL (remove size parameters)
                img_url = img['src'].split('._')[0] if '._' in img['src'] else img['src']
                if img_url not in image_urls:
                    image_urls.append(img_url)
        
        # Extract additional images from data attributes
        for img in soup.find_all('img', {'data-a-dynamic-image': True}):
            try:
                import json as json_lib
                dynamic_data = json_lib.loads(img['data-a-dynamic-image'])
                for img_url in dynamic_data.keys():
                    if img_url not in image_urls:
                        image_urls.append(img_url)
            except:
                pass
        
        # Clean and deduplicate image URLs
        cleaned_urls = []
        seen = set()
        for url in image_urls:
            # Remove size parameters
            clean_url = re.sub(r'\._[A-Z0-9,]+_\.', '.', url)
            if clean_url not in seen and 'http' in clean_url:
                cleaned_urls.append(clean_url)
                seen.add(clean_url)
        
        product_data = {
            "product_id": product_id,
            "url": url,
            "title": title or "Unknown",
            "bullet_points": bullet_points[:10],  # Limit to top 10
            "description": description,
            "main_image_urls": cleaned_urls[:10]  # Limit to top 10
        }
        
        # Save to JSON
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{product_id}_product.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(product_data, f, indent=2, ensure_ascii=False)
        
        print(f"[OK] Scraped product: {title}")
        print(f"  Saved to: {output_path}")
        
        return product_data
        
    except Exception as e:
        print(f"Error scraping product: {e}")
        raise


if __name__ == "__main__":
    # Test with provided URLs
    products = [
        "https://www.amazon.com/PlayStation%C2%AE5-console-slim-PlayStation-5/dp/B0CL61F39H/ref=sr_1_1?crid=JHI54LL4IB38&dib=eyJ2IjoiMSJ9.iljGzJ9gK4edCvZ4knhV5sEzGLOp35OxhJKXWBnySFW7vKcyeB8JmjRxnm6G4wOQ8S2wptC09n-5BA49qVeMopQkWirqavNnTksuwTsxOWy21S96F9h7-ny8aTboaLdspw-1mizwv8VAXviUOWQNZzMfrEupXa7pLrq6uNT9fP2kSZHzCHwmdcfo-m0SN5f6BEsPYVnlBD2heQ-nxQdlPcKCvCN7SZnHRd7IJq-hWOo.Dn3WgFVCe7q2lXdN5vUtsGVhdVqvpWnDz4Nfc1X2IrM&dib_tag=se&keywords=playstation+5&qid=1763956660&sprefix=playstation+5+%2Caps%2C279&sr=8-1",
        "https://www.amazon.com/STANLEY-Flowstate-3-Position-Compatible-Insulated/dp/B0CJZMP7L1/ref=sr_1_1?crid=LSHECHANWYZL&dib=eyJ2IjoiMSJ9.ffe_6KF4JbPgrGr7B4C9KrXJcpNjt0IIBTQAf34vus5KvIwkouMEPzvAzY7IUtendi97bcXiSoijEnrL-3l0kQF0l5iKTLpYG6Hzvivl-grXaJILOyRsjkUdTm-zMl71cJxtJLDbr_xn5LKxe-qtDhginVwXczYd1K8w6sxVHluEjB9gWUk9T8H_GFtKE2Rc1AH44d1-_ISnCvQrccCkwU5a1MmswKdwlvcfZu8_w-6pYCbKWNDBl32XE_6PFanWFBwKwXF51S0Kc7XJmrH_-4NYsfDIfaPsHpTBS4qhlUE.s2tHK2mowp5sZEeoUe9K2_5R_ubAItI4PE5s-trQfqF&dib_tag=se&keywords=amazon%2Bstanley%2Bcup&qid=1763922923&sprefix=amazon%2Bsta%2Caps%2C112&sr=8-1&th=1",
        "https://www.amazon.com/Jordan-Shoes-553558-092-Black-Medium/dp/B0DJ9SVTB6/ref=sr_1_11?crid=32OREV6IIBCA8&dib=eyJ2IjoiMSJ9.c9IM_GWKqt2P2AWxZIQJ0lXHB8YCj-AOddwnvCxeQTBV0gCVL4hki2D7bJLxGfCSDXcmZKoIXqtwBSAfrm5ed1XJu39pf7F63VwLzmBQp_-9R4dbwfpKnv9DhbQ8YNiLaQ44fo-mr3E90IB2Ml33juTDpdlm0RENcP2GzNEoX57KdX7ahemHlJ1bjNJwMpiSHaKkhN9jzetW1SfYofwJbYgVH_JGJqHjJfvJa22PiwenKKWW9mjE9YJ61lLI0X0h_oHxAhKu_Zk6l2LNIc_cl_xVqpAHWKUVEhwlcxOCQj4.WBcto1R2ouHGlnYZICgBhxrYQ9BRLcquTrgB4QieKlE&dib_tag=se&keywords=jordan%2Bshoes%2Bfor%2Bmen&qid=1763923037&sprefix=jordan%2B%2Caps%2C114&sr=8-11&th=1&psc=1"
    ]
    
    for url in products:
        try:
            scrape_product(url)
            time.sleep(2)  # Be respectful with requests
        except Exception as e:
            print(f"Failed to scrape {url}: {e}")

