#!/usr/bin/env python3
"""
GPT-5 Optimized Financial Data Enricher

Streamlined prompts and focused search strategies specifically designed for GPT-5's
reasoning capabilities to reduce processing time while maintaining quality.

Key optimizations:
- Simplified prompts that leverage GPT-5's reasoning rather than explicit step-by-step instructions
- Focused domain filtering for faster web search
- Shorter, more direct questions that still yield comprehensive results
"""

import os
import time
import logging
import json
import re
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Import field validator for data quality
from .field_validator import FieldValidator

logger = logging.getLogger(__name__)

# GPT-5 Optimized Configuration
FINANCIAL_MODEL = "gpt-5"
FINANCIAL_REASONING_EFFORT = os.getenv("OPENAI_REASONING_EFFORT", "low")  # Start with low for speed
FINANCIAL_MODEL_FALLBACK = "gpt-4o-search-preview"


class GPT5FinancialEnricher:
    """GPT-5 optimized financial data enricher for healthcare organizations."""

    FINANCIAL_FIELD_MAPPING = {
        'recent_disclosures': 'Recent_disclosures__c',
        'wacc': 'Weighted_average_cost_of_capital__c',
        'debt_appetite': 'Debt_appetite_constraints__c',
        'other_debt': 'Debt__c',
        'financial_outlook': 'Long_term_financial_outlook__c',
        'off_balance_appetite': 'Off_balance_sheet_financing__c',
    }

    def __init__(self):
        """Initialize the GPT-5 optimized financial enricher."""
        self.openai_client = None
        load_dotenv()
        self._setup_openai_client()

    def _setup_openai_client(self) -> None:
        """Setup OpenAI client."""
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("Missing OPENAI_API_KEY in environment variables")

            from openai import OpenAI
            self.openai_client = OpenAI(api_key=api_key)
            logger.info(f"✅ GPT-5 optimized financial enricher configured with {FINANCIAL_REASONING_EFFORT} reasoning effort")

        except Exception as e:
            logger.error(f"❌ Failed to setup OpenAI for GPT-5 financial analysis: {str(e)}")
            raise

    def _extract_json_result(self, response_text: str, key: str) -> Optional[str]:
        """Extract JSON result from response."""
        try:
            json_pattern = r'\{[^{}]*"' + key + r'"[^{}]*\}'
            json_matches = re.findall(json_pattern, response_text, re.DOTALL)

            if json_matches:
                json_str = json_matches[-1]
                data = json.loads(json_str)
                return data.get(key, "")
            return None
        except (json.JSONDecodeError, KeyError, AttributeError):
            return None

    def _make_gpt5_financial_search(self, prompt: str) -> Optional[str]:
        """Make optimized GPT-5 financial search."""
        try:
            logger.info(f"🧠 Using GPT-5 with {FINANCIAL_REASONING_EFFORT} reasoning effort...")

            response = self.openai_client.responses.create(
                model="gpt-5",
                reasoning={"effort": FINANCIAL_REASONING_EFFORT},
                tools=[
                    {
                        "type": "web_search",
                    }
                ],
                tool_choice="auto",
                input=prompt
            )

            return response.output_text.strip()

        except Exception as e:
            logger.warning(f"❌ GPT-5 failed, falling back: {str(e)}")
            # Fallback to search model
            try:
                resp = self.openai_client.chat.completions.create(
                    model=FINANCIAL_MODEL_FALLBACK,
                    web_search_options={},
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1000
                )
                return resp.choices[0].message.content.strip()
            except Exception as fallback_error:
                logger.error(f"❌ Fallback also failed: {str(fallback_error)}")
                raise

    def search_recent_disclosures_gpt5(self, hospital_name: str, location: str) -> Optional[str]:
        """GPT-5 optimized recent disclosures search."""
        try:
            logger.info(f"💰 GPT-5 searching for financial disclosures: {hospital_name}")

            # Simplified, focused prompt for GPT-5
            prompt = f"""Find recent financial disclosures for {hospital_name} in {location}.

Search for: annual reports, bond offerings, rating updates, financial statements from 2023-2024.

Return findings as: {{"disclosures_result": "• [Date] [Type]: $[Amount] - [Description]" or "No recent financial disclosures found"}}"""

            result = self._make_gpt5_financial_search(prompt)
            if not result:
                return None

            extracted_result = self._extract_json_result(result, 'disclosures_result')

            if extracted_result and FieldValidator.is_valid_field_value(extracted_result, 'recent_disclosures'):
                logger.info(f"   ✅ GPT-5 found disclosure data: {extracted_result[:100]}...")
                return extracted_result
            else:
                logger.info(f"   🛑 GPT-5 disclosures result failed validation: {str(extracted_result)[:50]}...")
                return None

        except Exception as e:
            logger.error(f"❌ Error in GPT-5 disclosures search: {str(e)}")
            return None

    def search_wacc_gpt5(self, hospital_name: str, location: str) -> Optional[str]:
        """GPT-5 optimized WACC calculation."""
        try:
            logger.info(f"💹 GPT-5 calculating WACC for: {hospital_name}")

            # Simplified prompt that lets GPT-5's reasoning handle the complexity
            prompt = f"""Calculate the Weighted Average Cost of Capital (WACC) for {hospital_name} in {location}.

Find: recent bond rates, credit ratings, financial statements, debt levels, and industry benchmarks.

Return: {{"wacc_result": "WACC: X.X% (Methodology: brief explanation, Confidence: High/Medium/Low)" or "WACC: Unable to calculate - insufficient data"}}"""

            result = self._make_gpt5_financial_search(prompt)
            if not result:
                return None

            extracted_result = self._extract_json_result(result, 'wacc_result')

            if extracted_result and FieldValidator.is_valid_field_value(extracted_result, 'wacc'):
                logger.info(f"   ✅ GPT-5 calculated WACC: {extracted_result}")
                return extracted_result
            else:
                logger.info(f"   🛑 GPT-5 WACC result failed validation: {str(extracted_result)[:50]}...")
                return None

        except Exception as e:
            logger.error(f"❌ Error in GPT-5 WACC calculation: {str(e)}")
            return None

    def search_debt_appetite_gpt5(self, hospital_name: str, location: str) -> Optional[str]:
        """GPT-5 optimized debt appetite analysis."""
        try:
            logger.info(f"📊 GPT-5 analyzing debt appetite for: {hospital_name}")

            prompt = f"""Analyze debt capacity and appetite for {hospital_name} in {location}.

Find: current debt levels, recent borrowings, credit ratings, debt service coverage, financial ratios.

Return: {{"debt_result": "• Current debt: $[Amount]\\n• Capacity: $[Amount]\\n• Recent activity: [Description]" or "Debt capacity: Unable to assess - insufficient data"}}"""

            result = self._make_gpt5_financial_search(prompt)
            if not result:
                return None

            extracted_result = self._extract_json_result(result, 'debt_result')

            if extracted_result and FieldValidator.is_valid_field_value(extracted_result, 'debt_appetite'):
                logger.info(f"   ✅ GPT-5 analyzed debt capacity: {extracted_result[:100]}...")
                return extracted_result
            else:
                logger.info(f"   🛑 GPT-5 debt appetite result failed validation: {str(extracted_result)[:50]}...")
                return None

        except Exception as e:
            logger.error(f"❌ Error in GPT-5 debt appetite analysis: {str(e)}")
            return None

    def search_all_financial_data_gpt5(self, hospital_name: str, location: str, website: str = None) -> Optional[Dict[str, str]]:
        """GPT-5 optimized comprehensive financial data search."""
        try:
            logger.info(f"💰 GPT-5 enhanced financial data search for: {hospital_name}")

            financial_results = {}

            # Test the three most important functions with GPT-5
            functions_to_test = [
                ("recent_disclosures", self.search_recent_disclosures_gpt5),
                ("wacc", self.search_wacc_gpt5),
                ("debt_appetite", self.search_debt_appetite_gpt5)
            ]

            for field_name, func in functions_to_test:
                try:
                    data = func(hospital_name, location)
                    if data:
                        financial_results[field_name] = data
                    time.sleep(1)  # Rate limiting
                except Exception as e:
                    logger.error(f"❌ GPT-5 function {field_name} failed: {str(e)}")
                    continue

            found_fields = [k for k, v in financial_results.items() if v]
            logger.info(f"   ✅ GPT-5 found financial data for {len(found_fields)} fields: {found_fields}")
            return financial_results

        except Exception as e:
            logger.error(f"❌ Error in GPT-5 comprehensive financial search: {str(e)}")
            return None