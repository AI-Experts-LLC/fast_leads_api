# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Metrus Energy - Account Enrichment API**: AI-powered prospect discovery and lead enrichment system for healthcare facilities. Automated pipeline that discovers, qualifies, and enriches prospects using LinkedIn search, AI qualification, and Salesforce integration.

**Primary Use Case**: Identify and qualify decision-makers (Directors of Facilities, CFOs, Energy Managers) at healthcare facilities for energy efficiency/infrastructure sales.

## Commands

### Running the Server
```bash
# Development (with auto-reload)
hypercorn main:app --reload

# Production (Railway deployment)
hypercorn main:app --bind "[::]:$PORT"
```

### Testing
```bash
# Test full prospect discovery pipeline
python test_local_linkedin_discovery.py

# Test multiple hospitals
python test_multiple_hospitals.py

# Test single company batch processing
python test_batch_single.py

# Quick validation test
python quick_test.py
```

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Required environment variables in .env:
# - SALESFORCE_DOMAIN, SALESFORCE_USERNAME, SALESFORCE_PASSWORD, SALESFORCE_SECURITY_TOKEN
# - SERPER_API_KEY (Google Search API)
# - OPENAI_API_KEY (GPT-4 for AI qualification)
# - APIFY_API_TOKEN (LinkedIn profile scraping)
```

## Architecture

### Two Prospect Discovery Pipelines

**1. Original Pipeline** (`/discover-prospects`):
```
Search → AI Qualification → AI Validation → LinkedIn Scraping
```
- **Issue**: AI creates/modifies data before getting complete LinkedIn profiles
- **Problem**: Inaccurate persona assignments (e.g., calling interns "highly qualified COOs")

**2. Improved Pipeline** (`/discover-prospects-improved`):
```
Search → Basic Filter → AI Company Filter → LinkedIn Scraping → AI Ranking
```
- **Fix**: Rule-based filtering first, LinkedIn scraping before AI analysis
- **Key**: AI only ranks real data, never creates or modifies prospect information
- See `PROSPECT_DISCOVERY_IMPROVEMENTS.md` for detailed explanation

### Core Service Architecture

```
app/services/
├── search.py                          # Serper API - LinkedIn profile search
├── linkedin.py                        # Apify - LinkedIn profile scraping
├── ai_qualification.py                # OpenAI - Original AI qualification (creates data)
├── improved_ai_ranking.py             # OpenAI - Improved ranking-only AI (preserves data)
├── company_validation.py              # AI employment validation (handles name variations)
├── prospect_discovery.py              # Original pipeline orchestrator
├── improved_prospect_discovery.py     # Improved pipeline orchestrator
├── salesforce.py                      # Salesforce CRM integration
└── credit_enrichment.py               # Additional enrichment services
```

### Key Design Principles

1. **Data Integrity**: The improved pipeline ensures LinkedIn data is never modified by AI - AI only adds ranking scores
2. **Multi-stage Filtering**:
   - Basic filter: Rule-based removal of interns, students, former employees
   - AI company filter: Validates current employment and company name variations
   - Location scoring: Matches prospect location with company location
3. **Parallel Processing**: AI ranking calls are executed concurrently using `asyncio.gather()`
4. **Cost Tracking**: Each pipeline tracks estimated API costs (~$0.57 per company analysis)

### AI Qualification Scoring (100-point scale)

- **Job Title Relevance (35%)**: Director of Facilities = 35-40 pts, CFO = 30-35 pts
- **Decision Authority (25%)**: High authority = 20-25 pts
- **Employment Validation (20%)**: Confidence score with bonus points for high confidence
- **Company Size (15%)**: Large healthcare systems = 12-15 pts
- **Accessibility (5%)**: Active LinkedIn profiles = 8-10 pts
- **Threshold**: ≥70 points = qualified prospect

### Important Implementation Details

**Search Service** (`search.py:68-75`):
- Searches 5 results per target title to balance coverage vs. cost
- Rate limiting: Small delays between searches to respect API limits
- Query format: `{company_name} {title} site:linkedin.com/in`

**Improved AI Ranking** (`improved_ai_ranking.py:56-68`):
- Individual AI calls per prospect (not batch) for better accuracy
- Parallel execution with `asyncio.gather()` for performance
- Returns original prospect data unchanged with added `ai_ranking` field

**Basic Filtering** (`improved_prospect_discovery.py:72-82`):
- Regex patterns for exclusions: `\bintern\b`, `\bstudent\b`, `\bformer\b`
- Senior indicators: `\bdirector\b`, `\bmanager\b`, `\bcfo\b`, `\bcoo\b`
- Location matching using Levenshtein distance for fuzzy matching

## API Endpoints

### Core Functionality
- `POST /discover-prospects` - Original pipeline (has accuracy issues)
- `POST /discover-prospects-improved` - **Use this** - Improved pipeline with accurate data
- `POST /salesforce/connect` - Test Salesforce authentication
- `GET /salesforce/status` - Check connection status
- `POST /lead` - Create Salesforce lead

### Testing/Debug
- `GET /health` - Health check
- `GET /test-services` - Test all API integrations
- `GET /debug/environment` - Environment variable check

## File Organization

- `main.py` - FastAPI application with all endpoint definitions
- `app/services/` - All business logic and external service integrations
- `test_*.py` - Various testing scripts for different scenarios
- `hospital_prospect_testing_*/` - Output directories from test runs (timestamped)
- `.env` - Environment configuration (not in repo)
- `requirements.txt` - Python dependencies (FastAPI, OpenAI, Apify, Salesforce)

## Deployment

**Platform**: Railway (https://railway.app)
- Nixpacks builder automatically detects Python
- Start command: `hypercorn main:app --bind "[::]:$PORT"`
- Environment variables configured in Railway dashboard
- Auto-deploy on git push to main branch

## Common Patterns

**When adding new prospect filters**: Edit `improved_prospect_discovery.py` basic filter or AI filter methods
**When modifying AI scoring**: Update `improved_ai_ranking.py` system prompt with new criteria
**When adding new target titles**: Default titles are in `search.py:54-62`
**When debugging LinkedIn scraping**: Check Apify Actor run logs via `linkedin_service.get_actor_run_status()`
