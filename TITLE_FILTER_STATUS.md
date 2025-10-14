# Title Filter Implementation Status

**Date:** October 14, 2025
**Status:** ⚠️ PARTIALLY IMPLEMENTED - NOT WORKING AS EXPECTED

---

## 🎯 Objective

**Filter out clinical roles (cardiovascular, wound care, radiology, emergency, etc.) BEFORE LinkedIn scraping** to:
1. Save costs (~$0.47 per clinical role not scraped)
2. Improve accuracy (clinical directors are not buyers for building infrastructure)
3. Speed up processing (fewer profiles to scrape and rank)

---

## ✅ What Was Implemented

### 1. New AI Title Filter Prompts (v2.0)
**Location:** `app/prompts.py:158-217`

**System Prompt:**
- Clear directive: "We sell building infrastructure, NOT healthcare services"
- Instructions to AGGRESSIVELY REJECT clinical/medical/patient care roles

**User Prompt Template:**
- Comprehensive rejection keyword list (30+ clinical terms)
- Keywords include: cardiovascular, surgery, wound, radiology, emergency, nursing, etc.
- Scoring: 0-39 = REJECT, 70-100 = ACCEPT
- Minimum passing score: 55 (but 70+ recommended)

**Rejection Keywords Added:**
- cardiovascular, cardiac, heart
- surgery, surgical, surgeon, operating room
- emergency, ER, trauma
- radiology, imaging, diagnostic
- oncology, cancer
- pediatric, pediatrics
- OB/GYN, women's health
- neurology, neuro, brain
- wound, wound care
- clinical, medical, physician, doctor, MD, RN
- nursing, nurse, patient care
- pharmacy, respiratory, therapy
- dietary, nutrition, food service
- social work, case management

### 2. Title Filter Integration
**Location:** `app/services/improved_prospect_discovery.py:780-853`

**Function:** `_ai_title_filter_prospects()`
- Scores each prospect's title using AI
- Runs in parallel with `asyncio.gather()`
- Filters prospects with score < 55
- Adds `ai_title_filter` metadata to each prospect

**Function:** `_score_title_relevance()`
- Individual AI calls per prospect
- Uses GPT-5 Responses API
- Returns score and reasoning

---

## ❌ What's NOT Working

### 1. Title Filter Metrics Show "0"
**Evidence:**
```
After AI Title Filter: 0
Filtered by Title: 0
```

**Problem:** The pipeline summary shows 0 prospects after title filtering, but:
- LinkedIn scraping still happens (111 profiles scraped in St. Vincent test)
- Clinical roles still appear in final results

### 2. Clinical Roles Still Being Scraped
**Evidence from St. Vincent Healthcare test:**
- "Director Cardiovascular Service Line" (scraped & scored 90/100)
- "Director of Wound Care Clinic" (scraped & scored 87/100)
- "Director Cardiovascular Imaging" (scraped & scored 77/100)
- "Director of Radiology" (scraped & scored 71/100)

**Expected:** These should have been filtered out BEFORE scraping

### 3. Test Results Show No Cost Savings
```
LinkedIn profiles saved from scraping: 0
Cost savings: $0.00
```

**Problem:** Title filter is not preventing scraping, so no cost savings

---

## 🐛 Root Cause Analysis

### Hypothesis 1: Filter Not Blocking Scraping
The title filter may be scoring prospects correctly but **not preventing them from being passed to LinkedIn scraping**.

**Evidence:**
- `prospects_after_ai_title_filter` shows 0
- But `linkedin_profiles_scraped` shows 111
- This suggests the filter runs, but the filtered list isn't used

**Code to Check:**
```python
# improved_prospect_discovery.py:176
linkedin_urls = [p.get("link") for p in ai_filtered_prospects if p.get("link")]
```

If `ai_filtered_prospects` is empty (0 prospects), why are 111 profiles being scraped?

### Hypothesis 2: Filter Runs After Scraping
The title filter may be running in the wrong order in the pipeline.

**Expected Order:**
1. Search → 2. Basic Filter → 3. Title Filter → 4. LinkedIn Scrape → 5. Advanced Filter → 6. AI Ranking

**Actual Order (suspected):**
1. Search → 2. Basic Filter → 3. LinkedIn Scrape → 4. Title Filter (too late!) → 5. Advanced Filter → 6. AI Ranking

### Hypothesis 3: Old Code Still Running
The server may not have picked up the new code changes.

**Evidence:**
- St. Vincent test (after code changes) shows same results as before
- No change in filtering behavior

