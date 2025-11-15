# Bright Data 3-Step Prospect Discovery

## Overview

This document describes the **Bright Data 3-Step Prospect Discovery** service, which replaces Google Search (Serper) with Bright Data LinkedIn Filter API as the starting point for prospect discovery.

## Architecture

### Service Class: `BrightDataProspectDiscoveryService`
**File**: `app/services/brightdata_prospect_discovery.py`

This service follows the same 3-step pattern as the original `ThreeStepProspectDiscoveryService` but uses Bright Data for Step 1:

```
Step 1: Bright Data Filter → LinkedIn dataset filtering by company + titles + location
Step 2: Scrape Profiles    → Full LinkedIn data enrichment (delegates to three_step_service)
Step 3: AI Ranking          → AI qualification and scoring (delegates to three_step_service)
```

## Key Differences from Original 3-Step Discovery

| Feature | Original (Serper) | Bright Data |
|---------|------------------|-------------|
| **Step 1 Source** | Google Search via Serper API | Bright Data LinkedIn Filter API |
| **Search Method** | Text search with `site:linkedin.com/in` | Direct LinkedIn dataset filtering |
| **Title Filtering** | Search 5 results per title | OR filter across all titles (max 20) |
| **Company Matching** | Text-based search | Dataset filter with normalization |
| **Location Filter** | Search query parameter | Dataset city filter |
| **Connection Filter** | Not available in search | Built-in ≥20 connections filter |
| **Processing Time** | 30-90s (multiple search queries) | 60-180s (single snapshot + polling) |
| **Accuracy** | Search result snippets | Structured LinkedIn dataset |
| **Cost** | ~$0.05 per company | ~$0.05 per snapshot |

## Step 1: Bright Data Filter

### What It Does
1. Normalizes company names (removes generic suffixes, keeps healthcare identifiers)
2. Builds company filter with local + parent account variations + location-based names
3. Builds title filter (OR logic across 16 optimized titles)
4. Applies quality filters (min connections, excludes interns/students)
5. Creates Bright Data snapshot
6. Polls for results (up to 5 minutes)
7. Extracts LinkedIn URLs from profiles

### Optimized Title List (16 titles)

Reduced from original 20 to focus on infrastructure/facilities roles:

**C-Suite (3 titles)**
- Chief Financial Officer
- Chief Operating Officer
- CFO

**VP Level (2 titles)**
- VP Facilities
- VP Operations

**Director Level (6 titles)**
- Director of Facilities
- Director of Engineering
- Director of Maintenance
- Director of Operations
- Facilities Director
- Engineering Director

**Manager Level (4 titles)**
- Facilities Manager
- Engineering Manager
- Energy Manager
- Plant Manager

### Key Parameters

```python
await service.step1_brightdata_filter(
    company_name: str,                  # Local account name
    parent_account_name: str = None,    # Parent account (searches both)
    target_titles: List[str] = None,    # Defaults to optimized 16
    company_city: str = None,           # City for location filter
    company_state: str = None,          # State (not used in BD filter)
    min_connections: int = 20           # Minimum LinkedIn connections
)
```

### Filter Logic

```json
{
  "operator": "and",
  "filters": [
    {
      "operator": "or",
      "filters": [
        // Company name variations (4-8 filters)
        // - Original name
        // - Normalized name
        // - Parent account name
        // - Location-based variations
      ]
    },
    {
      "operator": "or",
      "filters": [
        // 16 job titles
      ]
    },
    { "name": "position", "value": "intern", "operator": "not_includes" },
    { "name": "position", "value": "student", "operator": "not_includes" },
    { "name": "connections", "value": "20", "operator": ">=" },
    { "name": "city", "value": "Caldwell", "operator": "includes" }
  ]
}
```

### Output

```python
{
    "success": True,
    "step": "brightdata_filter_complete",
    "company_name": "West Valley Medical Center",
    "summary": {
        "total_profiles_from_brightdata": 152,
        "qualified_for_scraping": 152,
        "snapshot_id": "snap_...",
        "filters_applied": {
            "company_variations": 4,
            "target_titles": 16,
            "min_connections": 20,
            "location_filter": True
        }
    },
    "qualified_prospects": [
        {
            "linkedin_url": "https://linkedin.com/in/...",
            "brightdata_name": "John Doe",
            "brightdata_position": "Director of Facilities",
            "brightdata_company": "West Valley Medical Center",
            "brightdata_connections": 489
        },
        ...
    ]
}
```

## Step 2: Scrape Profiles

