# 🔄 Three-Step Prospect Discovery Pipeline

**Production-Ready Pipeline for Railway Deployment**

The three-step pipeline breaks prospect discovery into separate API calls to avoid Railway's 5-minute timeout while maintaining full functionality.

---

## 📊 Pipeline Overview

```
┌──────────────────────────────────────────────────────────────┐
│  Step 1: Search & Filter (30-90s)                            │
│  • LinkedIn profile search (Serper API)                       │
│  • Basic rule-based filtering                                 │
│  • AI title relevance scoring                                 │
│  • Returns: Qualified LinkedIn URLs                           │
└──────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────┐
│  Step 2: Scrape & Validate (15-35s)                          │
│  • LinkedIn profile scraping (Apify)                          │
│  • Company name validation                                    │
│  • Employment status verification                             │
│  • Location matching                                          │
│  • Returns: Enriched prospect data                            │
└──────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────┐
│  Step 3: AI Ranking (5-25s)                                  │
│  • Parallel AI analysis of prospects                          │
│  • Score-based qualification (≥65)                            │
│  • Returns: Ranked & qualified prospects                      │
└──────────────────────────────────────────────────────────────┘
```

**Total Time**: 50-150 seconds (~1-2.5 minutes)
**Success Rate**: 69% (9/13 hospitals in production test)

---

## 🚀 API Endpoints

### Step 1: Search and Filter

```bash
POST /discover-prospects-step1
```

**Request:**
```json
{
  "company_name": "Mayo Clinic",
  "company_city": "Rochester",
  "company_state": "Minnesota",
  "target_titles": []  // Optional - uses defaults if not provided
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Step 1: Search and filter completed",
  "data": {
    "success": true,
    "company_name": "Mayo Clinic",
    "summary": {
      "total_search_results": 45,
      "after_basic_filter": 38,
      "after_ai_basic_filter": 25,
      "after_title_filter": 8,
      "qualified_for_scraping": 8
    },
    "qualified_prospects": [
      {
        "linkedin_url": "https://www.linkedin.com/in/prospect",
        "search_title": "Director of Facilities at Mayo Clinic",
        "search_snippet": "...",
        "target_title": "Director of Facilities",
        "ai_title_score": 90,
        "ai_title_reasoning": "..."
      }
    ]
  },
  "next_step": "Call /discover-prospects-step2 with linkedin_urls"
}
```

---

### Step 2: Scrape Profiles

```bash
POST /discover-prospects-step2
```

**Request:**
```json
{
  "linkedin_urls": [
    "https://www.linkedin.com/in/prospect1",
    "https://www.linkedin.com/in/prospect2"
  ],
  "company_name": "Mayo Clinic",
  "company_city": "Rochester",
  "company_state": "Minnesota",
  "location_filter_enabled": true
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Step 2: LinkedIn scraping and filtering completed",
  "data": {
    "success": true,
    "company_name": "Mayo Clinic",
    "summary": {
      "profiles_scraped": 8,
      "after_advanced_filter": 6,
      "ready_for_ranking": 6
    },
    "enriched_prospects": [
      {
        "linkedin_url": "https://www.linkedin.com/in/prospect",
        "linkedin_data": {
          "name": "John Smith",
          "job_title": "Director of Facilities",
          "company": "Mayo Clinic",
          "location": "Rochester, Minnesota",
          "connections": 450,
          "email": "john.smith@mayo.edu",
          "total_experience_years": 15.2,
          // ... 35 more fields
        },
        "advanced_filter": {
          "passed": true,
          "company_match": true,
          "seniority_score": 85
        }
      }
    ],
    "filtering_details": {
      "filtered_out_count": 2,
      "filtered_out": [
        {
          "stage": "linkedin_connections",
          "name": "Jane Doe",
          "reason": "Low connections (42 < 50)"
        }
      ]
    }
  },
  "next_step": "Call /discover-prospects-step3 with enriched_prospects"
}
```

---

### Step 3: AI Ranking

```bash
POST /discover-prospects-step3
```

**Request:**
```json
{
  "enriched_prospects": [...],  // From Step 2
  "company_name": "Mayo Clinic",
  "min_score_threshold": 65,
  "max_prospects": 10
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Step 3: AI ranking completed - Pipeline finished!",
  "data": {
    "success": true,
    "company_name": "Mayo Clinic",
    "summary": {
      "prospects_ranked": 6,
      "above_threshold": 4,
      "final_top_prospects": 4
    },
    "qualified_prospects": [
      {
        "linkedin_url": "https://www.linkedin.com/in/prospect",
        "linkedin_data": { ... },
        "ai_ranking": {
          "ranking_score": 92,
          "ranking_reasoning": "Director-level facilities role with budget authority...",
          "rank_position": 1
        }
      }
    ],
    "pipeline_complete": true
  }
}
```

