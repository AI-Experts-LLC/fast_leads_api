# AI Prompts - Centralized Configuration

All AI prompts used in the prospect discovery pipeline are now centralized in `/app/prompts.py`.

## Location

**File:** `/app/prompts.py`

This file contains all system and user prompts as named global variables that can be easily reviewed and edited.

## Prompts Inventory

### 1. Company Name Expansion
- `COMPANY_NAME_EXPANSION_SYSTEM_PROMPT` - System prompt for AI
- `COMPANY_NAME_EXPANSION_USER_PROMPT_TEMPLATE` - User prompt template with placeholders

**Used in:** `app/services/company_name_expansion.py`

**Purpose:** Generates variations of company names for better LinkedIn search coverage

---

### 2. AI Ranking (Improved Pipeline) ⭐ PRIMARY
- `AI_RANKING_SYSTEM_PROMPT` - Strict scoring system instructions
- `AI_RANKING_USER_PROMPT_TEMPLATE` - Detailed scoring rubric with examples

**Used in:** `app/services/improved_ai_ranking.py`

**Purpose:** Scores prospects 0-100 based on buyer fit for energy infrastructure sales

**Key Scoring Criteria:**
- Role Match (40 pts)
- Technical Relevance (30 pts)
- Budget Authority (20 pts)
- Experience (10 pts)

---

### 3. Company Employment Validation
- `COMPANY_VALIDATION_SYSTEM_PROMPT` - Employment verification expert
- `COMPANY_VALIDATION_USER_PROMPT_TEMPLATE` - Validates current employment

**Used in:** `app/services/company_validation.py`

**Purpose:** Verifies if prospect currently works at target company

---

### 4. AI Qualification (Original Pipeline) - DEPRECATED
- `AI_QUALIFICATION_SYSTEM_PROMPT_ORIGINAL` - Legacy qualification logic
- `AI_QUALIFICATION_USER_PROMPT_ORIGINAL` - Original user prompt

**Used in:** `app/services/ai_qualification.py`

**Status:** Deprecated in favor of improved pipeline

---

### 5. Additional Prompts (Not Yet Used)
- `TITLE_RELEVANCE_CHECK_PROMPT` - Checks if job title is relevant
- `PERSONA_CLASSIFICATION_PROMPT` - Classifies prospects into buyer personas
- `SEARCH_QUERY_OPTIMIZATION_PROMPT` - Generates optimized search queries

**Status:** Defined but not currently integrated

---

## How to Edit Prompts

1. Open `/app/prompts.py`
2. Find the prompt you want to edit (search by name)
3. Make your changes
4. Save the file
5. Restart the API server (`hypercorn main:app --reload`)

## Prompt Template Variables

Most prompts use `.format()` placeholders:

**Example:**
```python
AI_RANKING_USER_PROMPT_TEMPLATE = """
Analyze prospect for {company_name}

Name: {name}
Title: {title}
...
"""
```

**Available Variables:**
- `{company_name}` - Target company
- `{name}` - Prospect name
- `{title}` - Job title
- `{company}` - Current company
- `{summary}` - LinkedIn summary
- `{skills}` - Top skills list
- `{experience_years}` - Years of experience
- `{company_city}` - Company location city
- `{company_state}` - Company location state

---

## Files Updated

The following service files now import and use centralized prompts:

1. ✅ `/app/services/improved_ai_ranking.py`
2. ✅ `/app/services/company_name_expansion.py`
3. `/app/services/company_validation.py` (uses prompts - needs import update)
4. `/app/services/ai_qualification.py` (deprecated, not updated)

---

## Prompt Versions

Track prompt versions in `/app/prompts.py`:

```python
PROMPT_VERSIONS = {
    "company_expansion": "v1.0",
    "company_validation": "v1.0",
    "ai_ranking": "v2.0",  # Improved version
    "ai_qualification_original": "v1.0",  # Deprecated
}
```

---

## Benefits

✅ **Single source of truth** - All prompts in one file
✅ **Easy to review** - See all AI instructions at once
✅ **Easy to edit** - No hunting through code
✅ **Version control** - Track prompt changes in git
✅ **Consistent formatting** - Standardized templates
✅ **Reusable** - Same prompts can be used across services

---

## Next Steps

To complete centralization:

1. Update `company_validation.py` to import prompts
2. Remove hardcoded prompts from any remaining services
3. Add prompt versioning to API responses (optional)
4. Create prompt testing framework (optional)
