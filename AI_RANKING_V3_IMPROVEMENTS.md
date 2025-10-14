# AI Ranking v3.0 - Improvements Summary

**Date:** October 7, 2025
**Status:** Ready for Testing

---

## Changes Made

### 1. **Upgraded to GPT-5 with Reasoning** 🚀

**Previous:** `gpt-4o-mini`
**New:** `gpt-5` with `minimal` reasoning effort

**Why:** GPT-5 is OpenAI's most intelligent model yet, specifically trained for:
- Better instruction following
- More accurate scoring and classification
- Improved reasoning for nuanced role distinctions

Using `minimal` reasoning effort provides:
- Fast response times (similar to GPT-4.1)
- Improved accuracy over non-reasoning models
- Better cost efficiency than `medium` or `high` reasoning

**File:** `/app/services/improved_ai_ranking.py:30-32`

```python
# Use GPT-5 for best prospect scoring accuracy with reasoning
self.model = os.getenv('OPENAI_MODEL', 'gpt-5')
# Use minimal reasoning for fast, accurate scoring
self.reasoning_effort = os.getenv('OPENAI_REASONING_EFFORT', 'minimal')
```

---

### 2. **Simplified AI Ranking Prompt** ✨

**Previous:** Complex 140-line rubric with detailed point scoring (Role Match 40pts + Technical 30pts + Budget 20pts + Experience 10pts)

**New:** Simplified, conversational prompt focused on who actually buys infrastructure projects

**File:** `/app/prompts.py:63-116`

#### Key Improvements:

**Clearer System Prompt:**
```
You are an expert at scoring B2B prospects for energy infrastructure sales to hospitals.

Score each prospect 0-100 based on their ability to influence or approve large infrastructure projects ($500K-$5M).

Key principle: Operations and Finance roles that manage buildings and budgets score HIGH. Clinical roles (doctors, nurses, surgeons) score LOW.
```

**Simplified User Prompt:**
- Removed complex point breakdown (38+28+18+9 = 93)
- Added clear scoring ranges:
  - 85-100: Perfect match (Director+ Facilities/Engineering/Finance)
  - 70-84: Strong prospect (Manager+ facilities/operations/finance)
  - 50-69: Possible contact (junior or adjacent roles)
  - 0-49: Not a buyer (clinical, support, unrelated)

**Better Examples:**
- "Director of Facilities, 12 years" → 92 (perfect: senior facilities leader)
- "Director of Operations, 15 years" → 78 (strong: operations leadership)
- "VP Surgical Services, 10 years" → 25 (clinical role, not a buyer)

**Simpler JSON Response:**
```json
{
  "score": 92,
  "reasoning": "Senior facilities leader with budget authority"
}
```

Instead of:
```json
{
  "reasoning": "Role(38) + Technical(28) + Budget(18) + Exp(9) = 93",
  "score": 93
}
```

---

### 3. **Enhanced Error Handling and Logging** 🔍

**Added comprehensive error tracking:**

#### Error Collection (`improved_ai_ranking.py:73-83`)
```python
# Track errors for debugging
errors = []
for i, result in enumerate(ranking_results):
    if isinstance(result, Exception):
        error_msg = f"Prospect {i}: {type(result).__name__}: {str(result)}"
        errors.append(error_msg)
        logger.error(error_msg)
    elif isinstance(result, dict) and not result.get("success"):
        error_msg = f"Prospect {i}: {result.get('error', 'Unknown error')}"
        errors.append(error_msg)
        logger.error(error_msg)
```

#### Specific Exception Handling (`improved_ai_ranking.py:191-212`)
- `json.JSONDecodeError` - Catches malformed JSON responses
- `openai.APITimeoutError` - Catches API timeouts (30s limit per request)
- `openai.RateLimitError` - Catches rate limit errors with 2s retry delay
- Generic `Exception` - Catches all other errors

