# L'Oréal Consumer Intelligence

## Project Overview

A consumer intelligence pipeline that identifies product whitespace opportunities for Lancôme by detecting desire language in verified Sephora consumer reviews. The central business question: **what do consumers wish Lancôme made that it doesn't currently offer?**

Built for the L'Oréal USA Commercial Management Trainee role — demonstrating multi-source data analysis, dimensional modeling, and consumer insight generation.

## Pipeline Architecture

```
Kaggle API (Sephora reviews + products)
    → GitHub Actions
    → Snowflake Raw
    → dbt Staging
    → dbt Mart (star schema)
    → Streamlit Dashboard

Web Scrape (Lancôme.com, L'Oréal press releases, beauty editorial)
    → GitHub Actions
    → knowledge/raw/
    → Claude Code
    → knowledge/wiki/
```

## Data Sources

| Source | Type | Schema |
|--------|------|--------|
| Kaggle: Sephora Products and Skincare Reviews (`product_info.csv`) | Kaggle API | `raw.sephora_products` |
| Kaggle: Sephora Products and Skincare Reviews (`reviews_0-250.csv`) | Kaggle API | `raw.sephora_reviews` |
| Lancôme.com, L'Oréal press releases, beauty editorial, Reddit | Web scrape | `knowledge/raw/` |

## Star Schema

- **`fct_reviews`** — review-level grain: `review_id`, `product_id`, `author_id`, `rating`, `review_date`, `is_recommended`, `helpfulness`, `desire_flag`, `desire_text`
- **`dim_products`** — `product_id`, `product_name`, `brand`, `primary_category`, `secondary_category`, `price_tier`
- **`dim_brands`** — `brand_id`, `brand_name`, `division` (Luxe / Consumer Products / Dermatological / Professional)

## Tech Stack

| Layer | Tool |
|-------|------|
| Data Warehouse | Snowflake (AWS US East 1) |
| Transformation | dbt |
| Orchestration | GitHub Actions |
| Dashboard | Streamlit (Streamlit Community Cloud) |
| Knowledge Base | Claude Code |

## Credentials

All secrets stored as environment variables. Never committed to the repo.

Required env vars:
- `KAGGLE_USERNAME`, `KAGGLE_KEY` — Kaggle API credentials
- `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PASSWORD`, `SNOWFLAKE_DATABASE`, `SNOWFLAKE_WAREHOUSE`, `SNOWFLAKE_SCHEMA` — Snowflake connection

## Knowledge Base

Raw sources are stored in `knowledge/raw/` (15+ sources from 3+ sites). Claude Code-generated wiki pages are in `knowledge/wiki/`.

### How to Query the Knowledge Base

When answering questions about this project's domain, follow these conventions:

1. **Start with the wiki.** Read `knowledge/index.md` first to find the most relevant wiki page, then read that page before answering.
2. **Cross-reference raw sources** when a question requires specific evidence (quotes, data points, source attribution). Raw files are named by source and date.
3. **Synthesize across pages.** If a question spans multiple wiki pages (e.g., "what does the brand strategy say about the whitespace themes?"), read all relevant pages before answering.
4. **Be specific.** Cite which wiki page or raw source supports each claim. Do not speculate beyond what the sources say.
5. **Flag gaps.** If the knowledge base doesn't have enough to answer a question, say so explicitly rather than filling in with general knowledge.

### Wiki Structure

| File | Contents |
|------|----------|
| `knowledge/wiki/overview.md` | Lancôme brand positioning, flagship products, L'Oréal division context |
| `knowledge/wiki/consumer-themes.md` | Synthesized desire clusters from raw sources and reviews |
| `knowledge/wiki/whitespace-analysis.md` | Synthesis: unmet consumer needs identified across sources |
| `knowledge/index.md` | Index of all wiki pages with one-line summaries |
