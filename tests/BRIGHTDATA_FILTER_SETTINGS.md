# Bright Data LinkedIn Filter Settings

## Overview

The filter uses nested AND/OR logic to search for qualified prospects matching multiple criteria simultaneously.

## Filter Structure

```
AND (all conditions must be true):
├── OR (company matches local OR parent)
│   ├── current_company_name includes "Baptist Health South Florida"
│   └── current_company_name includes "Baptist Health"
│
├── OR (position matches ANY target title)
│   ├── position includes "Director of Facilities"
│   ├── position includes "Director of Engineering"
│   ├── position includes "Director of Maintenance"
│   ├── position includes "VP Facilities"
│   ├── position includes "VP Operations"
│   ├── position includes "Chief Financial Officer"
│   ├── position includes "Chief Operating Officer"
│   ├── position includes "Facilities Manager"
│   ├── position includes "Energy Manager"
│   ├── position includes "Plant Manager"
│   └── position includes "Maintenance Manager"
│
├── NOT position includes "intern"
├── NOT position includes "student"
└── city includes "Miami"
```

## Complete JSON Filter

```json
{
  "dataset_id": "gd_l1viktl72bvl7bjuj0",
  "filter": {
    "operator": "and",
    "filters": [
      {
        "operator": "or",
        "filters": [
          {
            "name": "current_company_name",
            "value": "Baptist Health South Florida",
            "operator": "includes"
          },
          {
            "name": "current_company_name",
            "value": "Baptist Health",
            "operator": "includes"
          }
        ]
      },
      {
        "operator": "or",
        "filters": [
          {"name": "position", "value": "Director of Facilities", "operator": "includes"},
          {"name": "position", "value": "Director of Engineering", "operator": "includes"},
          {"name": "position", "value": "Director of Maintenance", "operator": "includes"},
          {"name": "position", "value": "VP Facilities", "operator": "includes"},
          {"name": "position", "value": "VP Operations", "operator": "includes"},
          {"name": "position", "value": "Chief Financial Officer", "operator": "includes"},
          {"name": "position", "value": "Chief Operating Officer", "operator": "includes"},
          {"name": "position", "value": "Facilities Manager", "operator": "includes"},
          {"name": "position", "value": "Energy Manager", "operator": "includes"},
          {"name": "position", "value": "Plant Manager", "operator": "includes"},
          {"name": "position", "value": "Maintenance Manager", "operator": "includes"}
        ]
      },
      {
        "name": "position",
        "value": "intern",
        "operator": "not_includes"
      },
      {
        "name": "position",
        "value": "student",
        "operator": "not_includes"
      },
      {
        "name": "city",
        "value": "Miami",
        "operator": "includes"
      }
    ]
  }
}
```

## Filter Logic Explanation

### 1. Company Filter (OR Logic)
Matches profiles where the company name includes EITHER:
- **Local Account**: "Baptist Health South Florida"
- **Parent Account**: "Baptist Health"

This ensures we capture prospects from both the specific facility AND the parent organization.

### 2. Job Title Filter (OR Logic)
Matches profiles where the position includes ANY of these 11 target titles:
- **Directors**: Director of Facilities, Director of Engineering, Director of Maintenance
- **VPs**: VP Facilities, VP Operations
- **C-Suite**: Chief Financial Officer, Chief Operating Officer
- **Managers**: Facilities Manager, Energy Manager, Plant Manager, Maintenance Manager

These titles are specifically chosen for energy efficiency/infrastructure sales opportunities.

### 3. Exclusions (NOT Logic)
Filters OUT profiles where the position includes:
- "intern" - Entry-level temporary positions
- "student" - Academic/trainee roles

This ensures we only get decision-makers and experienced professionals.

### 4. Location Filter (City Only)
Matches profiles where the city field includes "Miami"

**Why City Only (not state)?**
- LinkedIn's `city` field format varies: "Miami, Florida, United States" or "Miami, FL"
- Using city alone is more flexible and catches more valid matches
- State-only filtering was too restrictive and caused false negatives (e.g., Mayo Clinic)

## Available Filter Fields

According to Bright Data's LinkedIn Profiles dataset (`gd_l1viktl72bvl7bjuj0`), you can filter on:

| Field Name | Description | Example |
|------------|-------------|---------|
| `current_company_name` | Current employer | "Baptist Health" |
| `position` | Current job title | "Director of Facilities" |
| `city` | Location (city, state, country) | "Miami, Florida, United States" |
| `name` | Full name | "John Smith" |
| `headline` | LinkedIn headline | "Facilities Director at Baptist Health" |

