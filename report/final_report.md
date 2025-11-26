# Final Project Report: Generating Product Images from Customer Reviews

**Course:** 94-844 Generative AI Lab (Fall 2025)  
**Project:** Generating Product Images from Customer Reviews

## Introduction

This project implements an end-to-end pipeline that:
1. Scrapes product descriptions and customer reviews from Amazon
2. Builds a RAG (Retrieval-Augmented Generation) pipeline for analysis
3. Generates product images using DALL·E 3 and Stable Diffusion XL (SDXL)
4. Compares generated images against real product images
5. Orchestrates everything via a LangChain + LangGraph agentic workflow
6. Produces comprehensive analysis reports

The goal is to demonstrate how customer reviews can inform AI-generated product imagery, and to compare the effectiveness of different image generation models.

## Q1 – Product Selection & Data Collection

### Selected Products

We selected three diverse products to ensure comprehensive coverage:

1. **PlayStation 5 Console – Marvel's Spider-Man 2 Bundle** (B0CKZGY5B6)
   - Category: Electronics/Gaming
   - Visual Complexity: High
   - Review Focus: Build quality, design, aesthetics

2. **Stanley Flowstate Tumbler** (B0CJZMP7L1)
   - Category: Consumer Goods/Drinkware
   - Visual Complexity: Medium
   - Review Focus: Appearance, color accuracy, branding

3. **Nike Men's Air Jordan 1 Low Sneaker** (B0DJ9SVTB6)
   - Category: Fashion/Footwear
   - Visual Complexity: High
   - Review Focus: Style, color accuracy, material quality

### Data Collection

**Scraping Pipeline:**
- Product data: Title, bullet points, description, main image URLs
- Reviews: Up to 400 reviews per product with ratings, titles, bodies, dates, variants
- Preprocessing: Text cleaning, normalization, stratified sampling

**Data Storage:**
- Raw data: `data/raw/{product_id}_product.json`, `{product_id}_reviews_raw.json`
- Processed data: `data/processed/{product_id}_reviews_processed.json`

See `report/q1_products.md` for detailed product selection rationale.

## Q2 – LLM Analysis & RAG Pipeline

### RAG Architecture

**Chunking:**
- Product descriptions and reviews chunked into 800-1200 token segments
- 100-token overlap for context preservation
- Source type markers (description/review) for traceability

**Embedding:**
- Model: `text-embedding-3-large` (3072 dimensions)
- Vector DB: FAISS with cosine similarity
- Index per product for efficient retrieval

**Retrieval:**
- Specialized visual chunk retrieval
- Query examples: "visual features", "colors, materials, textures", "branding, packaging"
- Top-k retrieval (default: 10 chunks)

### LLM Analysis Components

1. **Holistic Summary:** Zero-shot product summary from description only
2. **RAG-Augmented Summary:** Synthesis of product info and retrieved review chunks
3. **Self-Refined Summary:** Draft → critique → refinement cycle
4. **Structured Extraction:** JSON schema for visual attributes (shape, material, colors, branding, etc.)
5. **Sentiment-Feature Mapping:** Links visual features to positive/negative sentiment

**Outputs:**
- `analysis/{product_id}_analysis.json` - Structured data
- `analysis/{product_id}_summary.md` - Human-readable summary
- `prompts/q2_prompts.md` - All prompts used

See `report/q2_analysis.md` for detailed architecture.

## Q3 – Image Generation & Model Comparison

### Image Generation

**Prompt Construction:**
- 1-3 variants per product (base, detailed, customer-focused)
- Incorporates extracted visual attributes
- Emphasizes customer descriptions

**DALL·E 3:**
- 5 images per prompt variant
- 1024x1024 resolution, standard quality
- Output: `image_generation/outputs/dalle/{product_id}/`

**SDXL:**
- 5 images per prompt variant
- 1024x1024 resolution, CFG scale 7, 30 steps
- Output: `image_generation/outputs/sdxl/{product_id}/`

**Ground Truth:**
- Downloaded from product pages
- Storage: `image_generation/ground_truth/{product_id}/`

### Comparison Metrics

1. **CLIP Embedding Similarity:** Semantic similarity (0-1)
2. **Color Histogram Comparison:** RGB histogram correlation (0-1)
3. **SSIM:** Structural Similarity Index (0-1)
4. **Average Similarity:** Mean of all metrics

