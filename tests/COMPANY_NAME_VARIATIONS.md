# Company Name Variations in Bright Data Filter

## Overview

The filter now searches for **4 company name variations** (when parent account and city are provided):

1. **Local Account Name** - e.g., "Baptist Health South Florida"
2. **Parent Account Name** - e.g., "Baptist Health"
3. **Local + City** - e.g., "Baptist Health South Florida Miami"
4. **Parent + City** - e.g., "Baptist Health Miami"

This captures prospects who list their company in any of these formats on LinkedIn.

## Why This Matters

LinkedIn users format company names inconsistently:
- Some use full names: "Baptist Health South Florida"
- Some use parent names: "Baptist Health"
- Some include location: "Baptist Health Miami Cancer Institute"
- Some use abbreviations: "BHSF Miami"

By searching all variations, we cast a wider net and catch more qualified prospects.

## Filter Structure

### Mayo Clinic Example (No Parent)
```
Company Names (OR - match ANY):
├─ "Mayo Clinic"
└─ "Mayo Clinic Rochester"
```

### Baptist Health Example (With Parent)
```
Company Names (OR - match ANY):
├─ "Baptist Health South Florida"
├─ "Baptist Health"
├─ "Baptist Health South Florida Miami"
└─ "Baptist Health Miami"
```

## Complete Filter JSON (Baptist Health)

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
          },
          {
            "name": "current_company_name",
            "value": "Baptist Health South Florida Miami",
            "operator": "includes"
          },
          {
            "name": "current_company_name",
            "value": "Baptist Health Miami",
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

## What Gets Matched

### Example LinkedIn Company Names That Would Match

For Baptist Health with parent + city:

✅ **Direct Matches:**
- "Baptist Health"
- "Baptist Health South Florida"
- "Baptist Health Miami"
- "Baptist Health South Florida Miami"

✅ **Partial Matches (includes keyword):**
- "Baptist Health Miami Cancer Institute"
- "Baptist Health South Florida - Miami Campus"
- "Baptist Health Cancer Care - Miami"
- "Baptist Health South Florida located in Miami"

❌ **No Match:**
- "Miami Baptist Church" (wrong entity)
- "South Florida Healthcare" (doesn't include "Baptist Health")

## Matching Logic

The `includes` operator in Bright Data is **case-insensitive** and matches **substrings**:

```
"Baptist Health" includes in "Baptist Health Miami Cancer Institute" → ✅ MATCH
"Baptist Health South Florida" includes in "BHSF" → ❌ NO MATCH (abbreviation)
"Miami" includes in "miami, florida, united states" → ✅ MATCH
```

## Real-World Examples

### St. Patrick Hospital (Providence Health System)

**Input:**
- Local: "St. Patrick Hospital"
- Parent: "Providence Health & Services"
- City: "Missoula"

**Variations Searched:**
1. "St. Patrick Hospital"
2. "Providence Health & Services"
3. "St. Patrick Hospital Missoula"
4. "Providence Health & Services Missoula"

**Would Match:**
- "St. Patrick Hospital"
- "Providence St. Patrick Hospital"
- "Providence Health - Missoula"
- "St. Patrick Hospital - Missoula, MT"

### West Valley Medical Center (HCA Healthcare)

**Input:**
- Local: "West Valley Medical Center"
- Parent: "HCA Healthcare"
- City: "Caldwell"

**Variations Searched:**
1. "West Valley Medical Center"
2. "HCA Healthcare"
3. "West Valley Medical Center Caldwell"
4. "HCA Healthcare Caldwell"

**Would Match:**
- "West Valley Medical Center"
- "HCA Healthcare - West Valley"
- "HCA Healthcare Caldwell Region"
- "West Valley Medical Center, Caldwell"

## Implementation in Code

```python
from tests.test_brightdata_linkedin_filter import BrightDataLinkedInFilter

client = BrightDataLinkedInFilter()

# Example 1: With parent account
result = client.search_with_parent_account(
    company_name="Baptist Health South Florida",
    parent_account_name="Baptist Health",
    company_city="Miami",
    company_state="Florida"
)
# Searches: 4 variations (local, parent, local+city, parent+city)

# Example 2: Without parent account
result = client.search_with_parent_account(
    company_name="Mayo Clinic",
    parent_account_name=None,
    company_city="Rochester",
    company_state="Minnesota"
)
# Searches: 2 variations (local, local+city)
```

## Benefits of Multiple Variations

1. **Higher Recall**: Catches prospects regardless of how they format their company name
2. **Parent Relationship Capture**: Finds executives at parent org who oversee local facility
3. **Location-Specific Matches**: Captures people who emphasize their location
4. **Reduced False Negatives**: Minimizes missed prospects due to name formatting

## Potential Issues

### Over-Matching
- "Providence Health Missoula" might match too broadly if there are multiple Providence entities

**Solution**: The location filter (city) helps narrow results

### Under-Matching
- Abbreviations like "BHSF" won't match "Baptist Health South Florida"

**Solution**: Could add common abbreviations as additional variations in future

## Comparison to Original Pipeline

### three_step_prospect_discovery.py
- Searches local name via Google
- Searches parent name via Google (separate search)
- Manually deduplicates by URL
- **Total**: 2 separate search operations

### Bright Data Filter API (New)
- Searches all 4 variations in single filter
- Bright Data handles deduplication automatically
- **Total**: 1 filter operation

## Future Enhancements

1. **Add State Variations**: "Baptist Health Florida", "Mayo Clinic Minnesota"
2. **Add Abbreviations**: Auto-generate common abbreviations (BHSF, WV Medical, etc.)
3. **Add Dashes/Hyphens**: "Baptist Health - South Florida", "Mayo Clinic - Rochester"
4. **Fuzzy Matching**: Use "sounds like" or edit distance for typos

## Testing

### Test Files:
- `tests/test_brightdata_mayo_simple.py` - Mayo Clinic with 2 variations
- `tests/test_brightdata_baptist_simple.py` - Baptist Health with 4 variations
- `tests/test_brightdata_mayo.py` - Full Mayo test with polling
- `tests/test_brightdata_baptist.py` - Full Baptist test with polling

### Run Tests:
```bash
# Show filter structure only
python tests/test_brightdata_mayo_simple.py
python tests/test_brightdata_baptist_simple.py

# Full test with results
python tests/test_brightdata_mayo.py
python tests/test_brightdata_baptist.py
```

## Summary

The filter now searches **up to 4 company name variations** in a single request:

| Variation | Example | When Used |
|-----------|---------|-----------|
| Local Only | "Baptist Health South Florida" | Always |
| Parent Only | "Baptist Health" | If parent provided |
| Local + City | "Baptist Health South Florida Miami" | If city provided |
| Parent + City | "Baptist Health Miami" | If parent AND city provided |

This increases match coverage while maintaining precision through additional filters (titles, location, exclusions).
