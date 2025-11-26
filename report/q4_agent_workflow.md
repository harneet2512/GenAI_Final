# Q4: Agentic Workflow

## LangGraph Architecture

The workflow is implemented using LangChain and LangGraph, with a state-based architecture that orchestrates multiple specialized agents.

## Workflow Graph

```
review_analyzer → prompt_constructor → image_generator → evaluation → report
```

### State Structure

The `WorkflowState` (defined in `agent_workflow/utils/state.py`) includes:
- `product_id`: Product identifier
- `product_data`: Scraped product information
- `processed_reviews`: Cleaned review data
- `faiss_index_path`: Path to vector index
- `summary`: LLM-generated summary
- `structured_attributes`: Extracted visual attributes
- `sentiment_features`: Sentiment-visual feature mappings
- `prompts`: Image generation prompts
- `generated_images_dalle`: DALL·E 3 image metadata
- `generated_images_sdxl`: SDXL image metadata
- `evaluation_results`: Image comparison metrics
- `report_snippet`: Final report content
- `errors`: Error log (append-only)

## Agent Responsibilities

### 1. Review Analyzer Agent
**File:** `agent_workflow/agents/review_analyzer_agent.py`

**Responsibilities:**
- Load product data and processed reviews
- Initialize FAISS retriever
- Run full LLM analysis pipeline
- Extract structured attributes and sentiment features
- Generate summaries (holistic, RAG-augmented, self-refined)

**Outputs to State:**
- `product_data`
- `processed_reviews`
- `faiss_index_path`
- `summary`
- `structured_attributes`
- `sentiment_features`

### 2. Prompt Constructor Agent
**File:** `agent_workflow/agents/prompt_constructor_agent.py`

**Responsibilities:**
- Build image generation prompts from analysis
- Generate 1-3 prompt variants per product
- Save prompts for reference

**Outputs to State:**
- `prompts`

### 3. Image Generator Agent
**File:** `agent_workflow/agents/image_generator_agent.py`

**Responsibilities:**
- Generate images using DALL·E 3 (5 per prompt)
- Generate images using SDXL (5 per prompt)
- Handle API errors gracefully
- Store image metadata

**Outputs to State:**
- `generated_images_dalle`
- `generated_images_sdxl`

### 4. Evaluation Agent
**File:** `agent_workflow/agents/evaluation_agent.py`

**Responsibilities:**
- Compare DALL·E images vs ground truth
- Compare SDXL images vs ground truth
- Compute similarity metrics (CLIP, color, SSIM)
- Aggregate statistics per model

**Outputs to State:**
- `evaluation_results`

### 5. Report Agent
**File:** `agent_workflow/agents/report_agent.py`

**Responsibilities:**
- Assemble comprehensive report snippet
- Summarize key visual attributes
- Compare model performance
- Identify notable findings
- Document potential hallucinations/mismatches
- Save report to file

**Outputs to State:**
- `report_snippet`

## Workflow Execution

### Entry Point

```python
from agent_workflow.graph import run_full_workflow

final_state = run_full_workflow(product_id="B0CKZGY5B6")
```

### Execution Flow

1. **Initialize:** Create initial state with product_id
2. **Review Analysis:** Analyze product and reviews
3. **Prompt Construction:** Build image generation prompts
4. **Image Generation:** Generate images with both models
5. **Evaluation:** Compare images vs ground truth
6. **Report Generation:** Assemble final report snippet

### Error Handling

- Errors are captured in `state["errors"]` list
- Workflow continues even if individual steps fail
- Each agent handles errors gracefully and logs them

## Output Files

Per-product workflow outputs:
- `report/workflow_outputs/{product_id}_snippet.md`

## Key Features

1. **Modular Agents:** Each agent is independently testable
2. **State Management:** Centralized state with type safety
3. **Error Resilience:** Workflow continues despite individual failures
4. **Reproducibility:** All steps are logged and traceable
5. **Extensibility:** Easy to add new agents or modify workflow

## Graph Visualization

The workflow can be visualized as a linear pipeline:

```
[Start] → [Review Analyzer] → [Prompt Constructor] → 
[Image Generator] → [Evaluation] → [Report] → [End]
```

Each node:
- Receives the full state
- Updates relevant state fields
- Passes state to next node
- Handles errors internally

## Benefits of Agentic Approach

1. **Separation of Concerns:** Each agent has a single responsibility
2. **Testability:** Agents can be tested independently
3. **Maintainability:** Changes to one agent don't affect others
4. **Debugging:** Easy to identify which agent caused issues
5. **Scalability:** Can parallelize or add conditional logic easily


