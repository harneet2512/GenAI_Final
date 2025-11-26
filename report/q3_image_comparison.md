# Q3: Image Generation & Model Comparison

## Image Generation Pipeline

### Prompt Construction

The prompt builder (`image_generation/prompt_builder.py`) creates 1-3 prompt variants per product:
- **Base variant:** Standard product photography prompt
- **Detailed variant:** Comprehensive specifications
- **Customer-focused variant:** Emphasizes customer descriptions

Each prompt includes:
- Product name
- Shape, material, color palette
- Branding elements
- Distinctive features
- Usage contexts

### DALL·E 3 Generation

**Implementation:** `image_generation/dalle_generator.py`
- **Model:** DALL·E 3 via OpenAI Images API
- **Settings:** 1024x1024, standard quality
- **Output:** 5 images per prompt variant
- **Storage:** `image_generation/outputs/dalle/{product_id}/`

### SDXL Generation

**Implementation:** `image_generation/sdxl_generator.py`
- **Model:** Stable Diffusion XL via Stability AI API
- **Settings:** 1024x1024, CFG scale 7, 30 steps
- **Output:** 5 images per prompt variant
- **Storage:** `image_generation/outputs/sdxl/{product_id}/`

### Ground Truth Images

Downloaded from product pages:
- **Source:** Main product image URLs from scraping
- **Storage:** `image_generation/ground_truth/{product_id}/`
- **Format:** PNG files named `real_{i}.png`

## Image Comparison Metrics

### 1. CLIP Embedding Similarity

- **Method:** Cosine similarity between CLIP embeddings
- **Model:** CLIP ViT-B/32 via sentence-transformers
- **Range:** 0-1 (higher is better)
- **Purpose:** Semantic similarity assessment

### 2. Color Histogram Comparison

- **Method:** Correlation coefficient of RGB histograms
- **Bins:** 256 per channel
- **Range:** 0-1 (normalized correlation)
- **Purpose:** Color distribution similarity

### 3. Structural Similarity Index (SSIM)

- **Method:** Structural similarity metric
- **Implementation:** scikit-image
- **Range:** 0-1 (higher is better)
- **Purpose:** Perceptual similarity assessment

### 4. Average Similarity

- **Method:** Mean of all three metrics
- **Purpose:** Overall comparison score

## Comparison Process

For each product:
1. Load all generated images (DALL·E and SDXL)
2. Load ground truth images
3. Compare each generated image vs each ground truth image
4. Aggregate statistics per model
5. Generate comparison reports

## Output Files

Per-product comparison:
- `report/q3_image_comparison_{product_id}_dalle.json`
- `report/q3_image_comparison_{product_id}_sdxl.json`

Overall comparison:
- `report/q3_image_comparison.md` (this file)

## Model Comparison Results

Results are aggregated across all products to determine:
- Which model better captures visual attributes
- Color accuracy
- Structural accuracy
- Overall perceptual similarity

## Key Findings

1. **Prompt Variants:** Different prompt styles yield different results
2. **Model Strengths:** Each model has different strengths (realism, detail, color accuracy)
3. **Ground Truth Alignment:** Comparison reveals how well models match real product appearance
4. **Hallucinations:** Identifies where models deviate from actual product features


