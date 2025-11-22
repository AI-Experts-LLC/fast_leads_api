# Hybrid Prospect Discovery Pipeline - Implementation Summary

**Date**: January 2025
**Status**: ✅ Complete and Ready for Testing

## Overview

Implemented a new **Hybrid Prospect Discovery Pipeline** that combines:
- **Serper** (web search) for maximum LinkedIn coverage
- **Bright Data** (LinkedIn dataset) for rich profile data

The pipeline discovers qualified leads and queues them to a **PendingUpdates** approval workflow before importing to Salesforce.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│  STEP 1: PARALLEL SEARCH (30-60s)              │
│  ┌──────────────┐      ┌──────────────────┐   │
│  │ Serper API   │      │  Bright Data     │   │
│  │ (Web Search) │ ║    │  (Dataset Filter)│   │
│  └──────┬───────┘      └────────┬─────────┘   │
│         │                        │              │
│         └────────────┬───────────┘              │
│                      ▼                          │
│            Deduplicate by name                  │
│         (Prefer Bright Data data)               │
└─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│  STEP 2: ENRICH SERPER-ONLY RESULTS (15-30s)   │
│  ┌──────────────────────────────────────┐      │
│  │ Serper-only → Apify scraping         │      │
│  │ (Get full LinkedIn data)             │      │
│  └──────────────────────────────────────┘      │
│                                                  │
│  ┌──────────────────────────────────────┐      │
│  │ Bright Data results → Already enriched │    │
│  └──────────────────────────────────────┘      │
└─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│  STEP 3: AI RANKING & QUALIFICATION (10-20s)   │
│  - Parallel AI scoring (0-100 scale)            │
│  - Filter by threshold (≥65)                    │
│  - Sort by score                                │
└─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│  STEP 4: QUEUE TO PENDING UPDATES (1-2s)       │
│  - Create PendingUpdate records (type: Lead)    │
│  - Store full prospect data                     │
│  - Show in dashboard for approval               │
└─────────────────────────────────────────────────┘
```

**Total Time**: 56-112 seconds (~1-2 minutes)

---

## Files Created/Modified

### New Files
1. **`app/services/hybrid_prospect_discovery.py`** (418 lines)
   - Main service orchestrating the 4-step pipeline
   - Parallel API calls using `asyncio.gather()`
   - Name-based deduplication with fuzzy matching
   - Delegates to existing services for reuse

2. **`test_hybrid_pipeline.py`** (246 lines)
   - Complete test script for local development
   - Tests all 4 steps sequentially
   - Provides formatted output with timing and stats
   - Usage: `python test_hybrid_pipeline.py`

3. **`HYBRID_PIPELINE_IMPLEMENTATION.md`** (this file)
   - Implementation summary and documentation

### Modified Files
1. **`app/models.py`** (line 41)
   - Added `LEAD = "Lead"` to `RecordType` enum
   - Enables queuing of Lead records to PendingUpdates

2. **`app/services/pending_updates.py`** (lines 154-157, 226-301)
   - Updated `approve_update()` to handle Lead creation
   - Added `queue_lead_batch()` method for bulk lead queuing
   - Transforms prospect data into Salesforce Lead fields

3. **`main.py`** (lines 21, 769-1068)
   - Imported `hybrid_prospect_discovery_service`
   - Added 4 new API endpoints:
     - `POST /discover-leads-step1` - Parallel Search
     - `POST /discover-leads-step2` - Deduplicate + Enrich
     - `POST /discover-leads-step3` - AI Ranking
     - `POST /discover-leads-step4` - Queue Leads
   - Comprehensive docstrings with examples

4. **`app/templates/dashboard.html`** (lines 370-374)
   - Added "New Lead Discovery" card
   - Links to API documentation
   - Explains results appear in Pending Updates

5. **`CLAUDE.md`** (lines 25-32, 144-165, 189, 198, 281-297)
   - Added test command for hybrid pipeline
   - Documented architecture and benefits
   - Added to service list
   - Added API endpoint documentation

---

## API Endpoints

### Step 1: Parallel Search
```bash
POST /discover-leads-step1
Content-Type: application/json

{
  "company_name": "Mayo Clinic",
  "parent_account_name": "Mayo Clinic Health System",  # Optional
  "company_city": "Rochester",
  "company_state": "Minnesota",  # REQUIRED
  "target_titles": []  # Optional - uses defaults if not provided
}
```

**Returns**: `serper_prospects` and `brightdata_prospects` for Step 2

---

### Step 2: Deduplicate + Enrich
```bash
POST /discover-leads-step2
Content-Type: application/json

