# Generative AI - Product Review to Image Agentic Pipeline

An agentic workflow that processes product reviews from local HTML files, extracts visual attributes using LLM analysis, and generates AI images using DALL·E 3 and SDXL.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up API Keys

Create a `.env` file in the project root with your API keys:

```env
OPENAI_API_KEY=your_openai_api_key_here
SDXL_API_KEY=your_sdxl_api_key_here
```

**Get your keys:**
- **OpenAI API Key**: https://platform.openai.com/api-keys (for DALL·E 3 and LLM analysis)
- **SDXL API Key**: https://platform.stability.ai/ (for SDXL image generation)

### 3. Add Product Review HTML Files

Place your product review HTML files in:
```
agent_app/data/html/{product_id}/*.html
```

Supported products: `ps5`, `stanley`, `jordans`

### 4. Run the Streamlit UI

**One command to run everything:**

```bash
streamlit run agent_app/ui/streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

## 📋 How It Works

The agentic pipeline consists of several specialized agents working together:

### 1. **Data Preparation Agent**
- Reads local HTML review files from `agent_app/data/html/{product_id}/`
- Parses reviews using BeautifulSoup
- Generates structured JSON output
- **Idempotent**: Skips if HTML files haven't changed

### 2. **Corpus & Index Agent**
- Builds a corpus from parsed reviews
- Chunks text for better retrieval
- Creates FAISS vector embeddings
- Builds a searchable index
- **Idempotent**: Rebuilds only if inputs changed

### 3. **Q2 Analysis Agent**
- Uses OpenAI GPT to analyze reviews
- Extracts visual attributes (shape, materials, colors, usage contexts)
- Generates sentiment analysis
- Outputs: `analysis/{product_id}_analysis.json` and `analysis/{product_id}_summary.md`
- **Idempotent**: Re-runs only if inputs changed

### 4. **Q2 Validation Agent**
- Validates Q2 outputs for completeness
- Checks for required visual attributes

### 5. **Q3 Image Generation Agent**
- Constructs prompts from Q2 visual attributes
- Generates images using:
  - **DALL·E 3** (OpenAI) - 3 images per product
  - **SDXL** (Stability AI) - 3 images per product
- Handles rate limits gracefully (SDXL fail-fast)
- Preserves previous images if generation fails
- Outputs: `images/q3/{product_id}/manifest.json`

### Input Fingerprinting

The pipeline uses **HTML fingerprinting** to detect changes:
- Computes SHA-256 hash of HTML file metadata (filename, size, last modified time)
- Stores fingerprint in `agent_app/data/state/{product_id}_input.json`
- Only re-runs agents if inputs have changed

## 🎯 Using the Streamlit UI

1. **Select a Product**: Choose from PS5, Stanley, or Jordans in the sidebar
2. **Click "Run Pipeline"**: This triggers the full agentic workflow
3. **View Results**:
   - **Run Summary**: Shows pipeline status, run ID, and execution logs
   - **Q2 Analysis Summary**: Visual attributes extracted from reviews
   - **Q3 Generated Images**: AI-generated product images (DALL·E 3 and SDXL)
   - **AI vs Real Comparison**: Comparison report (if available)

### Image Display Logic

- **Current Run Success**: Shows images from the current run
- **SDXL Rate Limit**: Falls back to previous successful SDXL images with a clear message
- **Partial Success**: Shows successful images from current run
- **No Images**: Shows warning and falls back to previous successful run

## 📁 Project Structure

```
GenAI_Final/
├── agent_app/              # New agentic workflow (Q4)
│   ├── core/              # Core utilities (HTML loading, parsing, paths)
│   ├── agents/            # Agent nodes and LangGraph workflow
│   ├── ui/                # Streamlit UI
│   └── data/              # Local data (HTML, raw reviews, state)
├── rag_pipeline/          # Q1: Corpus, chunking, embeddings, FAISS
├── analysis/              # Q2: LLM analysis, Q3: Image generation
├── images/q3/             # Generated images and manifests
└── .env                   # API keys (NOT committed to git)
```

## 🔒 Security

- **`.env` file is gitignored** - Your API keys will never be committed
- **Setup scripts are gitignored** - Files like `set_openai_key.py` are excluded
- **Generated images are gitignored** - Large files are not committed
- **HTML files are gitignored** - Local review data stays local

## 🛠️ Alternative: CLI Usage

You can also run the pipeline via CLI:

```bash
python -m agent_app.agents.cli --product ps5
python -m agent_app.agents.cli --product stanley
python -m agent_app.agents.cli --product jordans
```

## 📊 Output Files

- **Q2 Analysis**: `analysis/{product_id}_analysis.json`, `analysis/{product_id}_summary.md`
- **Q3 Images**: `images/q3/{product_id}/manifest.json`, `images/q3/{product_id}/{model}/{variant}/`
- **State**: `agent_app/data/state/{product_id}_input.json` (fingerprints)

## 🐛 Troubleshooting

**No images showing?**
- Check that the pipeline completed successfully (see Execution Logs)
- Verify API keys are set correctly
- Check that Q2 analysis succeeded (required for Q3)

**SDXL rate limits?**
- The pipeline will fail-fast and show previous successful SDXL images
- DALL·E 3 images will still be generated

**HTML files not found?**
- Ensure HTML files are in `agent_app/data/html/{product_id}/`
- Files must have `.html` extension

## 📝 Notes

- The pipeline is **idempotent**: Running it multiple times with unchanged inputs will skip up-to-date steps
- **First run** will take longer (builds corpus, generates images)
- **Subsequent runs** with unchanged HTML will be fast (skips up-to-date steps)
- **Changing HTML files** triggers a full re-run

## 🤝 Contributing

This is a class assignment project. Please ensure:
- No API keys are committed
- All sensitive data is in `.gitignore`
- Follow the existing code structure

## 📄 License

This project is for educational purposes.
