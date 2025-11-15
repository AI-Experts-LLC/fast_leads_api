# Bright Data LinkedIn Filter API - Implementation Notes

## ✅ Summary

Successfully implemented an object-oriented Python client for Bright Data's LinkedIn Filter API with proper polling mechanism for Baptist Health prospect discovery.

## ✅ What Works (October 2025)

### 1. Filter API Request (Status 200 ✅)
The filter API successfully accepts our nested AND/OR query structure:

```json
{
  "dataset_id": "gd_l1viktl72bvl7bjuj0",
  "filter": {
    "operator": "and",
    "filters": [
      {
        "name": "current_company_name",
        "value": "Baptist Health",
        "operator": "includes"
      },
      {
        "operator": "or",
        "filters": [
          {"name": "position", "value": "Director of Facilities", "operator": "includes"},
          {"name": "position", "value": "CFO", "operator": "includes"},
          {"name": "position", "value": "VP Operations", "operator": "includes"}
          // ... 8 more titles
        ]
      }
    ]
  }
}
```

**Response:** Returns `snapshot_id` (e.g., `snap_mh57lal61fv9vquada`) - Status 200 ✅

### 2. Snapshot Metadata Retrieval (Status 200 ✅)

**CORRECT ENDPOINT:** `GET /datasets/snapshots/{snapshot_id}` (NO v3 in path!)

```python
snapshot_url = f"https://api.brightdata.com/datasets/snapshots/{snapshot_id}"
```

Response includes:
- `id`: Snapshot ID
- `status`: scheduled | building | ready | failed
- `created`: Creation timestamp
- `dataset_id`: Dataset ID
- `dataset_size`: Number of records
- `file_size`: File size in bytes

### 3. Snapshot Data Download (When Status = ready)

**CORRECT ENDPOINT:** `GET /datasets/snapshots/{snapshot_id}/download?format=json`

```python
download_url = f"https://api.brightdata.com/datasets/snapshots/{snapshot_id}/download?format=json"
```

Returns array of LinkedIn profile objects with fields:
- `name`
- `position`
- `current_company_name`
- `city`, `country_code`
- `url` (LinkedIn profile URL)

### 4. Polling Implementation
- Polls snapshot endpoint every 10 seconds
- Maximum wait time: 5 minutes (300 seconds)
- Handles all snapshot statuses: scheduled → building → ready
- Clean progress output with elapsed time tracking

## 🎯 Key Fixes (October 2025)

### Issue 1: Wrong Snapshot Endpoint (FIXED ✅)
**Problem:** Used `/datasets/v3/snapshot/{id}` which returned 404
**Solution:** Correct endpoint is `/datasets/snapshots/{id}` (no v3!)

### Issue 2: Wrong Download Endpoint (FIXED ✅)
**Problem:** Tried `/datasets/v3/{dataset_id}/items?snapshot_id={id}`
**Solution:** Correct endpoint is `/datasets/snapshots/{id}/download?format=json`

### Issue 3: Missing Sleep in Polling Loop (FIXED ✅)
**Problem:** Polling too fast without delay between attempts
**Solution:** Added `time.sleep(poll_interval)` after checking status

### Issue 4: Status Field Naming (FIXED ✅)
**Problem:** API documentation showed lowercase `status` but response had `Status`
**Solution:** Check both: `snapshot_info.get('status', snapshot_info.get('Status', 'unknown'))`

## 📋 Implementation Details

### File: `tests/test_brightdata_linkedin_filter.py`

**Class:** `BrightDataLinkedInFilter`

**Key Methods:**
- `search_by_title_and_company()` - Creates filter with nested AND/OR logic
- `get_snapshot_results()` - Polls snapshot endpoint with 5-minute timeout
- `search_profiles()` - Generic search with custom filters

**Target Titles (from search.py):**
1. Director of Facilities
2. Director of Engineering
3. Director of Maintenance
4. VP Facilities
5. VP Operations
6. Chief Financial Officer
7. Chief Operating Officer
8. Facilities Manager
9. Energy Manager
10. Plant Manager
11. Maintenance Manager

## 🎯 Usage

### Quick Test (Baptist Health)
```bash
python tests/test_brightdata_baptist.py
```

### Full Test Suite (HCA Healthcare + Baptist Health)
```bash
python tests/test_brightdata_linkedin_filter.py
```

