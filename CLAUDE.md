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

# Check if server is running
curl http://localhost:8000/health
```

### Testing Hybrid Pipeline (New Lead Discovery)
```bash
# Test full 4-step hybrid pipeline (Serper + Bright Data)
python test_hybrid_pipeline.py

# Results will be queued to /pending-updates?record_type=Lead
# View in dashboard at /dashboard
```

### Testing
```bash
# Test 3-step pipeline (single hospital)
python tests/test_three_step_discovery.py

# Test batch processing (2 hospitals)
python tests/test_batch_three_step.py

# Test full batch with CSV export (all hospitals)
python tests/batch_all_hospitals_full_export.py

# Legacy tests (may be outdated)
python tests/test_local_linkedin_discovery.py
python tests/test_multiple_hospitals.py
python tests/batch_prospect_discovery.py

# Test enrichment endpoints
python tests/test_enrichment_api.py --account <account_id> --api-key <key>
```

### API Testing (Local)
```bash
# Test 3-step pipeline - Step 1
curl -X POST "http://127.0.0.1:8000/discover-prospects-step1" \
  -H "Content-Type: application/json" \
  -d '{"company_name": "Mayo Clinic", "company_city": "Rochester", "company_state": "Minnesota"}'

# Test 3-step pipeline - Step 2 (use linkedin_urls from Step 1)
curl -X POST "http://127.0.0.1:8000/discover-prospects-step2" \
  -H "Content-Type: application/json" \
  -d '{"linkedin_urls": ["..."], "company_name": "Mayo Clinic", "company_city": "Rochester", "company_state": "Minnesota"}'

# Test 3-step pipeline - Step 3 (use enriched_prospects from Step 2)
curl -X POST "http://127.0.0.1:8000/discover-prospects-step3" \
  -H "Content-Type: application/json" \
  -d '{"enriched_prospects": [...], "company_name": "Mayo Clinic", "min_score_threshold": 65}'

# Test improved discovery pipeline (local only - times out on Railway)
curl -X POST "http://127.0.0.1:8000/discover-prospects-improved" \
  -H "Content-Type: application/json" \
  -d '{"company_name": "Mayo Clinic", "company_city": "Rochester", "company_state": "Minnesota"}'

# Test Salesforce connection
curl http://localhost:8000/salesforce/status

# Test all services
curl http://localhost:8000/test-services
```

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Required environment variables in .env:
# Salesforce Configuration
SALESFORCE_DOMAIN=https://test.salesforce.com
SALESFORCE_USERNAME=your_username
SALESFORCE_PASSWORD=your_password
SALESFORCE_SECURITY_TOKEN=your_token

# Prospect Discovery API Keys (Required)
SERPER_API_KEY=your_serper_key          # Google Search API for LinkedIn
OPENAI_API_KEY=your_openai_key          # AI Qualification & Enrichment
APIFY_API_TOKEN=your_apify_token        # LinkedIn Profile Scraping

# Credit Enrichment (EDF-X) - Optional
EDFX_USERNAME=your_edfx_username        # Company credit ratings
EDFX_PASSWORD=your_edfx_password        # Probability of default data

# API Security (Required for enrichment endpoints)
API_KEY=your-secure-api-key             # Protect /enrich/* endpoints

# Dashboard Password (Required for web UI access)
DASHBOARD_PASSWORD=your-dashboard-password  # Password for /dashboard, /enrich, /logs/view
# Alternative: LOGS_PASSWORD (legacy, falls back to this if DASHBOARD_PASSWORD not set)

# Email Validation (Optional)
ZEROBOUNCE_API_KEY=your_zerobounce_key  # Email deliverability validation

# ZoomInfo Integration (Optional, not currently active)
ZOOMINFO_CLIENT_ID=your_client_id       # Contact validation
ZOOMINFO_CLIENT_SECRET=your_secret      # Requires OAuth setup

# Optional Settings
ENVIRONMENT=development
PORT=8000
```

## Architecture

### Prospect Discovery Pipelines

**✅ THREE-STEP PIPELINE (RECOMMENDED)** - `/discover-prospects-step1/2/3`
```
Step 1: Search & Filter (30-90s)  → LinkedIn search + basic filtering + AI title scoring
Step 2: Scrape & Validate (15-35s) → Profile scraping + company/employment validation
Step 3: AI Ranking (5-25s)        → AI scoring + qualification (≥65 threshold)
Total: 50-150s (~1-2.5 minutes)
```
- **Status**: Production-ready, 69% success rate (October 2025 test)
- **Use Case**: All production workloads on Railway
- **Benefits**: Avoids timeout, accurate data, comprehensive validation
- **Key Fixes** (October 2025):
  - Company name matching: "St." ↔ "Saint" normalization
  - LinkedIn scraping: Fallback company extraction from experience array
  - Employment validation: Enhanced with company name variations
  - State abbreviation handling: Removes " MT", " ID", etc. from company names
- **Documentation**: See `THREE_STEP_PIPELINE.md`

