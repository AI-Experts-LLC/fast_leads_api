# Step 4: ZoomInfo Contact Validation

## ⚠️ DISABLED BY DEFAULT

**Status:** This feature is implemented but **disabled by default** due to ZoomInfo's OAuth authentication requirements which are incompatible with Railway's serverless deployment.

**To Enable:** Pass `enable_zoominfo: true` in the request payload (only works in local development with proper OAuth setup).

## Overview

Step 4 enhances the prospect discovery pipeline by validating and enriching contact information (email, phone numbers) using the ZoomInfo API. This step compares LinkedIn data with ZoomInfo data and selects the most accurate and current information.

## Purpose

**Problem Solved:** LinkedIn profiles often don't have publicly visible email addresses or phone numbers due to privacy settings. ZoomInfo provides professional contact database access with more comprehensive and up-to-date contact information.

**Value:**
- Increases email/phone coverage for prospects
- Validates existing LinkedIn contact data
- Prefers ZoomInfo data when available (more current and verified)
- Provides data source transparency (LinkedIn vs ZoomInfo vs both match)

## Pipeline Position

```
Step 1: Search & Filter (LinkedIn)
  ↓
Step 2: Scrape Profiles (Apify)
  ↓
Step 3: AI Ranking (OpenAI)
  ↓
Step 4: Contact Validation (ZoomInfo) ← NEW
  ↓
Final Validated Prospects
```

## How It Works

### 1. Input
Takes qualified prospects from Step 3 (those scoring ≥70):
```json
{
  "qualified_prospects": [...],
  "company_name": "Bozeman Health"
}
```

### 2. Processing
For each prospect:
1. **Extract name and company** from LinkedIn data
2. **Search ZoomInfo** for matching contact
3. **Enrich** with detailed ZoomInfo data if found
4. **Compare** LinkedIn vs ZoomInfo values for:
   - Email
   - Mobile phone
   - Direct phone
5. **Select best value** using preference rules:
   - If both match → use value, mark as "both_match"
   - If different for contact fields → prefer ZoomInfo (more current)
   - If only one has value → use that value

### 3. Output
Returns validated prospects with:
- **Original LinkedIn data** (unchanged structure)
- **Enhanced contact fields** (email, mobile, direct phone)
- **Validation metadata** showing:
  - Search status (validated, not_found, skipped, error)
  - Data source for each field
  - Comparison details
  - Full ZoomInfo data for reference

### 4. Statistics
```json
{
  "stats": {
    "total": 10,
    "validated": 7,
    "email_enriched": 5,
    "phone_enriched": 6,
    "not_found": 2,
    "skipped": 1,
    "errors": 0
  }
}
```

## API Endpoint

**POST** `/discover-prospects-step4`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "qualified_prospects": [
    {
      "linkedin_data": {
        "name": "John Doe",
        "first_name": "John",
        "last_name": "Doe",
        "company_name": "Bozeman Health",
        "email": null,
        "mobile_number": null
      },
      "ai_ranking": {
        "ranking_score": 88,
        "reasoning": "..."
      }
    }
  ],
  "company_name": "Bozeman Health",
  "enable_zoominfo": false  // Default: false (disabled due to OAuth issues on Railway)
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Step 4: ZoomInfo validation completed - Pipeline finished!",
  "data": {
    "success": true,
    "prospects": [
      {
        "linkedin_data": {
          "name": "John Doe",
          "first_name": "John",
          "last_name": "Doe",
          "company_name": "Bozeman Health",
          "email": "john.doe@bozemanhealth.org",
          "mobile_number": "+1-406-555-1234",
          "direct_phone": "+1-406-555-5678"
        },
        "ai_ranking": {
          "ranking_score": 88,
          "reasoning": "..."
        },
        "zoominfo_validation": {
          "status": "validated",
          "searched": true,
          "contact_verified": true,
          "zoominfo_id": "123456789",
          "comparisons": {
            "email": {
              "source": "zoominfo",
              "linkedin_value": null,
              "zoominfo_value": "john.doe@bozemanhealth.org",
              "selected_value": "john.doe@bozemanhealth.org"
            },
            "mobile_phone": {
              "source": "zoominfo_preferred",
              "linkedin_value": "+1-406-555-9999",
              "zoominfo_value": "+1-406-555-1234",
              "selected_value": "+1-406-555-1234"
            }
          },
          "zoominfo_data": {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@bozemanhealth.org",
            "mobile_phone": "+1-406-555-1234",
            "direct_phone": "+1-406-555-5678",
            "job_title": "Director of Facilities",
            "company_name": "Bozeman Health"
          }
        }
      }
    ],
    "stats": {
      "total": 1,
      "validated": 1,
      "not_found": 0,
      "skipped": 0,
      "errors": 0,
      "email_enriched": 1,
      "phone_enriched": 1
    }
  },
  "timestamp": "2025-10-14T20:30:00.000Z"
}
```

## Configuration

### Environment Variables
```bash
# Option 1: Direct access token (preferred)
ZOOMINFO_ACCESS_TOKEN=your_access_token