## Filter Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `includes` | Field contains value (case-insensitive) | position includes "Director" |
| `not_includes` | Field does NOT contain value | position not_includes "intern" |
| `equals` | Exact match | current_company_name equals "Mayo Clinic" |
| `not_equals` | Does not exactly match | city not_equals "Unknown" |

## Example Results (Baptist Health South Florida)

**Query**: Local="Baptist Health South Florida", Parent="Baptist Health", City="Miami"

**Retrieved**: 5 profiles

1. **John Sciarrone** - Director of Facilities at Baptist Health South Florida (Miami, FL)
2. **Evelyn Rodriguez** - Senior Executive Assistant to CFO at Baptist Health South Florida (Miami, FL)
3. **Jenny Waltzer** - VP and Chief Operating Officer at Baptist Health (Miami, FL)
4. **Jerome Marshall** - Director of Facilities Management at Baptist Health (Miami, FL)

**Key Observations**:
- Mix of local ("Baptist Health South Florida") and parent ("Baptist Health") company names ✅
- All in Miami, Florida location ✅
- Target titles: Directors, VPs, CFO-adjacent ✅
- No interns or students ✅

## Usage in Python

```python
from tests.test_brightdata_linkedin_filter import BrightDataLinkedInFilter

client = BrightDataLinkedInFilter()

# Search with local + parent account
result = client.search_with_parent_account(
    company_name="Baptist Health South Florida",
    parent_account_name="Baptist Health",
    company_city="Miami",
    company_state="Florida"  # Note: state is ignored in current implementation
)

if result and result.get("snapshot_id"):
    profiles = client.get_snapshot_results(
        snapshot_id=result["snapshot_id"],
        max_wait_time=300,
        poll_interval=10
    )

    print(f"Found {len(profiles)} qualified prospects!")
```

## Configuration Options

### Method: `search_with_parent_account()`

**Parameters**:
- `company_name` (str, required): Local account name
- `parent_account_name` (str, optional): Parent organization name
- `target_titles` (List[str], optional): Custom job titles (defaults to 11 standard titles)
- `company_city` (str, optional): City for location filtering
- `company_state` (str, optional): State (currently not used in filter)

**Default Target Titles**:
```python
[
    "Director of Facilities",
    "Director of Engineering",
    "Director of Maintenance",
    "VP Facilities",
    "VP Operations",
    "Chief Financial Officer",
    "Chief Operating Officer",
    "Facilities Manager",
    "Energy Manager",
    "Plant Manager",
    "Maintenance Manager"
]
```

## Performance Metrics

- **Filter Creation**: ~1 second (Status 200)
- **Snapshot Processing**: 1-3 minutes (scheduled → building → ready)
- **Data Download**: ~1 second (once ready)
- **Total Time**: 1-3 minutes per query

## Limitations

1. **Dataset Dependency**: Only filters EXISTING data in the dataset
   - If a company's profiles haven't been scraped yet, filter returns empty
   - Mayo Clinic returned "no_records_found" - not in dataset

2. **No Real-Time Scraping**: This is a filter API, not a scraping API
   - Need to populate dataset first using Bright Data's collection APIs
   - Or use alternative APIs (Discover by Keyword, Scrape by URL)

3. **Dataset Size**: Unknown how many profiles are in `gd_l1viktl72bvl7bjuj0`
   - Baptist Health had ~37 profiles (before location filter)
   - After filters: 5 qualified prospects in Miami

## Comparison to three_step_prospect_discovery.py

| Feature | three_step_prospect_discovery.py | Bright Data Filter API |
|---------|----------------------------------|------------------------|
| Search Method | Serper Google Search → LinkedIn scraping | Filter pre-collected LinkedIn data |
| Real-time | ✅ Yes (scrapes on demand) | ❌ No (filters existing data) |
| Speed | Slower (~2-3 min for full pipeline) | Faster (~1-2 min if data exists) |
| Coverage | Limited by search results (5 per title) | Depends on dataset size |
| Cost | ~$0.57 per company | TBD (depends on Bright Data pricing) |
| Data Quality | Fresh, current | Depends on when dataset was updated |
| Filtering | Multi-stage (basic → AI → advanced) | Single-stage (rule-based only) |

## Next Steps

1. **Integrate with Salesforce**: Auto-pull company name, parent, and location from account ID
2. **Add AI Ranking**: Apply the same AI scoring logic from `three_step_prospect_discovery.py`
3. **Hybrid Approach**: Use Bright Data filter first, fall back to Serper search if no results
4. **Dataset Management**: Investigate Bright Data's collection APIs to populate dataset proactively