---

## 🔧 Key Technical Improvements (October 2025)

### 1. Company Name Matching
**Problem**: "St. Patrick Hospital" vs "Saint Patrick Hospital MT" caused validation failures
**Solution**:
- Normalize "St." ↔ "Saint" variations
- Remove state abbreviations (MT, ID, CA, etc.)
- Collapse multiple whitespaces
- Generate multiple name variations

```python
# Before: Failed to match
"St. Patrick Hospital" ≠ "Saint Patrick Hospital MT"

# After: Successfully matches
"st patrick hospital" == "saint patrick hospital"
```

### 2. LinkedIn Company Extraction
**Problem**: Apify sometimes returns `companyName: null` even when experience data exists
**Solution**: Fallback to extract company from most recent experience

```python
# Extract current company from experience array if main field is null
if not current_company and experience:
    current_company = experience[0].get('company')
```

### 3. Employment Status Validation
**Problem**: Prospects from parent health systems incorrectly flagged as "not employed"
**Solution**: Enhanced company variations generator with St/Saint normalization

```python
variations = [
    "St. Patrick Hospital",
    "Saint Patrick Hospital",
    "St Patrick Hospital",
    "Saint Patrick"
]
```

---

## 📈 Production Test Results

**Test Date**: October 20, 2025
**Dataset**: 13 hospitals in Montana & Idaho
**Total Processing Time**: 25.2 minutes

### Success Metrics

| Metric | Value |
|--------|-------|
| **Hospitals Processed** | 13 |
| **Successful** | 9 (69%) |
| **Failed** | 4 (31%) |
| **Total Prospects Found** | 23 qualified |
| **Avg Prospects/Hospital** | 2.6 |
| **Avg Time/Hospital** | 116 seconds (~2 min) |

### Top Performing Hospitals

| Hospital | Location | Prospects | Top Score |
|----------|----------|-----------|-----------|
| **Saint Alphonsus Regional MC** | Boise, ID | 6 | 92 |
| **Benefis Hospitals Inc** | Great Falls, MT | 3 | 92 |
| **Billings Clinic Hospital** | Billings, MT | 3 | 88 |
| **Bozeman Health Deaconess** | Bozeman, MT | 3 | 88 |
| **St. Patrick Hospital** | Missoula, MT | 3 | 90 |

### Common Failure Reasons

1. **Low LinkedIn Connections** (3 hospitals)
   - All prospects had <50 connections
   - Connection threshold prevents spam/inactive profiles

2. **Employment Status Issues** (1 hospital)
   - 17 prospects found but all flagged as former employees
   - Indicates outdated LinkedIn profiles

---

## 🎯 Filtering Pipeline Details

### Step 1 Filters

**Basic Filter** (Rule-Based):
- ❌ Remove: interns, students, graduates, entry-level
- ❌ Remove: "former," "previously," "ex-" (former employees)
- ✅ Require: Senior indicators OR company mention

**AI Basic Filter** (Connections & Company):
- ❌ Connections < 50 (spam/inactive profiles)
- ✅ Company mention in title/snippet OR connections ≥ 50

**AI Title Filter** (Relevance Scoring):
- Score 0-100 based on title relevance to target roles
- Threshold: ≥55 to proceed to scraping
- Examples:
  - "Director of Facilities" → 90-95
  - "CFO" → 85-90
  - "Energy Manager" → 75-85

### Step 2 Filters

**Advanced Filtering** (LinkedIn Data):
1. **LinkedIn Connections**: ≥50 required
2. **Company Validation**: Name matching with variations
3. **Employment Status**: Current employee verification
4. **Location Matching**: Same state as hospital (if enabled)

**Company Validation Logic**:
```
1. Normalize: "St." → "Saint", remove periods
2. Remove healthcare suffixes: "Medical Center", "Hospital", etc.
3. Remove state abbreviations: " MT", " ID", etc.
4. Normalize whitespace: collapse multiple spaces
5. Compare base names
```

### Step 3 Filters

**AI Ranking** (Parallel Analysis):
- Scores 0-100 based on multiple factors
- Threshold: ≥65 for qualification
- Top N prospects returned (default: 10)

**Scoring Factors**:
- Job title relevance (35%)
- Decision authority (25%)
- Employment confidence (20%)
- Company size (15%)
- Profile accessibility (5%)

---

## 💾 Batch Processing

### Test Scripts Available

Located in `tests/` directory:

1. **`test_three_step_discovery.py`**
   - Single hospital test
   - Good for debugging specific issues
   - Usage: `python tests/test_three_step_discovery.py`

