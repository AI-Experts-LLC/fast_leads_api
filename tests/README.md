# Test Scripts

This directory contains test scripts for the Fast Leads API prospect discovery pipeline.

## Railway Deployment Tests

### test_bozeman_health_railway.py

Tests the complete 3-step prospect discovery pipeline against the Railway deployment.

**Target:** Bozeman Health Deaconess Regional Medical Center (Bozeman, MT)

**Usage:**
```bash
python tests/test_bozeman_health_railway.py
```

**Outputs:**
- `bozeman_health_prospects_YYYYMMDD_HHMMSS.csv` - Qualified prospects in CSV format
- `bozeman_health_full_results_YYYYMMDD_HHMMSS.json` - Complete pipeline results

**What it tests:**
1. **Step 1:** LinkedIn search and filtering (basic + AI title filter)
2. **Step 2:** Profile scraping and advanced filtering
3. **Step 3:** AI ranking and final selection

**Expected Duration:** 3-5 minutes (depends on number of prospects)

**CSV Columns:**
- rank, name, job_title, company, location, connections
- email, mobile_number, ai_score, ai_reasoning
- linkedin_url, headline, summary
- total_experience_years, professional_authority_score
- skills_count, top_skills

## Local Development Tests

### batch_prospect_discovery.py
Batch processing script for testing multiple hospitals at once.

### test_local_linkedin_discovery.py
Tests the original monolithic prospect discovery endpoint locally.

### test_multiple_hospitals.py
Tests multiple hospitals with the improved pipeline.

### test_enrichment_api.py
Tests the account/contact enrichment endpoints with authentication.

## Quick Tests

### quick_test.py
Quick validation test for basic functionality.

### test_title_filter_*.py
Tests for the AI title filtering functionality.

## Hospital-Specific Tests

Tests for specific hospitals that were problematic:
- `test_medstar.py` / `test_medstar_improved.py`
- `test_mercy_springfield.py`
- `test_providence_medford.py`
- `test_st_vincent_direct.py`

## Utility Scripts

### compare_medstar_results.py
Compares results between different pipeline versions.

### display_medstar_results.py
Displays formatted results from test runs.

### show_search_queries.py
Shows the search queries being generated.

## Running Tests

Most test scripts can be run directly:
```bash
python tests/<test_name>.py
```

Some scripts require environment variables to be set in `.env`:
- `SERPER_API_KEY` - For LinkedIn search
- `OPENAI_API_KEY` - For AI ranking/filtering
- `APIFY_API_TOKEN` - For LinkedIn scraping
- `API_KEY` - For enrichment endpoint authentication
