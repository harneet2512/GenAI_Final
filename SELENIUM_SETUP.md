# Selenium Setup Guide

## What You Need

1. **Google Chrome Browser** - Must be installed on your system
   - Download from: https://www.google.com/chrome/
   - The scraper will automatically download the matching ChromeDriver

2. **Python Packages** - Will be installed automatically when you run:
   ```bash
   pip install -r requirements.txt
   ```

## How It Works

The Selenium-based scraper:
- Opens a real Chrome browser window
- Navigates to Amazon review pages
- Waits for JavaScript to load content
- Extracts reviews from each page
- Handles pagination automatically

## Running the Scraper

### Option 1: Use the updated main script (automatically uses Selenium)
```bash
python main.py --step scrape
```

### Option 2: Use Selenium scraper directly
```python
from scrapers.scrape_reviews_selenium import scrape_reviews_selenium

reviews = scrape_reviews_selenium(
    url="https://www.amazon.com/product/dp/B0CL61F39H",
    max_reviews=250,
    headless=False  # Set to True to hide browser window
)
```

## What to Expect

1. **First Run**: ChromeDriver will be automatically downloaded (one-time setup)
2. **Browser Window**: A Chrome window will open and navigate through review pages
3. **Progress**: You'll see console output showing progress
4. **Time**: Takes longer than requests-based scraping (2-5 seconds per page)

## Troubleshooting

### ChromeDriver Issues
- If ChromeDriver download fails, manually download from: https://chromedriver.chromium.org/
- Place it in your PATH or project directory

### Browser Not Opening
- Make sure Chrome is installed
- Check if Chrome is up to date
- Try running with `headless=False` first to see what's happening

### Slow Performance
- This is normal - Selenium is slower but more reliable
- Each page takes 2-5 seconds to load
- For 250 reviews across ~25 pages, expect 1-2 minutes

### Amazon Blocking
- If Amazon still blocks, try:
  - Running with `headless=False` (visible browser)
  - Adding delays between requests
  - Using a VPN or different network

## Notes

- The browser window will be visible by default (you can watch it work)
- Set `headless=True` to run in background (may be more easily detected)
- The scraper automatically handles:
  - Waiting for page loads
  - Scrolling to load content
  - Handling pagination
  - Avoiding duplicate reviews


