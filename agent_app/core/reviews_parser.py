"""
Review parser wrapper - extracts reviews from HTML.
Reuses existing parsing logic from scrapers.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from bs4 import BeautifulSoup

from .paths import ProductId, raw_reviews_path
from .html_loader import load_html_contents


def _parse_review_container(container, review_index: int) -> Optional[Dict]:
    """
    Parse a single review container element and extract review data.
    Reuses logic from scrapers/scrape_reviews.py.
    
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
            rating_icon = title_elem.find('i', {'data-hook': re.compile('review-star-rating|cmps-review-star-rating')})
            if rating_icon:
                rating_text = rating_icon.get_text(strip=True)
                all_text = title_elem.get_text(strip=True)
                title = all_text.replace(rating_text, '').strip()
                title = re.sub(r'\d+\.\d+\s+out\s+of\s+5\s+stars', '', title, flags=re.IGNORECASE).strip()
                title = re.sub(r'^\s*[|\-\s]+\s*', '', title).strip()
                title = ' '.join(title.split())
            else:
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
            collapsed_elem = body_elem.find('div', {'data-hook': 'review-collapsed'})
            if collapsed_elem:
                body = collapsed_elem.get_text(strip=True)
            else:
                for script in body_elem.find_all('script'):
                    script.decompose()
                for expander in body_elem.find_all(['a', 'div'], {'data-hook': re.compile('expand|collapse')}):
                    expander.decompose()
                body = body_elem.get_text(strip=True)
            
            if body:
                body = ' '.join(body.split())
        
        # Extract date
        date = ""
        date_elem = container.find('span', {'data-hook': 'review-date'})
        if date_elem:
            date = date_elem.get_text(strip=True)
        
        # Extract variant (color/size)
        variant = ""
        variant_elem = container.find('span', {'data-hook': 'format-strip-linkless'})
        if variant_elem:
            variant = variant_elem.get_text(strip=True)
        else:
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
    except Exception:
        return None


def parse_reviews_from_html(html_list: List[str]) -> List[Dict]:
    """
    Extract reviews from raw HTML strings.
    
    Args:
        html_list: List of HTML content strings
        
    Returns:
        List of review dictionaries with keys: review_id, rating, title, body, date, variant
    """
    all_reviews: List[Dict] = []
    review_index = 0
    
    for html_content in html_list:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all review containers
        review_containers = soup.find_all('li', {'data-hook': 'review'})
        
        for container in review_containers:
            review = _parse_review_container(container, review_index)
            if review and review.get('body') and len(review.get('body', '')) > 10:
                all_reviews.append(review)
                review_index += 1
    
    return all_reviews


def build_reviews_json(product_id: ProductId) -> Path:
    """
    Build reviews JSON from HTML files for a product.
    
    Args:
        product_id: Product identifier
        
    Returns:
        Path to the created JSON file
    """
    html_list = load_html_contents(product_id)
    reviews = parse_reviews_from_html(html_list)
    
    out_path = raw_reviews_path(product_id)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)
    
    return out_path

