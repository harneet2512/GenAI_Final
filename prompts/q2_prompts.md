# Q2 Prompt Log

This file records every prompt template used in the Q2 RAG + LLM pipeline.

## Zero-shot summary
System:
```
You analyze products without external retrieval.
```
User:
```
You are an expert product analyst. Using the product description and representative customer reviews below,
write a concise yet rich summary covering:
- what the product is and who it's for
- key functional + visual characteristics
- standout positives and any notable caveats

Product description:
{description_text}

Representative customer snippets:
{sample_reviews}
```

## RAG summary
System:
```
You synthesize RAG contexts into high-signal product summaries.
```
User:
```
Use the retrieved context below to produce a grounded summary that merges description + review insights.
Highlight visual, functional, and experiential takeaways. Keep it around 4-5 paragraphs.

Context:
{retrieved_context}
```

## Visual attributes extraction
System:
```
You are a precise product analyst that extracts structured data from product reviews. Always return valid JSON.
```
User:
```
You are an expert product analyst. Using ONLY the context below, extract structured visual attributes
for the product. When information is missing, use "N/A" for strings and [] for lists.

Context:
{retrieved_context}

Return a JSON object with the following schema:
{
  "product_name": "string",
  "shape": "string",
  "dimensions_or_size_impression": "string",
  "materials": "string",
  "color_palette": ["list of colors"],
  "branding_elements": ["logos or brand marks"],
  "distinctive_features": ["unique visual traits"],
  "usage_contexts": ["notable usage scenarios"],
  "positive_visual_themes": ["what customers like visually"],
  "negative_visual_themes": ["visual complaints"]
}

Return ONLY valid JSON. Do not include explanations.
```

## Visual sentiment extraction
System:
```
You are a sentiment analyst specializing in visual product features. Always return valid JSON.
```
User:
```
Analyze the visual/appearance themes in the customer review context below. Identify
which visual attributes are spoken about positively vs negatively. When you make a
claim, reference how customers talk about it (brief quote or paraphrase). Classify
frequency qualitatively (high/medium/low).

Context:
{retrieved_context}

Return JSON:
{
  "positive_visual_features": [
    {"feature": "...", "mentions": "...", "frequency": "high/medium/low"}
  ],
  "negative_visual_features": [
    {"feature": "...", "mentions": "...", "frequency": "high/medium/low"}
  ]
}

Focus on visual attributes only. Return ONLY valid JSON.
```

## Additional notes
- Queries used for RAG retrieval are logged inside the code (see `retrieve_chunks` call sites).
- Every prompt above is invoked for each product (`ps5`, `stanley`, `jordans`) during the Q2 pipeline run.

