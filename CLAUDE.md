# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important: Always Use Virtual Environment

**ALWAYS activate the virtual environment before running any Python or pip commands:**
```bash
source venv/bin/activate
```

Never install packages or run scripts without activating venv first.

## Project Overview

jobs_agent is an LLM-powered job search assistant that fetches live job listings from multiple sources (Adzuna API and JobSpy), evaluates candidates against job postings using OpenAI's GPT-4o-mini, and produces ranked CSV outputs. It uses LangChain for LLM workflows and Chroma for vector embeddings of the user's profile.

## Commands

```bash
# Setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Build profile vector index (one-time, or when profile.md changes)
python -c "from src.memory import build_profile_index; build_profile_index()"

# Fetch jobs from Adzuna
python -m src.run_fetch

# Rank jobs using LLM
python -m src.rank_llm

# Run tests
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/test_adzuna.py -v
```

## Architecture

**Data Pipeline:**
```
profile.md → [build_profile_index] → Chroma vector store
                                           ↓
sources.yaml → [run_fetch] → Adzuna API / JobSpy → jobs.csv
                                           ↓
                    [rank_llm Pass 1] ← profile retrieval
                           ↓
                    jobs_ranked.csv
                           ↓
              [fetch_url enrichment for top K]
                           ↓
                    [rank_llm Pass 2]
                           ↓
                    jobs_top_k.csv
```

**Key Modules:**
- `src/run_fetch.py` - Entry point for fetching and normalizing jobs from Adzuna
- `src/rank_llm.py` - Entry point for LLM ranking (two-pass: initial + enriched top-K)
- `src/memory.py` - Chroma vector store for profile embeddings (chunks profile.md, retrieves top-4 matches)
- `src/fetchers/adzuna.py` - Adzuna API wrapper with pagination and rate limiting
- `src/fetchers/jobspy.py` - JobSpy wrapper (scrapes LinkedIn, Indeed, Glassdoor, ZipRecruiter)
- `src/enrich.py` - SHA1-based URL caching for job descriptions
- `src/tools/fetch_url.py` - HTML scraper that extracts clean text (max 8k chars)
- `src/agent.py` - Placeholder for future LangChain agent implementation

**Configuration:**
- `configs/sources.yaml` - Search queries with `source: adzuna` or `source: jobspy`, query params (what_or, what_exclude, where, distance, search_term, site_name), and global params
- `.env` - Required: `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`

**Data Files:**
- `data/profile.md` - User resume/profile in Markdown
- `data/jobs.csv` - Normalized job listings
- `data/jobs_ranked.csv` - Jobs with LLM scores
- `data/jobs_top_k.csv` - Top jobs re-ranked with full descriptions

## Key Patterns

- LLM ranking returns structured JSON with fields: score (0-100), why, level_fit, tech_fit, location_fit, relevance_tags, summary, concerns
- Vector retrieval uses 800-char chunks with 100-char overlap
- Adzuna fetcher has 0.2s sleep between paginated requests
- URL fetcher truncates to 8000 chars and strips nav/footer/script elements