{
  "serper_prospects": [...],      # From Step 1
  "brightdata_prospects": [...],  # From Step 1
  "company_name": "Mayo Clinic",
  "company_city": "Rochester",
  "company_state": "Minnesota"
}
```

**Returns**: `enriched_prospects` (deduplicated and enriched) for Step 3

---

### Step 3: AI Ranking
```bash
POST /discover-leads-step3
Content-Type: application/json

{
  "enriched_prospects": [...],   # From Step 2
  "company_name": "Mayo Clinic",
  "min_score_threshold": 65,     # Optional, defaults to 65
  "max_prospects": 10            # Optional, defaults to 10
}
```

**Returns**: `qualified_prospects` (scored ≥65) for Step 4

---

### Step 4: Queue to PendingUpdates
```bash
POST /discover-leads-step4
Content-Type: application/json

{
  "qualified_prospects": [...],  # From Step 3
  "company_name": "Mayo Clinic",
  "company_account_id": "001..."  # Optional - Salesforce Account ID
}
```

**Returns**: Count of queued leads

**Result**: Leads appear at `/pending-updates?record_type=Lead` and in `/dashboard`

---

## Key Features

### 1. Maximum Coverage
- **Serper**: Web search finds profiles not in datasets
- **Bright Data**: LinkedIn dataset provides rich, structured data
- **Combined**: More prospects than either source alone

### 2. Smart Deduplication
- Compares prospects by **name** (fuzzy matching)
- For duplicates: **Prefers Bright Data** (richer profile data)
- For unique Serper results: **Enriches via Apify** scraping

### 3. Approval Workflow
- All leads queued to **PendingUpdates** database table
- **RecordType.LEAD** distinguishes from Account/Contact updates
- Dashboard shows leads for manual review
- User approves → Creates Lead in Salesforce
- User rejects → Marks as rejected, no Salesforce action

### 4. Dashboard Integration
- **New card**: "New Lead Discovery" links to API docs
- **Pending Updates section**: Shows all pending leads
- **Approve/Reject buttons**: One-click approval or rejection
- **Collapsible details**: View full prospect data in table

---

## Testing

### Local Development
```bash
# Start API server
hypercorn main:app --reload

# In another terminal, run test script
python test_hybrid_pipeline.py
```

**Expected Output**:
```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║            🆕 HYBRID PROSPECT DISCOVERY PIPELINE TEST                        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

================================================================================
  🆕 HYBRID PROSPECT DISCOVERY PIPELINE TEST
================================================================================

Test Company: Portneuf Medical Center
Location: Pocatello, Idaho
Timestamp: 2025-01-21T10:30:00

🔹 STEP 1: Parallel Search (Serper + Bright Data)
--------------------------------------------------------------------------------
✅ Step 1 completed in 45.2s
   → Serper: 15 prospects
   → Bright Data: 8 prospects

🔹 STEP 2: Deduplicate + Enrich
--------------------------------------------------------------------------------
✅ Step 2 completed in 22.1s
   → Bright Data: 8 prospects
   → Serper (enriched): 12 prospects
   → Duplicates skipped: 3 prospects
   → Total enriched: 20 prospects

🔹 STEP 3: AI Ranking & Qualification
--------------------------------------------------------------------------------
✅ Step 3 completed in 18.5s
   → Qualified prospects (≥65 score): 5

   📋 Top Qualified Prospects:
      1. John Smith - Director of Facilities (Score: 82)
      2. Jane Doe - CFO (Score: 78)
      3. Bob Johnson - VP Operations (Score: 72)
      4. Alice Williams - Energy Manager (Score: 69)
      5. Mike Brown - Director of Engineering (Score: 67)

🔹 STEP 4: Queue Leads for Approval
--------------------------------------------------------------------------------
✅ Step 4 completed in 1.2s
   → Queued: 5 leads
   → Failed: 0 leads
   → Total: 5 leads

================================================================================
  🎉 PIPELINE COMPLETED SUCCESSFULLY
================================================================================
Total Time: 87.0s
  → Step 1 (Parallel Search): 45.2s
  → Step 2 (Deduplicate + Enrich): 22.1s
  → Step 3 (AI Ranking): 18.5s
  → Step 4 (Queue Leads): 1.2s

✅ 5 leads queued for approval
📊 View at: http://127.0.0.1:8000/dashboard
📋 View pending updates at: http://127.0.0.1:8000/pending-updates?record_type=Lead

================================================================================
Test complete! 🚀
================================================================================
```

### Verify in Dashboard
1. Navigate to `http://127.0.0.1:8000/dashboard`
2. Login with password (set in `.env` as `DASHBOARD_PASSWORD`)
3. **Pending Salesforce Updates** section shows queued leads
4. Click **row** to expand and see full prospect data
5. Click **green checkmark** (✓) to approve and create Lead in Salesforce
6. Click **red X** to reject

---

## Code Quality