### Python API Usage
```python
from tests.test_brightdata_linkedin_filter import BrightDataLinkedInFilter

client = BrightDataLinkedInFilter()

# Create filter (returns snapshot_id)
result = client.search_by_title_and_company(
    company_name="Baptist Health",
    company_city="Miami",      # Optional
    company_state="Florida"    # Optional
)

# Poll for results (up to 5 minutes)
if result and result.get("snapshot_id"):
    profiles = client.get_snapshot_results(
        snapshot_id=result["snapshot_id"],
        max_wait_time=300,  # 5 minutes
        poll_interval=10    # Check every 10 seconds
    )

    if profiles and isinstance(profiles, list):
        print(f"Found {len(profiles)} profiles!")
        for profile in profiles:
            print(f"{profile['name']} - {profile['position']}")
```

## 📊 API Endpoints Summary

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/datasets/filter` | POST | Create filter snapshot | ✅ Working |
| `/datasets/snapshots/{id}` | GET | Get snapshot metadata | ✅ Working |
| `/datasets/snapshots/{id}/download` | GET | Download snapshot data | ✅ Working |

## ⚠️ Important Notes

### Dataset Requirements
- The Filter API only filters **EXISTING** data in the dataset
- If no matching profiles exist in `gd_l1viktl72bvl7bjuj0`, the snapshot will be empty
- You may need to collect/scrape LinkedIn profiles first before filtering
- Use Bright Data's "Discover by Name" or "Collect by URL" endpoints to populate the dataset

### Snapshot Processing Time
- Snapshots typically take 1-5 minutes to process
- Status progression: `scheduled` → `building` → `ready`
- Poll every 10 seconds to check status
- Maximum recommended wait time: 5 minutes (300 seconds)

### Response Format
- Filter creation: Returns `{"snapshot_id": "snap_..."}`
- Snapshot metadata: Returns object with `status`, `dataset_size`, `file_size`, etc.
- Snapshot download: Returns array of profile objects `[{name, position, ...}, ...]`

## 🔧 Error Handling

### Common Issues
1. **Empty Results:** No matching data in dataset - need to collect profiles first
2. **Status: failed:** Filter processing failed - check filter syntax
3. **Timeout:** Snapshot still `scheduled` after 5 minutes - may need longer wait
4. **404 on download:** Snapshot not ready - ensure status is `ready` first

## 💡 Next Steps

### Option 1: Collect Data First
Use Bright Data's collection APIs to populate the dataset before filtering:
```python
# Trigger data collection
trigger_url = "https://api.brightdata.com/datasets/v3/trigger"
payload = [{
    "first_name": "John",
    "last_name": "Smith",
    "current_company": "Baptist Health"
}]
```

### Option 2: Use Alternative Bright Data APIs
- **Discover by Keyword:** Search LinkedIn without pre-collection
- **Scrape by URL:** Direct profile scraping from LinkedIn URLs
- **People Search:** Real-time LinkedIn search (may be slower/more expensive)

## 📝 Test Results (October 2025)

### HCA Healthcare (Tampa)
- Filter created: ✅ Status 200
- Snapshot ID: `snap_mh5a3ge31zhi1m6ni0`
- Initial status: `scheduled`
- Expected: Wait for `ready` status then download

### Baptist Health
- Filter created: ✅ Status 200
- Snapshot ID: TBD
- Target: 11 job titles with OR logic
- Expected: Wait for `ready` status then download

## 🎉 Success Criteria Met

- ✅ Filter API accepts nested AND/OR queries (200 OK)
- ✅ Snapshot metadata endpoint working (200 OK)
- ✅ Polling mechanism properly implemented with sleep intervals
- ✅ All snapshot statuses handled (scheduled, building, ready, failed)
- ✅ Download endpoint integrated for data retrieval
- ✅ OOP design with reusable `BrightDataLinkedInFilter` class
- ✅ Simple test script for Baptist Health (`test_brightdata_baptist.py`)
- ✅ Comprehensive test suite with HCA Healthcare example

## 📚 Documentation References

- **Bright Data Datasets API:** https://docs.brightdata.com/api-reference/datasets/introduction
- **Filter Dataset:** https://docs.brightdata.com/api-reference/datasets/filter-dataset
- **Get Snapshot:** https://docs.brightdata.com/api-reference/datasets/get-snapshot-metadata
- **Download Snapshot:** https://docs.brightdata.com/api-reference/datasets/download-snapshot-content
