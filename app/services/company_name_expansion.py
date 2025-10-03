"""
Company Name Expansion Service
Uses OpenAI to identify all variations of how a company might be listed on LinkedIn
"""

import os
import logging
from typing import List, Dict, Any
from openai import OpenAI
import json

logger = logging.getLogger(__name__)


class CompanyNameExpansionService:
    """Service to expand company names into all possible LinkedIn variations"""

    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            logger.info(f"Company name expansion service initialized with model: {self.model}")
        else:
            self.client = None
            logger.warning("OPENAI_API_KEY not found - company name expansion unavailable")

    async def expand_company_name(self, company_name: str, company_city: str = None, company_state: str = None) -> Dict[str, Any]:
        """
        Expand a company name into all possible variations used on LinkedIn

        Args:
            company_name: Official company name (e.g., "Lankenau Medical Center")
            company_city: Company city for context (optional)
            company_state: Company state for context (optional)

        Returns:
            Dictionary with list of name variations and metadata
        """
        if not self.client:
            return {
                "success": False,
                "error": "OpenAI client not configured",
                "variations": [company_name]  # Fallback to original name
            }

        try:
            location_context = ""
            if company_city and company_state:
                location_context = f"\nLocation: {company_city}, {company_state}"
            elif company_state:
                location_context = f"\nLocation: {company_state}"

            prompt = f"""
Given a healthcare organization name, identify ALL possible ways employees might list this company on their LinkedIn profiles.

COMPANY: {company_name}{location_context}

Consider:
1. Official name and common abbreviations
2. Parent organization names (if part of a health system)
3. Affiliated institutes, research centers, or foundations
4. Historical names (if renamed)
5. Department-specific listings (e.g., "Finance at XYZ Hospital")
6. Location-based variations (e.g., "XYZ Hospital - City Branch")

IMPORTANT:
- Include the parent health system if this is a hospital within a larger network
- Include research/institute affiliates (e.g., "Lankenau Institute for Medical Research" for Lankenau Medical Center)
- Include common abbreviations and acronyms
- Do NOT include unrelated organizations
- Do NOT include generic terms like "Hospital" or "Healthcare" alone

Return ONLY a JSON array of strings (no explanations):
{{
  "variations": ["Official Name", "Parent Organization", "Affiliate Institute", "Common Abbreviation", ...]
}}
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a healthcare organization expert. Return ONLY valid JSON with company name variations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=800,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            variations = result.get("variations", [company_name])

            # Always ensure the original name is in the list
            if company_name not in variations:
                variations.insert(0, company_name)

            logger.info(f"Expanded '{company_name}' into {len(variations)} variations")

            return {
                "success": True,
                "original_name": company_name,
                "variations": variations,
                "total_variations": len(variations)
            }

        except Exception as e:
            logger.error(f"Error expanding company name: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "original_name": company_name,
                "variations": [company_name]  # Fallback to original
            }

    def generate_basic_variations(self, company_name: str) -> List[str]:
        """
        Generate basic variations without AI (fallback method)
        """
        variations = [company_name]

        # Add common healthcare suffixes
        healthcare_suffixes = [
            "Medical Center", "Hospital", "Health System", "Healthcare",
            "Medical", "Health", "Clinic", "Regional Medical Center"
        ]

        # Extract base name
        base_name = company_name
        for suffix in healthcare_suffixes:
            if suffix in company_name:
                base_name = company_name.replace(suffix, "").strip()
                break

        # Add variations with different suffixes
        for suffix in healthcare_suffixes:
            variations.append(f"{base_name} {suffix}")

        # Add just the base name
        if base_name != company_name:
            variations.append(base_name)

        # Add first word only (for unique identifiers)
        first_word = company_name.split()[0]
        if len(first_word) > 4:  # Only for non-generic words
            variations.append(first_word)

        # Remove duplicates while preserving order
        seen = set()
        unique_variations = []
        for v in variations:
            if v.lower() not in seen:
                seen.add(v.lower())
                unique_variations.append(v)

        return unique_variations


# Global instance
company_name_expansion_service = CompanyNameExpansionService()
