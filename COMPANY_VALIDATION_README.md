# Company Validation System

## Overview

The Company Validation System is a new AI-powered validation layer that ensures prospects currently work at the target company and handles company name variations. This system addresses the critical need to filter out former employees and account for different company name formats.

## Problem Solved

### Before
- Prospects could include former employees who no longer work at the target company
- Company name variations (e.g., "UCI Medical Center" vs "UCI Health" vs "UC Irvine") were not handled
- No systematic way to verify current employment status

### After
- AI-powered validation using OpenAI to analyze LinkedIn titles and descriptions
- Intelligent handling of company name variations and subsidiaries
- Confidence scoring for employment validation
- Integrated into the prospect discovery pipeline as Step 2

## How It Works

### 1. Company Validation Service (`company_validation.py`)

The service uses OpenAI GPT-4 to analyze prospect data and determine current employment:

```python
from app.services.company_validation import company_validation_service

result = await company_validation_service.validate_current_employment(
    prospects=search_results,
    target_company="UCI Medical Center"
)
```

### 2. Validation Criteria

The AI analyzes:
- **LinkedIn Title Format**: "Name - Job Title at Company"
- **Job Description**: Current role details and employment timeline
- **Employment Indicators**: Present vs. past tense language
- **Company Variations**: Handles subsidiaries and name variations

### 3. Company Name Variation Handling

Examples of variations the system recognizes:
- "UCI Medical Center" = "UCI Health" = "UC Irvine Health" = "University of California Irvine Health"
- "Mayo Clinic" = "Mayo Clinic Health System" = "Mayo One"
- "Johns Hopkins" = "Johns Hopkins Medicine" = "Johns Hopkins Hospital"
- "Cleveland Clinic" = "Cleveland Clinic Foundation"

### 4. Confidence Scoring

- **90-100%**: Clear current employment with exact/obvious company match
- **70-89%**: Strong indicators with company variation match
- **50-69%**: Probable current employment but some uncertainty
- **30-49%**: Uncertain employment status
- **0-29%**: Likely past employment or different company

Only prospects with confidence ≥ 70% pass validation.

## Integration with Prospect Discovery Pipeline

The validation is now integrated as Step 2 in the prospect discovery pipeline:

1. **Search** - Find LinkedIn profiles using Serper
2. **🆕 Validation** - Verify current employment at target company
3. **Qualification** - AI qualification of validated prospects
4. **LinkedIn Scraping** - Detailed data for top prospects
5. **Combine Results** - Final prospect data

### Updated Pipeline Flow

```python
# Step 1: Search for LinkedIn profiles
search_result = await self.search_service.search_linkedin_profiles(...)

# Step 2: Validate current employment (NEW!)
validation_result = await self.validation_service.validate_current_employment(
    prospects=search_results,
    target_company=company_name
)

# Step 3: Qualify validated prospects
qualification_result = await self.ai_service.qualify_prospects(
    search_results=validated_prospects,  # Only validated prospects
    company_name=company_name
)
```

## Enhanced AI Qualification

The AI qualification service has been updated to consider employment validation data:

### New Scoring Criteria
- Job title relevance to energy/facilities decisions (35%)
- Decision-making authority level (25%)
- **🆕 Employment validation confidence (20%)**
- Company size and budget likelihood (15%)
- Accessibility and engagement potential (5%)

### Employment Confidence Bonus
- **+10 points** for high validation confidence (90-100%)
- **+5 points** for medium validation confidence (70-89%)
- **No bonus** for low confidence (<70%)

## API Response Structure

### Validation Results

```json
{
  "success": true,
  "target_company": "UCI Medical Center",
  "total_prospects_analyzed": 10,
  "currently_employed_count": 6,
  "validated_prospects": [...],
  "validation_details": {
    "validation_results": [
      {
        "index": 0,
        "currently_employed": true,
        "confidence_score": 95,
        "employment_status": "current",
        "company_match_type": "variation",
        "detected_company_name": "UCI Health",
        "validation_reasoning": "LinkedIn title shows current role as Director of Facilities at UCI Health...",
        "red_flags": [],
        "employment_indicators": ["current title shows...", "active role description..."]
      }
    ],
    "company_variations_detected": ["UCI Health", "UC Irvine Medical"],
    "validation_summary": {
      "total_analyzed": 10,
      "currently_employed": 6,
      "employment_verified": 5,
      "employment_uncertain": 1
    }
  },
  "cost_estimate": 0.015
}
```

### Enhanced Prospect Data

Each validated prospect now includes employment validation data:

```json
{
  "title": "John Smith - Director of Facilities at UCI Health",
  "employment_validation": {
    "currently_employed": true,
    "confidence_score": 95,
    "employment_status": "current",
    "company_match_type": "variation",
    "detected_company_name": "UCI Health",
    "validation_reasoning": "Clear current employment indicators...",
    "red_flags": [],
    "employment_indicators": ["current title", "active role"]
  },
  "validation_passed": true
}
```

## Cost Estimates

- **Validation Cost**: ~$0.015 per batch of prospects
- **Total Pipeline Cost**: Search + Validation + Qualification + LinkedIn
- Cost is added to the pipeline summary in the final response

## Testing

### Test the Validation Service

```bash
# Run the validation test script
cd fast_leads_api
python test_company_validation.py
```

### Test All Services

```python
from app.services.prospect_discovery import prospect_discovery_service

# Test all services including validation
result = await prospect_discovery_service.test_services()
print(result["service_tests"]["validation_service"])
```

## Error Handling

- **Missing OpenAI API Key**: Service fails gracefully, continues with original prospects
- **API Errors**: Logs warning, continues pipeline with unvalidated prospects
- **Invalid Prospect Data**: Skips invalid prospects, processes remaining ones

## Configuration

### Required Environment Variables

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### Service Configuration

The validation service is automatically imported and configured:

```python
# In prospect_discovery.py
from .company_validation import company_validation_service

class ProspectDiscoveryService:
    def __init__(self):
        self.validation_service = company_validation_service
```

## Benefits

1. **Higher Quality Leads**: Only current employees are qualified
2. **Better Conversion**: Outreach to people who can actually make decisions
3. **Cost Efficiency**: No wasted effort on former employees
4. **Company Variations**: Handles complex healthcare system naming
5. **Confidence Scoring**: Know how certain the validation is
6. **Detailed Insights**: Rich validation reasoning for each prospect

## Future Enhancements

- **Caching**: Cache validation results to avoid re-processing
- **Batch Optimization**: Optimize API calls for large prospect lists
- **Company Database**: Build database of known company variations
- **Real-time Updates**: Monitor for employment changes over time