Delegates to `ThreeStepProspectDiscoveryService.step2_scrape_profiles()` - same logic as original:

1. Scrapes full LinkedIn profiles via Apify
2. Validates company match (with St./Saint normalization)
3. Validates employment status (filters retired/former employees)
4. Validates location match (same state required)
5. Filters by connections (≥50)

## Step 3: AI Ranking

Delegates to `ThreeStepProspectDiscoveryService.step3_rank_prospects()` - same logic as original:

1. AI scores each prospect (0-100 scale)
2. Filters by minimum threshold (default: 65)
3. Sorts by score and limits to top N (default: 10)

## Usage

### Python Service

```python
from app.services.brightdata_prospect_discovery import BrightDataProspectDiscoveryService

# Initialize service
service = BrightDataProspectDiscoveryService()

# Step 1: Bright Data Filter
step1_result = await service.step1_brightdata_filter(
    company_name="West Valley Medical Center",
    company_city="Caldwell",
    company_state="Idaho",
    min_connections=20
)

# Step 2: Scrape Profiles
linkedin_urls = [p["linkedin_url"] for p in step1_result["qualified_prospects"]]
step2_result = await service.step2_scrape_profiles(
    linkedin_urls=linkedin_urls,
    company_name="West Valley Medical Center",
    company_city="Caldwell",
    company_state="Idaho"
)

# Step 3: AI Ranking
step3_result = await service.step3_rank_prospects(
    enriched_prospects=step2_result["enriched_prospects"],
    company_name="West Valley Medical Center",
    min_score_threshold=65,
    max_prospects=10
)
```

### Test Script

```bash
python tests/test_brightdata_three_step.py
```

**Test Company**: West Valley Medical Center, Caldwell, Idaho

## Configuration

### Required Environment Variables

```bash
# Bright Data API
BRIGHTDATA_API_TOKEN=your_brightdata_token

# Step 2: LinkedIn Scraping
APIFY_API_TOKEN=your_apify_token

# Step 3: AI Ranking
OPENAI_API_KEY=your_openai_key
```

## Performance

### Expected Timing
- **Step 1 (Bright Data Filter)**: 60-180s (snapshot creation + polling)
- **Step 2 (Scrape Profiles)**: 15-35s (depends on number of profiles)
- **Step 3 (AI Ranking)**: 5-25s (depends on number of prospects)
- **Total Pipeline**: 80-240s (~1.5-4 minutes)

### API Costs (per company)
- **Bright Data (Step 1)**: ~$0.05 (snapshot creation)
- **Apify (Step 2)**: ~$0.0047 per profile
- **OpenAI (Step 3)**: ~$0.03 per prospect
- **Example**: 152 profiles → 48 enriched → 10 qualified = $0.05 + $0.71 + $1.44 = **$2.20**

## Advantages over Serper

1. **Structured Data**: Bright Data returns structured LinkedIn profiles, not search snippets
2. **Connection Filtering**: Built-in filter for minimum connections (quality control)
3. **Single API Call**: One snapshot vs. multiple search queries (5 per title)
4. **Company Variations**: Automatically handles name variations in dataset
5. **More Accurate**: Direct dataset filtering vs. text-based search

## Limitations

1. **Bright Data Dataset Coverage**: Limited to profiles in Bright Data's LinkedIn dataset
2. **Polling Required**: Must wait for snapshot processing (up to 5 minutes)
3. **Filter Limit**: Maximum 20 filters per OR group (title list constrained)
4. **No Negative Keywords**: Cannot exclude specific titles (e.g., "nursing manager")
5. **Cost**: May be higher if dataset returns many profiles (scraping cost)

## Recommended Use Cases

Use **Bright Data 3-Step** when:
- You need structured, high-quality LinkedIn data
- You want built-in connection filtering
- You prefer fewer API calls (one snapshot vs. multiple searches)
- Dataset coverage is sufficient for your target companies

Use **Original 3-Step (Serper)** when:
- Target company not in Bright Data dataset
- Need more control over search queries
- Want faster initial results (no polling wait)
- Prefer lower upfront cost (search cheaper than scraping many profiles)

## Future Enhancements

1. **Dynamic Title Expansion**: Adjust title list based on company size/type
2. **Negative Title Filters**: Exclude non-relevant titles (e.g., nursing, social work)
3. **Multi-Region Support**: Better handling of remote/multi-location employees
4. **Caching**: Cache Bright Data snapshots to avoid re-filtering same company
5. **Batch Processing**: Process multiple companies in parallel with shared title filters
