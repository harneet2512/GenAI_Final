# Q2 – LLM + RAG Text Analysis

## 1. Method Overview

- **Data**: customer reviews and product descriptions for three products (PS5, Stanley tumbler, Jordan sneakers)
- **Chunking**: 88 chunks for PS5, 15 for Stanley, 6 for Jordans
- **Embeddings**: text-embedding-3-large
- **Vector store**: FAISS index per product
- **LLM**: gpt-4o with retrieval-augmented prompts

## 2. Per-Product Visual Understanding

### 2.1 PlayStation 5

**Customer Description Summary:**
Overall, customer perception of the PS5 Pro is mixed. While some users appreciate the enhanced performance and visual improvements, many feel that the high cost is not justified by the benefits provided, especially when compared to the base PS5 model.

**Key Strengths:**
- The PS5 Pro offers noticeable improvements in performance, with higher frame rates and smoother gameplay, especially for games patched for the Pro version.
- Visual enhancements such as improved graphics, lighting, and reflect...

**Key Visual Cues:**
- **Shape**: sleek and compact
- **Dimensions/Size**: similar to normal PS5, only central side fins different
- **Color Palette**: white
- **Branding Elements**: PlayStation logo
- **Distinctive Features**: ultra-sharp 4K visuals, stunning ray tracing, PSSR AI enhancement, 2TB SSD storage

**Comparison with Official Description:**
Customer reviews emphasize practical usage experiences and visual details that may not be fully captured in official product descriptions, such as real-world appearance, material feel, and contextual usage patterns.

### 2.2 Stanley Tumbler

**Customer Description Summary:**
**Overall Customer Perception:**
The Stanley Quencher H2.0 Tumbler is generally well-received by customers, who appreciate its ability to keep beverages cold for extended periods and its aesthetic appeal, particularly the color options. However, some users express dissatisfaction with certain functional aspects and customer service experiences.

**Key Strengths:**
- **Temperature Retention:** The tumbler effectively maintains cold temperatures for up to two days, making it ideal for keeping drin...

**Key Visual Cues:**
- **Shape**: narrow base with a handle
- **Dimensions/Size**: available in 14oz, 20oz, 30oz, 40oz, and 64oz
- **Materials**: recycled BPA-free stainless steel
- **Color Palette**: lilac, pink, darker colors
- **Branding Elements**: Stanley logo
- **Distinctive Features**: FlowState 3-Position Lid, comfort-grip handle, fits most cup holders

**Comparison with Official Description:**
Customer reviews emphasize practical usage experiences and visual details that may not be fully captured in official product descriptions, such as real-world appearance, material feel, and contextual usage patterns.

### 2.3 Jordan Sneakers

**Customer Description Summary:**
**Overall Customer Perception:**
Customers generally perceive the Nike Men's Air Jordan 1 Low Sneaker positively, appreciating its classic style and comfort. However, there are mixed reviews regarding its durability and initial comfort.

**Key Strengths:**
- **Comfort and Fit:** Many customers find the shoes comfortable and true to size, with some noting that they are wide and suitable for daily wear.
- **Style:** The sneakers are praised for their classic, stylish appearance, and are considered...

**Key Visual Cues:**
- **Shape**: high tops
- **Dimensions/Size**: fit like a 8.5 -9, go a half size down
- **Materials**: recycled materials
- **Color Palette**: white, black
- **Branding Elements**: Nike logo
- **Distinctive Features**: old skool look, classic Nike look

**Comparison with Official Description:**
Customer reviews emphasize practical usage experiences and visual details that may not be fully captured in official product descriptions, such as real-world appearance, material feel, and contextual usage patterns.

## 3. Sentiment-Weighted Visuals

### PlayStation 5

**Positive visual aspects:**
  - Improved visuals, lighting, and reflections (high frequency)
  - Stabilized frames and cleaned-up artifacts (medium frequency)
  - Crystal clear fluid higher frame rate (medium frequency)
  - Sharper and smoother edges (medium frequency)
  - Stunning ray tracing (medium frequency)

**Negative visual aspects:**
  - Dark image at 120 Hz (medium frequency)
  - No significant visual upgrade (medium frequency)
  - Lack of noticeable difference (medium frequency)

### Stanley Tumbler

**Positive visual aspects:**
  - Color (high frequency)
  - Handle (medium frequency)
  - Size (medium frequency)

**Negative visual aspects:**
  - Scratches and Dents (high frequency)
  - Handle Durability (medium frequency)
  - Packaging (medium frequency)

### Jordan Sneakers

**Positive visual aspects:**
  - classic look (medium frequency)
  - appearance of quality (medium frequency)
  - stylish design (medium frequency)

**Negative visual aspects:**
  - box condition (medium frequency)
  - initial rigidity (medium frequency)
  - material quality (low frequency)
  - deterioration over time (low frequency)

### Cross-Product Comparison

Across the three products, customers show varying levels of attention to visual details:
- **Color accuracy vs photos**: Customers frequently mention whether products match online images, with color discrepancies being a common complaint.
- **Perceived premium/cheap look**: Visual quality indicators (finish, materials, branding) strongly influence perceived value.
- **Functional aesthetics**: Visual features that impact usability (e.g., grip, size, visibility) receive more detailed feedback than purely aesthetic elements.

## 4. Discussion

**RAG vs Zero-Shot Performance:**
RAG-augmented summaries provide more comprehensive and contextually grounded insights compared to zero-shot approaches. By retrieving relevant chunks based on specific queries, the RAG pipeline captures nuanced customer perspectives that might be missed in a simple sample-based summary. The zero-shot approach relies on a small representative sample, while RAG dynamically selects the most relevant information across the entire corpus.

**Failure Modes and Limitations:**
- **Vague attributes**: Some products (especially Jordans with fewer chunks) produced less detailed visual attribute extractions, likely due to sparse visual descriptions in reviews.
- **Hallucinated details**: The LLM occasionally infers visual attributes not explicitly mentioned in reviews, particularly for products with limited review content.
- **Sparse visual info**: Products with primarily functional reviews (e.g., gaming console) may have fewer visual attribute mentions compared to fashion/appearance-focused products.

