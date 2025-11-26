# Q1: Product Selection & Data Collection

## Product Selection

We selected three diverse products from Amazon to ensure comprehensive coverage across different categories, visual complexities, and review patterns:

### 1. PlayStation 5 Console – Marvel's Spider-Man 2 Bundle
**URL:** https://www.amazon.com/PlayStation-Console-Marvels-Spider-Man-Bundle-5/dp/B0CKZGY5B6
**Product ID:** B0CKZGY5B6

**Why this product:**
- **Category:** Electronics/Gaming Console
- **Visual Complexity:** High - includes console, controller, packaging, branding
- **Review Richness:** Electronics products typically have detailed reviews about build quality, design, and visual appearance
- **Variability:** Mix of technical and aesthetic reviews

### 2. Stanley Flowstate Tumbler
**URL:** https://www.amazon.com/STANLEY-Flowstate-3-Position-Compatible-Insulated/dp/B0CJZMP7L1
**Product ID:** B0CJZMP7L1

**Why this product:**
- **Category:** Consumer Goods/Drinkware
- **Visual Complexity:** Medium - simple form but distinctive branding and color options
- **Review Richness:** Lifestyle products have emotional and visual descriptions
- **Variability:** Reviews focus on appearance, color accuracy, and aesthetic appeal

### 3. Nike Men's Air Jordan 1 Low Sneaker
**URL:** https://www.amazon.com/Jordan-Shoes-553558-092-Black-Medium/dp/B0DJ9SVTB6
**Product ID:** B0DJ9SVTB6

**Why this product:**
- **Category:** Fashion/Footwear
- **Visual Complexity:** High - intricate design, multiple colors, branding, texture
- **Review Richness:** Fashion items have highly detailed visual descriptions
- **Variability:** Reviews emphasize style, color accuracy, material quality, and visual appeal

## Category Diversity

The three products span:
- **Electronics** (PS5) - Technical product with functional and aesthetic considerations
- **Consumer Goods** (Stanley Tumbler) - Lifestyle product with strong brand identity
- **Fashion** (Jordan Sneakers) - Style-focused product with high visual importance

This diversity ensures our pipeline can handle:
- Different types of visual descriptions
- Varying levels of technical detail
- Multiple sentiment patterns
- Diverse customer language

## Visual Complexity

1. **PS5 Bundle:** Complex - multiple components, packaging, branding elements, color schemes
2. **Stanley Tumbler:** Moderate - simple form but important color and branding details
3. **Jordan Sneakers:** High - intricate design patterns, multiple materials, detailed colorways

## Review Richness and Variability

All three products have:
- **High review volume** (targeting 400 reviews per product)
- **Diverse rating distribution** (1-5 stars)
- **Temporal diversity** (older and newer reviews)
- **Visual focus** - customers describe appearance, colors, materials, and design

The scraping pipeline ensures:
- Balanced sampling across rating buckets
- Temporal diversity
- Sufficient visual descriptions for RAG analysis

## Data Collection Process

1. **Product Scraping:** Extracts title, bullet points, description, and main image URLs
2. **Review Scraping:** Paginates through review pages, extracts up to 400 reviews with:
   - Review ID, rating, title, body, date, variant
   - Diversity across ratings and dates
3. **Preprocessing:** Cleans text, normalizes whitespace, performs stratified sampling if needed
4. **Storage:** Saves raw and processed data in structured JSON/CSV formats

## Data Files

Raw data stored in `data/raw/`:
- `{product_id}_product.json` - Product information
- `{product_id}_reviews_raw.json` - Raw reviews (JSON)
- `{product_id}_reviews_raw.csv` - Raw reviews (CSV)

Processed data stored in `data/processed/`:
- `{product_id}_reviews_processed.json` - Cleaned, normalized reviews