#### Enhanced Response Data
```python
return {
    "success": True,
    "total_prospects": 32,
    "successfully_ranked": 28,
    "failed_rankings": 4,
    "errors": [
        "Prospect 5: APITimeoutError: Request timed out",
        "Prospect 12: RateLimitError: Rate limit exceeded"
    ],
    "ranked_prospects": [...]
}
```

**Previous:** Silent failures, no error tracking
**New:** Every error is logged and returned in response

---

### 4. **Added Request Timeouts** ⏱️

**File:** `/app/services/improved_ai_ranking.py:168`

```python
response = self.client.chat.completions.create(
    model=self.model,
    timeout=30  # 30 second timeout per request
    # ...
)
```

**Why:** Prevents hanging requests from blocking the entire pipeline.

---

### 5. **Improved Debug Logging** 📝

**Added logging at key points:**

```python
logger.info(f"Starting AI ranking for {len(prospects)} prospects using {self.model}")
logger.debug(f"Ranking prospect {index} ({prospect_data.get('name', 'Unknown')}), attempt {attempt + 1}")
logger.debug(f"Successfully ranked prospect {index}: {ranking_data['score']}/100")
logger.info(f"AI ranking complete: {successful_rankings}/{len(prospects)} succeeded")
```

**Benefits:**
- Track which prospects are being ranked in real-time
- See success/failure rates
- Identify bottlenecks

---

## Expected Improvements

### 1. **Better Scoring Accuracy**

**Problem:** GPT-4o-mini was giving low scores to good prospects like:
- Ryan Hutchinson (Director of Operations) - should score 75-85
- Susan Sauder (CFO Southern Oregon) - should score 85-90

**Solution:** GPT-4.5 has better reasoning and should correctly identify these as high-value prospects.

---

### 2. **Fewer AI Ranking Failures**

**Problem:** All 32 Providence Medford prospects had empty `ai_ranking` objects

**Possible Causes:**
- Silent API failures
- Timeout issues
- JSON parsing errors
- Rate limiting

**Solution:**
- Explicit timeout handling (30s per request)
- Retry logic with delays for rate limits
- Detailed error logging for every failure type
- Error messages included in response

---

### 3. **More Consistent Scoring**

**Problem:** Complex rubric (Role 40pts + Technical 30pts + Budget 20pts + Experience 10pts) might confuse the AI

**Solution:** Simplified scoring guide with clear ranges:
- Perfect match (85-100)
- Strong prospect (70-84)
- Possible contact (50-69)
- Not a buyer (0-49)

---

### 4. **Better Clinical Role Detection**

**Problem:** Clinical roles like "VP Surgical Services" or "Clinical Pharmacist" sometimes scored too high

**Solution:**
- Clear "WHO DOES NOT BUY" section in prompt
- Explicit examples of clinical roles scoring <50
- Stronger language: "Clinical roles: Doctors, nurses, surgeons, medical directors, clinical department heads"

---

## Cost Impact

**Previous:** `gpt-4o-mini` (~$0.001 per prospect)
**New:** `gpt-5` with minimal reasoning (~$0.003 per prospect)

**For 32 prospects:**
- Previous: $0.032
- New: $0.096
- Increase: $0.064 (~200% more)

**Justification:** 3x cost increase is worth it for accurate prospect identification with reasoning capabilities. Missing 1 good prospect (like Ryan Hutchinson) costs far more than $0.064 in lost sales opportunity.

**Note:** Can adjust reasoning effort via environment variable:
- `OPENAI_REASONING_EFFORT=minimal` (fastest, default)
- `OPENAI_REASONING_EFFORT=low` (more thorough)
- `OPENAI_REASONING_EFFORT=medium` (balanced)
- `OPENAI_REASONING_EFFORT=high` (most thorough, slowest)

---

## Testing Recommendations

### Test 1: Re-run Providence Medford
```bash
python test_providence_medford.py
```