### Minimal Code Changes ✅
- Reused existing services: `three_step_prospect_discovery`, `brightdata_prospect_discovery`
- No modifications to core search/scraping logic
- Simple, readable Python code

### Comprehensive Error Handling ✅
- Try/catch blocks in all steps
- Graceful degradation if one source fails
- Detailed error messages with context

### Cost Tracking ✅
- Inherits cost tracking from underlying services
- Logs API call counts and durations
- Summary stats in each step response

### Documentation ✅
- Inline code comments
- Comprehensive docstrings
- API endpoint documentation
- This implementation summary

---

## Production Deployment

### Environment Variables Required
```bash
# Existing (already configured)
SERPER_API_KEY=your_serper_key
OPENAI_API_KEY=your_openai_key
APIFY_API_TOKEN=your_apify_token
BRIGHTDATA_API_TOKEN=your_brightdata_token
SALESFORCE_DOMAIN=https://test.salesforce.com
SALESFORCE_USERNAME=your_username
SALESFORCE_PASSWORD=your_password
SALESFORCE_SECURITY_TOKEN=your_token
DASHBOARD_PASSWORD=your_dashboard_password

# No new environment variables needed!
```

### Railway Deployment
1. **No code changes needed** - merge to main branch
2. Railway auto-deploys on git push
3. Database migrations auto-run (new `RecordType.LEAD` enum)
4. Test with: `curl https://your-railway-url.up.railway.app/health`

### Database Migration
The `RecordType` enum change will require a database migration:
```sql
-- PostgreSQL migration (Railway runs this automatically)
ALTER TYPE recordtype ADD VALUE 'Lead';
```

---

## Usage Workflow

### For Sales Team
1. Go to dashboard: `/dashboard`
2. Click **"New Lead Discovery"** card
3. In API docs, use `/discover-leads-step1` with company details
4. Copy results to Step 2, 3, 4 sequentially
5. Return to dashboard to review/approve leads

### For Developers (Automated)
```python
import requests

# Full pipeline in one script
BASE_URL = "http://127.0.0.1:8000"

# Step 1: Parallel Search
response1 = requests.post(f"{BASE_URL}/discover-leads-step1", json={
    "company_name": "Mayo Clinic",
    "company_state": "Minnesota"
})
data1 = response1.json()["data"]

# Step 2: Deduplicate + Enrich
response2 = requests.post(f"{BASE_URL}/discover-leads-step2", json={
    "serper_prospects": data1["serper_prospects"],
    "brightdata_prospects": data1["brightdata_prospects"],
    "company_name": "Mayo Clinic"
})
data2 = response2.json()["data"]

# Step 3: AI Ranking
response3 = requests.post(f"{BASE_URL}/discover-leads-step3", json={
    "enriched_prospects": data2["enriched_prospects"],
    "company_name": "Mayo Clinic"
})
data3 = response3.json()["data"]

# Step 4: Queue Leads
response4 = requests.post(f"{BASE_URL}/discover-leads-step4", json={
    "qualified_prospects": data3["qualified_prospects"],
    "company_name": "Mayo Clinic"
})
print(f"Queued {response4.json()['data']['queued']} leads for approval")
```

---

## Next Steps

### Immediate
- [x] Complete implementation
- [x] Add to documentation
- [x] Create test script
- [ ] **Test locally with real company** ← YOU ARE HERE
- [ ] Verify leads appear in dashboard
- [ ] Deploy to Railway
- [ ] Test in production environment

### Future Enhancements (Optional)
- [ ] Add webhook notifications when leads are queued
- [ ] Email alerts for pending approvals
- [ ] Bulk approval API endpoint
- [ ] Lead deduplication against existing Salesforce Leads
- [ ] Scheduled/automated lead discovery (cron jobs)
- [ ] Export leads to CSV from dashboard
- [ ] Lead scoring confidence intervals

---

## Success Metrics

### Coverage Improvement
- **Before**: Single source (either Serper OR Bright Data)
- **After**: Dual source (Serper AND Bright Data)
- **Expected**: 20-50% more prospects discovered

### Data Quality
- **Deduplication**: Eliminates redundant prospects
- **Preference**: Chooses richer Bright Data profiles
- **Validation**: Multiple filters ensure quality

### User Experience
- **Approval Workflow**: Manual review before Salesforce import
- **Dashboard Integration**: One-click approve/reject
- **Transparency**: Full prospect details visible

---

## Summary

✅ **Complete hybrid pipeline implemented with minimal code changes**
✅ **4 new API endpoints for the 4-step workflow**
✅ **PendingUpdates system extended to support Lead records**
✅ **Dashboard updated with new card and lead display**
✅ **Test script created for local development**
✅ **Documentation updated in CLAUDE.md and this file**

**Ready for testing!** Run `python test_hybrid_pipeline.py` to test locally.
