# Setup Checklist - What You Need to Run This Implementation

## ✅ Already Complete
- [x] Project structure created
- [x] All code files implemented
- [x] Python 3.12.0 detected

## 🔧 What You Need to Do

### 1. Install Dependencies

Run this command to install all required packages:

```bash
pip install -r requirements.txt
```

**Key dependencies:**
- `openai` - For DALL·E 3 and embeddings
- `langchain` & `langgraph` - For agentic workflow
- `faiss-cpu` - For vector database
- `sentence-transformers` - For CLIP embeddings
- `beautifulsoup4` - For web scraping
- And others (see requirements.txt)

### 2. Set Up API Keys

You need to create a `.env` file with your API keys:

**Option A: Use the setup script**
```bash
python setup_env.py
```
Then edit `.env` and add your keys.

**Option B: Create manually**
Create a file named `.env` in the project root with:

```
OPENAI_API_KEY=your_actual_openai_key_here
SDXL_API_KEY=your_actual_sdxl_key_here
```

**Where to get API keys:**
- **OpenAI API Key:** https://platform.openai.com/api-keys
  - Needed for: DALL·E 3 image generation, text-embedding-3-large embeddings, GPT-4o for analysis
- **SDXL API Key:** https://platform.stability.ai/ (Stability AI)
  - Alternative: You can use other SDXL providers (Replicate, etc.) - just update `sdxl_generator.py` accordingly

### 3. Verify Installation

Test that everything is installed correctly:

```bash
python -c "import openai, faiss, langgraph, sentence_transformers; print('✓ All core dependencies installed')"
```

### 4. Run the Pipeline

**Full pipeline (recommended):**
```bash
python main.py --all
```

**Or step by step:**
```bash
# Step 1: Scrape data
python main.py --step scrape

# Step 2: Build RAG indexes
python main.py --step rag

# Step 3: Run analysis
python main.py --step analyze

# Step 4: Generate images
python main.py --step images

# Step 5: Compare images
python main.py --step compare

# Step 6: Full workflow
python main.py --step workflow
```

## 📋 Pre-Run Checklist

Before running, make sure you have:

- [ ] Python 3.8+ installed (you have 3.12.0 ✓)
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created with API keys
- [ ] OpenAI API key with:
  - Access to GPT-4o (or GPT-4-turbo)
  - Access to DALL·E 3
  - Access to text-embedding-3-large embeddings
  - Sufficient credits/quota
- [ ] SDXL API key (Stability AI or alternative) with sufficient credits
- [ ] Internet connection (for scraping Amazon and API calls)

## 💰 Estimated Costs

**OpenAI API:**
- Embeddings: ~$0.13 per 1M tokens (text-embedding-3-large)
- GPT-4o: ~$5-15 per 1M input tokens (for analysis)
- DALL·E 3: $0.040 per image (1024x1024)

**For 3 products with 400 reviews each:**
- Embeddings: ~$1-5 (depends on review length)
- Analysis: ~$5-20 (multiple LLM calls per product)
- Images: ~$1.20 (5 images × 3 prompts × 2 models = 30 images × $0.04)

**Total estimated: ~$10-30 for full pipeline**

**SDXL API:**
- Varies by provider (Stability AI, Replicate, etc.)
- Typically $0.01-0.05 per image

## 🚨 Common Issues & Solutions

### Issue: "OPENAI_API_KEY not found"
**Solution:** Make sure `.env` file exists in project root and contains `OPENAI_API_KEY=...`

### Issue: "ModuleNotFoundError: No module named 'X'"
**Solution:** Run `pip install -r requirements.txt` again

### Issue: "FAISS import error"
**Solution:** Make sure you installed `faiss-cpu` (not `faiss` which requires CUDA)

### Issue: "Amazon scraping blocked"
**Solution:** 
- Amazon may block requests - the code includes delays and proper headers
- If issues persist, you may need to use a proxy or different approach
- Consider using Amazon Product Advertising API as alternative

### Issue: "SDXL API error"
**Solution:**
- Verify your SDXL_API_KEY is correct
- Check if you're using Stability AI or another provider
- Update `sdxl_generator.py` if using a different API endpoint

### Issue: "Out of API credits"
**Solution:**
- Check your OpenAI/Stability AI account balance
- Reduce number of images per prompt (edit `images_per_prompt` parameter)
- Process one product at a time instead of all three

## 🎯 Quick Start (Minimal Setup)

If you just want to test quickly:

1. **Install dependencies:**
   ```bash
   pip install openai langchain langgraph faiss-cpu sentence-transformers beautifulsoup4 requests pillow numpy tiktoken python-dotenv
   ```

2. **Create `.env` file:**
   ```
   OPENAI_API_KEY=sk-...
   SDXL_API_KEY=sk-...
   ```

3. **Test with one product:**
   ```bash
   python main.py --product-id B0CKZGY5B6
   ```

## 📝 Notes

- The pipeline will create all necessary directories automatically
- Data files will be saved in `data/` directory
- Generated images in `image_generation/outputs/`
- Reports in `report/` directory
- You can run individual steps if the full pipeline fails at any point

## ✅ Ready to Run?

Once you've completed the checklist above, you're ready to run:

```bash
python main.py --all
```

This will process all three products end-to-end and generate the final report.