**Expected Results:**
- Ryan Hutchinson (Director of Operations) → 75-85 score ✅
- Susan Sauder (CFO) → 85-90 score ✅
- Cylix Shane (Facilities Planner, Portland) → 55-65 score (location penalty) ⚠️
- Clinical roles → <50 scores ❌

**Success Criteria:**
- ≥90% of prospects successfully ranked (no empty `ai_ranking` objects)
- 3-5 prospects score ≥70 (not just 1)
- Errors logged in response JSON if any failures occur

---

### Test 2: Test on Known Good Prospect Set (MedStar)
```bash
python test_medstar_improved.py
```

**Expected Results:**
- Higher quality scores for facilities directors
- Lower scores for clinical roles
- More prospects meeting ≥70 threshold

---

### Test 3: Monitor Logs for Errors
```bash
# Run server with visible logs
hypercorn main:app --reload

# In another terminal, run test
python test_providence_medford.py

# Check logs for:
# - "Starting AI ranking for X prospects using gpt-4.5-preview"
# - "Successfully ranked prospect X: Y/100"
# - "AI ranking complete: X/Y succeeded"
# - Any error messages
```

---

## Rollback Plan

If GPT-5 performs worse or has issues:

**Option 1: Revert to GPT-4o-mini**
```bash
# In .env file
OPENAI_MODEL=gpt-4o-mini
```

**Option 2: Try GPT-4.1 (fast non-reasoning model)**
```bash
OPENAI_MODEL=gpt-4.1
```

**Option 3: Try GPT-5-mini (smaller, faster reasoning model)**
```bash
OPENAI_MODEL=gpt-5-mini
OPENAI_REASONING_EFFORT=minimal
```

**Option 4: Adjust reasoning effort only**
```bash
# Keep GPT-5 but reduce reasoning overhead
OPENAI_MODEL=gpt-5
OPENAI_REASONING_EFFORT=low  # or medium/high
```

---

## Files Modified

1. ✅ `/app/prompts.py` (lines 63-116) - Simplified AI ranking prompt
2. ✅ `/app/services/improved_ai_ranking.py` (line 30) - Model upgrade to GPT-4.5
3. ✅ `/app/services/improved_ai_ranking.py` (lines 62-115) - Enhanced error handling
4. ✅ `/app/services/improved_ai_ranking.py` (lines 146-214) - Individual ranking improvements
5. ✅ `/app/prompts.py` (lines 212-228) - Updated version metadata

---

## Next Steps

1. **Test Providence Medford** with new AI ranking
2. **Review error logs** to see if failures are resolved
3. **Compare scores** between v2.0 (complex rubric) and v3.0 (simplified)
4. **Analyze cost** - is 2x cost justified by better accuracy?
5. **Fine-tune threshold** - should we lower from 70 to 65 if we're being too strict?

---

## Summary

**What Changed:**
- ✅ Upgraded to GPT-5 with minimal reasoning for best accuracy
- ✅ Simplified prompt from complex rubric to clear scoring guide
- ✅ Added comprehensive error tracking and logging
- ✅ Added timeout handling (30s per request)
- ✅ Improved retry logic with rate limit handling
- ✅ Configurable reasoning effort via environment variable

**Expected Outcomes:**
- ✅ Ryan Hutchinson and similar prospects score ≥70
- ✅ Clinical roles consistently score <50
- ✅ AI ranking failures reduced from ~97% to <10%
- ✅ Error messages visible for debugging
- ✅ Better instruction following with reasoning model

**Trade-offs:**
- ⚠️ 3x cost increase ($0.001 → $0.003 per prospect)
- ✅ Worth it for accurate prospect identification with reasoning
- ⚠️ Slightly slower than gpt-4o-mini (but minimal reasoning keeps it fast)

---

**Ready for Testing:** Yes ✅
**Backward Compatible:** Yes (can revert via environment variable)
**Breaking Changes:** None