---

## 🔍 Debugging Steps Needed

1. **Check Pipeline Order**
   - Verify title filter runs at Step 3.5 (before scraping)
   - Check that `ai_filtered_prospects` is properly passed to scraping step

2. **Add Debug Logging**
   ```python
   logger.info(f"Title filter: {len(filtered_prospects)} → {len(ai_filtered_prospects)}")
   logger.info(f"Passing {len(ai_filtered_prospects)} prospects to LinkedIn scraping")
   ```

3. **Verify Filter is Running**
   - Check if `_ai_title_filter_prospects()` is actually being called
   - Log each prospect's title and filter score

4. **Test Filter Logic Directly**
   - Create unit test that calls title filter on known clinical titles
   - Verify scores < 55 for clinical roles

---

## 📊 Expected vs Actual Results

### St. Vincent Healthcare Test

| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| Search Results | 229 | 229 | ✓ |
| After Basic Filter | ~180 | 178 | ✓ |
| **After Title Filter** | **~30-40** | **0 (reported)** | ❌ |
| **LinkedIn Scraped** | **~30-40** | **111** | ❌ |
| After Advanced Filter | ~20-30 | 23 | ✓ |
| Final Prospects | ~5-8 | 8 | ✓ |

**Key Issue:** Title filter reports 0 prospects, but 111 are still scraped. This suggests:
- Either the filter isn't running
- Or the filtered list isn't being used for scraping
- Or there's a logic error in how the filter results are applied

---

## 💰 Cost Impact

### Current (Without Working Title Filter)
- **Search:** 229 results
- **Scraped:** 111 profiles
- **Clinical roles scraped:** ~80 (estimated)
- **Wasted scraping cost:** 80 × $0.0047 = **$0.38 per hospital**

### Expected (With Working Title Filter)
- **Search:** 229 results
- **After title filter:** ~40 prospects
- **Scraped:** ~40 profiles
- **Clinical roles rejected:** ~140
- **Cost savings:** 140 × $0.0047 = **$0.66 saved per hospital**

### Annual Impact (500 hospitals/year)
- **Current waste:** $190/year on irrelevant scraping
- **Potential savings:** $330/year with working title filter

---

## 🔧 Next Steps

### Immediate (Critical)
1. **Debug why title filter metrics show "0"**
   - Add extensive logging to `_ai_title_filter_prospects()`
   - Log before/after counts at each step

2. **Verify filter is blocking scraping**
   - Check that `linkedin_urls` list uses filtered prospects
   - Add assertion: `assert len(ai_filtered_prospects) > 0, "Title filter removed all prospects"`

3. **Test with smaller dataset**
   - Use 10-20 prospects mix of clinical and facilities roles
   - Manually verify clinical roles are filtered

### Short-term
4. **Add fallback logic**
   - If title filter removes ALL prospects, log warning but continue
   - This prevents complete pipeline failure

5. **Improve reporting**
   - Fix `prospects_after_ai_title_filter` metric
   - Show actual filtered count, not "0"

6. **Add cost tracking**
   - Log actual vs potential scraping costs
   - Show savings from title filtering

### Long-term
7. **Consider hybrid approach**
   - Rule-based pre-filter for obvious clinical keywords
   - AI filter for borderline cases
   - Faster and cheaper than pure AI

8. **Add integration tests**
   - Automated test with known clinical/facilities titles
   - Verify expected filtering behavior

---

## 📝 Code Locations

- **Prompts:** `app/prompts.py:158-217`
- **Title Filter Function:** `app/services/improved_prospect_discovery.py:780-853`
- **Pipeline Orchestration:** `app/services/improved_prospect_discovery.py:28-285`
- **Scoring Function:** `app/services/improved_prospect_discovery.py:855-936`

---

## 🎯 Success Criteria

Title filter will be considered working when:

1. ✓ Clinical roles score < 40 (IMPLEMENTED)
2. ✓ Facilities/Finance roles score 70+ (IMPLEMENTED)
3. ❌ **Title filter metrics show actual filtered count** (NOT WORKING)
4. ❌ **LinkedIn scraping only processes filtered prospects** (NOT WORKING)
5. ❌ **Cost savings measurable** (NOT WORKING)
6. ❌ **No clinical roles in final results** (NOT WORKING)

**Current Status:** 2/6 criteria met

---

**Last Updated:** October 14, 2025, 11:59 AM
**Test Hospital:** St. Vincent Healthcare, Billings, MT
**Test Status:** Filter implemented but not preventing clinical role scraping