**🆕 HYBRID PIPELINE (NEW LEAD DISCOVERY)** - `/discover-leads-step1/2/3/4`
```
Step 1: Parallel Search (30-60s)    → Run Serper AND Bright Data searches simultaneously
Step 2: Deduplicate + Enrich (15-30s) → Prefer Bright Data data, scrape Serper-only via Apify
Step 3: AI Ranking (10-20s)        → AI scoring + qualification (≥65 threshold)
Step 4: Queue to Pending (1-2s)    → Add leads to PendingUpdates for approval
Total: 56-112s (~1-2 minutes)
```
- **Status**: Production-ready, maximizes coverage with dual sources
- **Use Case**: Discover NEW leads and queue them for manual approval before Salesforce import
- **Benefits**:
  - **Maximum coverage**: Combines web search (Serper) + dataset filtering (Bright Data)
  - **Smart deduplication**: Prefers Bright Data's richer profiles when duplicates found
  - **Approval workflow**: Leads queued to `/pending-updates?record_type=Lead` for review
  - **Dashboard integration**: View and approve leads at `/dashboard`
- **Key Features**:
  - Parallel API calls for speed (Serper + Bright Data run simultaneously)
  - Name-based deduplication with fuzzy matching
  - Fallback enrichment for Serper-only results via Apify scraping
  - Automatic Lead record creation in PendingUpdates database
- **Test Script**: `python test_hybrid_pipeline.py`
- **Service**: `app/services/hybrid_prospect_discovery.py`

**🔍 OPTIONAL: ZOOMINFO VALIDATION** - `/discover-prospects-zoominfo`
- **What it does**: Validates email/phone contact information after Step 3
- **Status**: Optional enhancement, gracefully skips if not configured
- **Use Case**: Contact validation before outreach campaigns

**⚠️ DEPRECATED PIPELINES** (Maintained for backward compatibility)

1. **Original Pipeline** (`/discover-prospects`):
   - **Issue**: AI creates/modifies data before LinkedIn scraping
   - **Status**: Deprecated, use 3-step pipeline instead

2. **Improved Pipeline** (`/discover-prospects-improved`):
   - **Issue**: Times out on Railway (>5 minute limit)
   - **Status**: Deprecated for production, works locally only

### Core Service Architecture

```
app/services/
├── search.py                              # Serper API - LinkedIn profile search
├── linkedin.py                            # Apify - LinkedIn profile scraping
├── brightdata_prospect_discovery.py       # Bright Data LinkedIn dataset filtering
├── hybrid_prospect_discovery.py           # 🆕 Hybrid pipeline (Serper + Bright Data)
├── ai_qualification.py                    # OpenAI - Original AI qualification (creates data)
├── improved_ai_ranking.py                 # OpenAI - Improved ranking-only AI (preserves data)
├── company_validation.py                  # AI employment validation (handles name variations)
├── company_name_expansion.py              # Handles company name variations (aliases)
├── prospect_discovery.py                  # Original pipeline orchestrator
├── improved_prospect_discovery.py         # Improved pipeline orchestrator
├── three_step_prospect_discovery.py       # 3-step pipeline for Railway (avoids timeout)
├── zoominfo_validation.py                 # ZoomInfo contact validation (Step 4, disabled)
├── pending_updates.py                     # 🆕 PendingUpdates service (queue leads/updates)
├── salesforce.py                          # Salesforce CRM integration
├── credit_enrichment.py                   # EDF-X credit rating/PD enrichment
└── enrichment.py                          # Account/Contact enrichment orchestrator
```

**Supporting Files:**
- `app/auth.py` - API key authentication for enrichment endpoints
- `main.py` - FastAPI application with all endpoint definitions
- `batch_prospect_discovery.py` - Batch processing script for multiple hospitals

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

**Company Name Matching** (`three_step_prospect_discovery.py:665-725`):
- Normalizes "St." ↔ "Saint" variations before comparison
- Removes healthcare suffixes: "Medical Center", "Hospital", "Health System"
- Removes state abbreviations: " MT", " ID", " CA", etc.
- Collapses multiple whitespaces after suffix removal
- Generates multiple company name variations for matching

**LinkedIn Company Extraction** (`linkedin.py:180-185`):
- Extracts company from `companyName` field if available
- Falls back to most recent experience if `companyName` is null
- Fixes issue where Apify returns null company despite valid experience data

## API Endpoints

### Web Dashboards (Password Protected)
All HTML dashboards require password authentication via session cookies.

- `GET /dashboard/login` - Login page for dashboard access
- `POST /dashboard/auth` - Authenticate with password (returns session cookie)
- `GET /dashboard` - Main dashboard with system status and links
- `GET /enrich` - Enrichment dashboard (manual account/contact enrichment)
- `GET /logs/view` - API request logs viewer with real-time monitoring

**Authentication Flow:**
1. Navigate to any dashboard URL (e.g., `/dashboard`, `/enrich`, `/logs/view`)
2. If not authenticated, redirected to `/dashboard/login`
3. Enter password (set via `DASHBOARD_PASSWORD` environment variable)
4. Receive session cookie valid for 24 hours
5. Access all dashboards without re-authentication