### Results

Comparison results stored in:
- `report/q3_image_comparison_{product_id}_{model}.json`
- `report/q3_image_comparison.md`

See `report/q3_image_comparison.md` for detailed methodology.

## Q4 – Agentic Workflow

### LangGraph Architecture

**Workflow Graph:**
```
review_analyzer → prompt_constructor → image_generator → evaluation → report
```

**State Management:**
- Centralized `WorkflowState` with all pipeline data
- Type-safe state updates
- Error logging in state

### Agent Responsibilities

1. **Review Analyzer:** Loads data, runs RAG analysis, extracts attributes
2. **Prompt Constructor:** Builds image generation prompts
3. **Image Generator:** Generates images with DALL·E 3 and SDXL
4. **Evaluation:** Compares images vs ground truth
5. **Report Agent:** Assembles final report snippet

**Execution:**
```python
from agent_workflow.graph import run_full_workflow
final_state = run_full_workflow(product_id="B0CKZGY5B6")
```

**Outputs:**
- `report/workflow_outputs/{product_id}_snippet.md`

See `report/q4_agent_workflow.md` for detailed architecture.

## Challenges & Lessons Learned

### Technical Challenges

1. **Amazon Scraping:** 
   - Challenge: Anti-scraping measures, dynamic content
   - Solution: Proper headers, error handling, rate limiting

2. **RAG Pipeline:**
   - Challenge: Balancing chunk size vs context
   - Solution: 800-1200 token chunks with overlap

3. **Image Comparison:**
   - Challenge: Multiple similarity metrics, computational cost
   - Solution: CLIP for semantic, histograms for color, SSIM for structure

4. **SDXL API:**
   - Challenge: API availability and format differences
   - Solution: Fallback handling, error resilience

### Lessons Learned

1. **Modularity:** Separating concerns into agents improves maintainability
2. **Error Handling:** Graceful degradation keeps pipeline running
3. **State Management:** Centralized state simplifies debugging
4. **Prompt Engineering:** Multiple prompt variants improve results
5. **Evaluation:** Multiple metrics provide comprehensive comparison

### Best Practices Applied

- Clean, modular code structure
- Comprehensive error handling
- Reproducible prompts and configurations
- Detailed logging and documentation
- Type safety with TypedDict

## Conclusion

This project successfully demonstrates:

1. **End-to-End Pipeline:** From scraping to image generation to evaluation
2. **RAG Integration:** Effective use of retrieval-augmented generation for analysis
3. **Multi-Model Comparison:** Systematic comparison of DALL·E 3 vs SDXL
4. **Agentic Workflow:** LangGraph orchestration of complex multi-step pipeline
5. **Comprehensive Reporting:** Detailed analysis and comparison reports

The pipeline is fully functional, reproducible, and extensible. All components are modular and can be improved or replaced independently.

## Appendix

### Project Structure

```
project/
  data/
    raw/          # Raw scraped data
    processed/    # Cleaned data
  scrapers/      # Scraping modules
  rag_pipeline/  # RAG components
  analysis/      # LLM analysis
  prompts/       # Prompt logs
  image_generation/  # Image generation & comparison
  agent_workflow/   # LangGraph workflow
  report/        # All reports
```

### Key Files

- **Scrapers:** `scrapers/scrape_product.py`, `scrapers/scrape_reviews.py`
- **RAG:** `rag_pipeline/chunker.py`, `embedder.py`, `retriever.py`
- **Analysis:** `analysis/llm_analysis.py`, `structure_extractors.py`, `sentiment_extractors.py`
- **Image Gen:** `image_generation/prompt_builder.py`, `dalle_generator.py`, `sdxl_generator.py`, `compare_images.py`
- **Workflow:** `agent_workflow/graph.py`, `agents/*.py`

### Configuration

- **Environment:** `.env` with API keys
- **Dependencies:** `requirements.txt`
- **Setup:** See `README.md`

### Data Paths

- Product data: `data/raw/{product_id}_product.json`
- Reviews: `data/processed/{product_id}_reviews_processed.json`
- Analysis: `analysis/{product_id}_analysis.json`
- Images: `image_generation/outputs/{model}/{product_id}/`
- Reports: `report/workflow_outputs/{product_id}_snippet.md`

---

**End of Report**


