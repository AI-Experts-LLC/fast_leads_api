"""
AI-Powered Company Name Normalization Service
Uses GPT-5 to generate intelligent company name variations for LinkedIn filtering
"""

import os
import logging
import json
from typing import List, Dict, Any
from openai import OpenAI

logger = logging.getLogger(__name__)


class AICompanyNormalizationService:
    """AI service that generates company name variations for LinkedIn filtering"""

    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-5-mini-2025-08-07')
        self.reasoning_effort = os.getenv('OPENAI_REASONING_EFFORT', 'minimal')

        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            logger.info(f"AI company normalization service initialized with model: {self.model}")
        else:
            self.client = None
            logger.warning("OPENAI_API_KEY not found - AI company normalization disabled")

    async def normalize_company_name(
        self,
        company_name: str,
        parent_account_name: str = None,
        company_city: str = None,
        company_state: str = None
    ) -> List[str]:
        """
        Generate intelligent company name variations using AI

        Args:
            company_name: Primary company name (e.g., "BENEFIS HOSPITALS INC")
            parent_account_name: Parent organization name (e.g., "Benefis Health System")
            company_city: City location (e.g., "Great Falls")
            company_state: State location (e.g., "Montana")

        Returns:
            List of company name variations optimized for LinkedIn "includes" filter
        """
        if not self.client:
            logger.warning("AI normalization not available - falling back to basic normalization")
            return [company_name]

        try:
            # Build context for AI
            context_parts = [f"Company: {company_name}"]
            if parent_account_name:
                context_parts.append(f"Parent Organization: {parent_account_name}")
            if company_city and company_state:
                context_parts.append(f"Location: {company_city}, {company_state}")
            elif company_state:
                context_parts.append(f"State: {company_state}")

            context = "\n".join(context_parts)

            prompt = f"""Generate company name variations for LinkedIn profile filtering.

{context}

Generate ALL possible name variations that might appear on LinkedIn profiles, including:
1. Official company names (with and without legal suffixes like Inc, LLC, Corp)
2. Parent organization names (if provided)
3. Common abbreviations (e.g., "St." vs "Saint", "Med Ctr" vs "Medical Center")
4. Location-based variations (e.g., "Benefis Great Falls")
5. Shortened versions (e.g., "Benefis" from "Benefis Health System")
6. Department-specific names (e.g., "Benefis Medical Group")

IMPORTANT RULES:
- Remove legal suffixes (Inc, LLC, Corp, Corporation) as they rarely appear on LinkedIn
- Keep healthcare suffixes (Hospital, Medical Center, Health System, Clinic)
- Include both formal and informal variations
- Consider how employees would list their employer on LinkedIn
- Return 5-10 variations ordered by likelihood of appearing on LinkedIn

Return ONLY a JSON object with this format:
{{
  "variations": [
    "Most common variation",
    "Second most common",
    "Third variation",
    ...
  ],
  "reasoning": "Brief explanation of why these variations were chosen"
}}"""

            # Use Responses API for GPT-5
            full_input = f"""You are an expert at normalizing company names for LinkedIn profile searches. Your goal is to generate name variations that will match how employees actually list their company on LinkedIn profiles.

{prompt}"""

            api_params = {
                "model": self.model,
                "input": full_input,
                "text": {"format": {"type": "json_object"}},
                "max_output_tokens": 400,
                "timeout": 15
            }

            # Add reasoning parameter for GPT-5 models
            if "gpt-5" in self.model or self.model.startswith("o"):
                api_params["reasoning"] = {"effort": self.reasoning_effort}

            logger.info(f"Generating company name variations for: {company_name}")
            response = self.client.responses.create(**api_params)

            # Parse response from Responses API
            if not response or not hasattr(response, 'output') or not response.output:
                raise ValueError("Invalid API response")

            # Get the actual output (last item if reasoning is enabled)
            output_item = response.output[-1]
            output_text = output_item.content[0].text

            result = json.loads(output_text)
            variations = result.get("variations", [])
            reasoning = result.get("reasoning", "")

            if not variations:
                logger.warning("AI returned no variations - falling back to original name")
                return [company_name]

            logger.info(f"Generated {len(variations)} company name variations")
            logger.debug(f"AI reasoning: {reasoning}")
            logger.debug(f"Variations: {variations}")

            return variations

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in AI company normalization: {e}")
            return [company_name]
        except Exception as e:
            logger.error(f"Error in AI company normalization: {type(e).__name__}: {str(e)}")
            return [company_name]

    def normalize_company_name_fallback(self, company_name: str) -> List[str]:
        """
        Fallback normalization when AI is not available
        Returns basic variations using simple rules
        """
        import re

        variations = [company_name]

        # Remove legal suffixes
        legal_suffixes = [
            r'\bInc\.?\b',
            r'\bLLC\b',
            r'\bL\.L\.C\.?\b',
            r'\bCorp\.?\b',
            r'\bCorporation\b',
            r'\bCo\.?\b',
            r'\bLtd\.?\b',
            r'\bLimited\b'
        ]

        cleaned = company_name
        for suffix in legal_suffixes:
            cleaned = re.sub(suffix, '', cleaned, flags=re.IGNORECASE)

        cleaned = ' '.join(cleaned.split()).strip(' ,&-')
        if cleaned and cleaned != company_name:
            variations.append(cleaned)

        # St/Saint normalization
        if 'St.' in company_name or 'St ' in company_name:
            saint_version = company_name.replace('St.', 'Saint').replace('St ', 'Saint ')
            variations.append(saint_version)

        # Get first word(s) as shortened version
        words = cleaned.split()
        if len(words) >= 2:
            variations.append(' '.join(words[:2]))

        # Remove duplicates while preserving order
        seen = set()
        unique_variations = []
        for v in variations:
            v_lower = v.lower()
            if v_lower not in seen:
                seen.add(v_lower)
                unique_variations.append(v)

        return unique_variations


# Global instance
ai_company_normalization_service = AICompanyNormalizationService()
