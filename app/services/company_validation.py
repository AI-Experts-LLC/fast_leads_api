"""
Company validation service using OpenAI to verify current employment
and handle company name variations
"""

import os
import logging
from typing import List, Dict, Any, Optional
import openai
from openai import OpenAI
import json

logger = logging.getLogger(__name__)


class CompanyValidationService:
    """Service for validating prospect current employment using AI"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')  # Default to gpt-4o-mini
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            logger.info(f"Company validation initialized with model: {self.model}")
        else:
            self.client = None
            logger.warning("OPENAI_API_KEY not found in environment variables")
    
    async def validate_current_employment(self, prospects: List[Dict], target_company: str) -> Dict[str, Any]:
        """
        Validate that prospects currently work at the target company or its variations
        
        Args:
            prospects: List of prospect data with LinkedIn titles and snippets
            target_company: The target company name to validate against
        
        Returns:
            Dictionary with validated prospects and validation details
        """
        if not self.client:
            return {
                "success": False,
                "error": "OpenAI client not configured - missing API key"
            }
        
        if not prospects:
            return {
                "success": False,
                "error": "No prospects to validate"
            }
        
        try:
            # Prepare validation data
            validation_data = []
            for i, prospect in enumerate(prospects):
                validation_data.append({
                    "index": i,
                    "linkedin_title": prospect.get("title", ""),
                    "linkedin_snippet": prospect.get("snippet", ""),
                    "linkedin_url": prospect.get("link", ""),
                    "search_context": prospect.get("target_title", "")
                })
            
            # Create validation prompt
            prompt = self._build_validation_prompt(validation_data, target_company)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert data analyst specializing in employment verification and company name matching. You excel at identifying company name variations and determining current vs. past employment."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Lower temperature for more consistent validation
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            # Parse validation response
            validation_result = json.loads(response.choices[0].message.content)
            
            # Process and filter prospects
            validated_prospects = self._process_validation_result(
                validation_result, prospects, target_company
            )
            
            return {
                "success": True,
                "target_company": target_company,
                "total_prospects_analyzed": len(prospects),
                "currently_employed_count": len(validated_prospects),
                "validated_prospects": validated_prospects,
                "validation_details": validation_result,
                "cost_estimate": 0.0008  # Updated for gpt-4o-mini pricing
            }
            
        except Exception as e:
            logger.error(f"Error validating employment: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_validation_prompt(self, prospects: List[Dict], target_company: str) -> str:
        """Build the company validation prompt"""
        return f"""
Analyze these LinkedIn prospects to determine if they CURRENTLY work at "{target_company}" or its variations.

CRITICAL VALIDATION RULES:
1. CURRENT EMPLOYMENT ONLY - Reject if they previously worked there but moved to a different company
2. COMPANY NAME VARIATIONS - Accept variations like:
   - "UCI Medical Center" = "UCI Health" = "UC Irvine Health" = "University of California Irvine Health"
   - "Mayo Clinic" = "Mayo Clinic Health System" = "Mayo One"
   - "Johns Hopkins" = "Johns Hopkins Medicine" = "Johns Hopkins Hospital"
   - "Cleveland Clinic" = "Cleveland Clinic Foundation"
3. DIVISION/SUBSIDIARY MATCHING - Accept if they work at a division/subsidiary of the target company
4. KEYWORD ANALYSIS - Look for employment indicators in job descriptions, not just company names

Target Company: {target_company}

Prospects to validate:
{json.dumps(prospects, indent=2)}

For each prospect, analyze:
- LinkedIn title format: "Name - Job Title at Company" 
- LinkedIn snippet: Job description and current role details
- Employment timeline indicators (current vs. past tense)
- Company name variations and subsidiaries

Return JSON with this exact structure:
{{
  "validation_results": [
    {{
      "index": 0,
      "currently_employed": true,
      "confidence_score": 95,
      "employment_status": "current",
      "company_match_type": "exact_match|variation|subsidiary|division",
      "detected_company_name": "Actual company name found",
      "validation_reasoning": "Specific evidence for this determination",
      "red_flags": ["any concerns about employment status"],
      "employment_indicators": ["current title shows...", "active role description..."]
    }}
  ],
  "company_variations_detected": [
    "List of company name variations found in the data"
  ],
  "validation_summary": {{
    "total_analyzed": 5,
    "currently_employed": 3,
    "employment_verified": 2,
    "employment_uncertain": 1,
    "common_variations": ["UCI Health", "UC Irvine Medical"]
  }}
}}

SCORING CRITERIA (0-100 confidence):
- 90-100: Clear current employment with exact/obvious company match
- 70-89: Strong indicators of current employment with company variation match
- 50-69: Probable current employment but some uncertainty
- 30-49: Uncertain employment status or weak company connection
- 0-29: Likely past employment or different company

Only mark "currently_employed": true for confidence scores ≥ 70.
"""
    
    def _process_validation_result(self, validation_result: Dict, original_prospects: List[Dict], target_company: str) -> List[Dict]:
        """Process validation results and return validated prospects"""
        validated_prospects = []
        
        validation_results = validation_result.get("validation_results", [])
        
        for result in validation_results:
            index = result.get("index", -1)
            if 0 <= index < len(original_prospects) and result.get("currently_employed", False):
                # Combine original prospect data with validation results
                validated_prospect = {
                    **original_prospects[index],  # Original search data
                    "employment_validation": {
                        "currently_employed": result.get("currently_employed", False),
                        "confidence_score": result.get("confidence_score", 0),
                        "employment_status": result.get("employment_status", ""),
                        "company_match_type": result.get("company_match_type", ""),
                        "detected_company_name": result.get("detected_company_name", ""),
                        "validation_reasoning": result.get("validation_reasoning", ""),
                        "red_flags": result.get("red_flags", []),
                        "employment_indicators": result.get("employment_indicators", [])
                    },
                    "validation_passed": True,
                    "validation_timestamp": None  # Would add timestamp in production
                }
                validated_prospects.append(validated_prospect)
        
        return validated_prospects
    
    async def test_validation(self) -> Dict[str, Any]:
        """Test the validation functionality with sample data"""
        if not self.client:
            return {
                "success": False,
                "error": "OpenAI client not configured"
            }
        
        # Test data with various employment scenarios
        test_prospects = [
            {
                "title": "John Smith - Director of Facilities at UCI Health",
                "snippet": "Experienced facilities director currently managing infrastructure and maintenance operations at UCI Health medical center",
                "link": "https://linkedin.com/in/johnsmith",
                "target_title": "Director of Facilities"
            },
            {
                "title": "Jane Doe - Former CFO at UCI Medical Center, now at ABC Corp",
                "snippet": "Previously served as CFO at UCI Medical Center for 5 years. Currently Chief Financial Officer at ABC Corporation",
                "link": "https://linkedin.com/in/janedoe",
                "target_title": "CFO"
            },
            {
                "title": "Mike Johnson - Energy Manager at University of California Irvine",
                "snippet": "Managing energy efficiency programs and sustainability initiatives at UC Irvine campus and medical facilities",
                "link": "https://linkedin.com/in/mikejohnson",
                "target_title": "Energy Manager"
            }
        ]
        
        try:
            result = await self.validate_current_employment(test_prospects, "UCI Medical Center")
            return {
                "success": result.get("success", False),
                "test_company": "UCI Medical Center",
                "validation_summary": result.get("validation_details", {}),
                "validated_count": len(result.get("validated_prospects", []))
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Global instance
company_validation_service = CompanyValidationService()