# Option 2: API key
ZOOMINFO_API_KEY=your_api_key

# Option 3: OAuth credentials
ZOOMINFO_CLIENT_ID=your_client_id
ZOOMINFO_CLIENT_SECRET=your_client_secret
```

### Graceful Degradation
**By default (enable_zoominfo=false):**
- Step 4 returns "skipped" status immediately
- Original LinkedIn data is preserved unchanged
- Pipeline completes successfully
- No ZoomInfo API calls made
- No OAuth authentication required

**If enabled but credentials not configured:**
- Step 4 returns "skipped" status with reason
- Original LinkedIn data is preserved
- Pipeline still completes successfully
- No error thrown

## Data Source Preference Rules

| Field Type | LinkedIn Only | ZoomInfo Only | Both Match | Both Differ |
|------------|--------------|---------------|------------|-------------|
| Email | Use LinkedIn | Use ZoomInfo | Use value (mark "both_match") | **Prefer ZoomInfo** (more current) |
| Mobile Phone | Use LinkedIn | Use ZoomInfo | Use value (mark "both_match") | **Prefer ZoomInfo** (more current) |
| Direct Phone | Use LinkedIn | Use ZoomInfo | Use value (mark "both_match") | **Prefer ZoomInfo** (more current) |

**Rationale:** ZoomInfo data is typically more current because:
- Professional database actively maintained
- Verified through multiple sources
- Updated more frequently than public LinkedIn profiles
- Includes direct lines not typically public on LinkedIn

## Implementation Files

| File | Purpose |
|------|---------|
| `app/services/zoominfo_validation.py` | Core validation service |
| `main.py` (lines 529-592) | Step 4 API endpoint |
| `tests/test_bozeman_health_railway.py` | Testing with Railway deployment |

## Performance

**Expected Duration:** 10-20 seconds for 10 prospects

**Parallelization:** All ZoomInfo API calls are executed concurrently using `asyncio.gather()` for optimal performance.

**Cost:** ~$0.10-0.20 per prospect (ZoomInfo API pricing varies by plan)

## Testing

### Manual Test
```bash
# Requires prospects from Step 3
curl -X POST "http://127.0.0.1:8000/discover-prospects-step4" \
  -H "Content-Type: application/json" \
  -d '{
    "qualified_prospects": [...],
    "company_name": "Bozeman Health"
  }'
```

### Automated Test
```bash
# Full 4-step pipeline test
python tests/test_bozeman_health_railway.py
```

## Validation Status Codes

| Status | Description |
|--------|-------------|
| `validated` | Contact found in ZoomInfo and enriched |
| `not_found` | Contact not found in ZoomInfo search |
| `skipped` | Missing required fields (first/last name) or ZoomInfo disabled |
| `error` | Exception occurred during validation |

## Benefits

1. **Higher Contact Coverage**
   - Fills in missing emails/phones from LinkedIn
   - Adds direct phone numbers not available on LinkedIn

2. **Data Quality**
   - More current contact information
   - Verified through professional database
   - Reduces bounce rates and wrong numbers

3. **Transparency**
   - Shows data source for each field
   - Preserves both LinkedIn and ZoomInfo values
   - Logs comparison decisions

4. **Non-Breaking**
   - Gracefully handles missing credentials
   - Preserves original data structure
   - No impact on existing Steps 1-3

## Future Enhancements

- [ ] Add option to prefer LinkedIn over ZoomInfo for specific fields
- [ ] Include confidence scores from ZoomInfo
- [ ] Add caching to reduce duplicate API calls
- [ ] Support batch ZoomInfo API calls for better performance
- [ ] Add ZoomInfo enrichment for company data (not just contacts)