**Environment Variable:**
- `DASHBOARD_PASSWORD` - Password for all web dashboards (default: "changeme")
- Falls back to `LOGS_PASSWORD` if `DASHBOARD_PASSWORD` not set

### Prospect Discovery

**🆕 HYBRID PIPELINE (NEW LEAD DISCOVERY)**
- `POST /discover-leads-step1` - Step 1: Parallel Search (Serper + Bright Data)
  - Required: `company_name`, `company_state`
  - Optional: `parent_account_name`, `target_titles`, `company_city`
  - Time: 30-60 seconds
- `POST /discover-leads-step2` - Step 2: Deduplicate + Enrich
  - Required: `serper_prospects`, `brightdata_prospects`, `company_name`
  - Optional: `company_city`, `company_state`
  - Time: 15-30 seconds
- `POST /discover-leads-step3` - Step 3: AI Ranking
  - Required: `enriched_prospects`, `company_name`
  - Optional: `min_score_threshold` (default: 65), `max_prospects` (default: 10)
  - Time: 10-20 seconds
- `POST /discover-leads-step4` - Step 4: Queue to PendingUpdates
  - Required: `qualified_prospects`, `company_name`
  - Optional: `company_account_id` (Salesforce Account ID to link)
  - Time: 1-2 seconds

**✅ THREE-STEP PIPELINE (RECOMMENDED)**
- `POST /discover-prospects-step1` - Step 1: Search & Filter
  - Required: `company_name`
  - Optional: `target_titles`, `company_city`, `company_state`
  - Time: 30-90 seconds
- `POST /discover-prospects-step2` - Step 2: Scrape & Validate
  - Required: `linkedin_urls`, `company_name`
  - Optional: `company_city`, `company_state`, `location_filter_enabled`
  - Time: 15-35 seconds
- `POST /discover-prospects-step3` - Step 3: AI Ranking
  - Required: `enriched_prospects`, `company_name`
  - Optional: `min_score_threshold` (default: 65), `max_prospects` (default: 10)
  - Time: 5-25 seconds

**🔍 OPTIONAL ZOOMINFO VALIDATION**
- `POST /discover-prospects-zoominfo` - ZoomInfo Contact Validation
  - Required: `qualified_prospects`, `company_name`
  - Status: Optional, gracefully skips if not configured
  - Time: 10-20 seconds

**⚠️ DEPRECATED PIPELINES** (Backward compatibility only)
- `POST /discover-prospects` - Original pipeline (⚠️ deprecated, AI accuracy issues)
- `POST /discover-prospects-improved` - Improved pipeline (⚠️ deprecated, Railway timeout)

### Salesforce Integration
- `POST /salesforce/connect` - Test Salesforce authentication
- `GET /salesforce/status` - Check connection status
- `GET /salesforce/test-account` - Test account query
- `GET /salesforce/test-lead` - Test lead creation
- `POST /lead` - Create Salesforce lead
- `GET /account/{account_id}` - Get account details

### Enrichment (Requires X-API-Key header)
- `POST /enrich/account` - Enrich Salesforce account with company data
  - Required: `account_id`
  - Optional: `overwrite`, `include_financial`, `credit_only`
- `POST /enrich/contact` - Enrich Salesforce contact with personal data
  - Required: `contact_id`
  - Optional: `overwrite`, `include_linkedin`

### Credit Enrichment (EDF-X)
- `POST /credit/test-connection` - Test EDF-X API connection
- `POST /credit/enrich-company` - Get credit rating for single company
- `POST /credit/batch-enrich` - Batch enrich multiple companies

### LinkedIn Scraping
- `POST /linkedin/scrape-profiles` - Scrape LinkedIn profiles directly (max 10)
- `GET /linkedin/test` - Test LinkedIn scraping service

### Testing/Debug
- `GET /health` - Health check
- `GET /version` - API version information
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
**When adding new enrichment fields**: Update `enrichment.py` service and Salesforce field mappings
**When testing batch processing**: Use `batch_prospect_discovery.py` with `TEST_MODE=True` for single hospital tests

## Important Notes

**Authentication**: Enrichment endpoints (`/enrich/*`) require `X-API-Key` header. Set `API_KEY` environment variable. See `AUTHENTICATION.md` for details.

**API Costs** (approximate per company):
- Serper search: ~$0.05 (5 titles × 5 results × $0.002)
- OpenAI AI ranking: ~$0.45 (15 prospects × ~$0.03)
- Apify LinkedIn scraping: ~$0.07 (15 prospects × $0.0047)
- **Total**: ~$0.57 per company analysis

**Rate Limits**:
- Serper: 5,000 searches/month on $50 plan
- OpenAI: GPT-4 standard rate limits apply
- Apify: $49/month + usage-based pricing

**Output Files**: Test scripts generate timestamped output directories (`hospital_prospect_testing_*/`) with JSON and summary files. Batch processing generates CSV and JSON files in project root.