2. **`test_batch_three_step.py`**
   - Test first 2 hospitals from CSV
   - Configurable START_ROW/END_ROW
   - Usage: Edit rows, then run

3. **`batch_all_hospitals_full_export.py`** ⭐
   - Complete batch processing with CSV export
   - Processes all hospitals from HospitalAccountsAndIDs.csv
   - Exports detailed CSV with 40 fields per prospect
   - Usage: `python tests/batch_all_hospitals_full_export.py`

### CSV Export Format

**File**: `all_prospects_detailed.csv`

**40 Fields Per Prospect**:
- Hospital info (name, city, state, account_id)
- Prospect identity (name, LinkedIn URL, title)
- Contact info (email, phone)
- Network metrics (connections, followers)
- Experience (years, authority score)
- Skills (count, top skills)
- AI ranking (score, reasoning, position)
- Profile metrics (completeness, accessibility)
- Filtering results (seniority score, company match)

---

## 🐛 Troubleshooting

### Issue: "No prospects passed advanced filtering"

**Causes**:
1. **Low connections**: All prospects have <50 LinkedIn connections
2. **Company mismatch**: LinkedIn company name doesn't match target
3. **Employment status**: All prospects are former employees
4. **Location mismatch**: Prospects in different state (if location_filter_enabled)

**Solutions**:
1. Lower connection threshold (edit `three_step_prospect_discovery.py:587`)
2. Check company name variations are working
3. Verify LinkedIn profiles are up-to-date
4. Disable location filter with `"location_filter_enabled": false`

### Issue: Step 1 finds prospects but Step 2 filters them all out

**Debug Steps**:
1. Check Step 2 error message for filtering reasons
2. Scrape one profile manually: `POST /linkedin/scrape-profiles`
3. Compare scraped company name with target company name
4. Check if employment status validation is too strict

### Issue: Pipeline times out

**Solutions**:
- Railway has 5-minute timeout - use 3-step pipeline
- For very large hospitals (>20 prospects), may need to:
  - Reduce search results per title (edit `search.py`)
  - Increase min_score_threshold to reduce AI ranking time
  - Process in smaller batches

---

## 📊 Cost Breakdown

### Per Hospital Analysis

| Service | Cost | Notes |
|---------|------|-------|
| **Serper** (Search) | ~$0.05 | 5 titles × 5 results × $0.002 |
| **OpenAI** (AI Ranking) | ~$0.30 | 10 prospects × $0.03 |
| **Apify** (Scraping) | ~$0.05 | 10 prospects × $0.005 |
| **Total** | **~$0.40** | Per hospital processed |

### Monthly Estimates

**For 100 hospitals/month**:
- Serper: $5
- OpenAI: $30
- Apify: $5
- **Total**: $40/month

**Base subscriptions**:
- Serper: $50/month (5,000 searches)
- OpenAI: Pay-as-you-go
- Apify: $49/month + usage

---

## 🔐 Authentication

All prospect discovery endpoints are **public** (no API key required).

Enrichment endpoints (`/enrich/*`) require `X-API-Key` header - see `AUTHENTICATION.md`.

---

## 📚 Related Documentation

- `CLAUDE.md` - Complete development guide for Claude Code
- `README.md` - Project overview and setup
- `AUTHENTICATION.md` - API key setup for enrichment endpoints
- `ENRICHMENT_API.md` - Account/contact enrichment details
- `tests/README.md` - Test suite documentation

---

## 🎯 Best Practices

### When to Use 3-Step Pipeline

✅ **Use 3-step** when:
- Deploying to Railway (5-minute timeout)
- Processing large hospitals (>15 prospects)
- Need detailed progress tracking
- Want to inspect/modify data between steps

❌ **Use improved pipeline** (`/discover-prospects-improved`) when:
- Running locally (no timeout)
- Quick single-hospital tests
- Automated batch processing

### Optimizing Success Rate

1. **Include parent health system**: Many prospects list parent (e.g., "Providence Health")
2. **Use location filter**: Reduces false positives from other locations
3. **Review failed hospitals**: Check filtering reasons to adjust thresholds
4. **Monitor connection counts**: Some hospitals have prospects with low LinkedIn activity

### CSV Export Recommendations

For Salesforce import:
1. Use `hospital_account_id` column to match accounts
2. Map `linkedin_url` to custom field
3. Use `email` and `mobile_number` for contact info
4. Reference `ai_ranking_score` for prioritization
5. Include `ai_ranking_reasoning` in notes/description

---

**Last Updated**: October 21, 2025
**Version**: 3.0 (Company matching fixes)
