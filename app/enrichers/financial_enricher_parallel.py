#!/usr/bin/env python3
"""
Parallel Financial Data Enricher for GPT-5

Implements both parallel processing and combined API calls to significantly
reduce execution time from ~10 minutes to ~2-3 minutes.

Two optimization strategies:
1. Parallel API calls using asyncio/threading
2. Combined prompts in single API call for related analyses
"""

import os
import time
import logging
import json
import re
import asyncio
import concurrent.futures
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Import field validator for data quality
from .field_validator import FieldValidator

logger = logging.getLogger(__name__)

# GPT-5 Configuration
FINANCIAL_MODEL = os.getenv("OPENAI_FINANCIAL_MODEL", "gpt-5")
FINANCIAL_REASONING_EFFORT = os.getenv("OPENAI_REASONING_EFFORT", "low")
FINANCIAL_MODEL_FALLBACK = "gpt-4o-search-preview"


class ParallelFinancialEnricher:
    """Parallel processing financial enricher for GPT-5."""

    FINANCIAL_FIELD_MAPPING = {
        'recent_disclosures': 'Recent_disclosures__c',
        'wacc': 'Weighted_average_cost_of_capital__c',
        'debt_appetite': 'Debt_appetite_constraints__c',
        'other_debt': 'Debt__c',
        'financial_outlook': 'Long_term_financial_outlook__c',
        'off_balance_appetite': 'Off_balance_sheet_financing__c',
    }

    def __init__(self):
        """Initialize the parallel financial enricher."""
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
            logger.info(f"✅ Parallel financial enricher configured with GPT-5 {FINANCIAL_REASONING_EFFORT} reasoning")

        except Exception as e:
            logger.error(f"❌ Failed to setup OpenAI for parallel financial analysis: {str(e)}")
            raise

    def _extract_json_results(self, response_text: str, keys: List[str]) -> Dict[str, Optional[str]]:
        """Extract multiple JSON results from a single response."""
        results = {}
        for key in keys:
            try:
                json_pattern = r'\{[^{}]*"' + key + r'"[^{}]*\}'
                json_matches = re.findall(json_pattern, response_text, re.DOTALL)

                if json_matches:
                    json_str = json_matches[-1]
                    data = json.loads(json_str)
                    results[key] = data.get(key, "")
                else:
                    results[key] = None
            except (json.JSONDecodeError, KeyError, AttributeError):
                results[key] = None
        return results

    def search_combined_financial_analysis(self, hospital_name: str, location: str) -> Optional[Dict[str, str]]:
        """Combined GPT-5 search for all financial metrics in one API call."""
        try:
            logger.info(f"💰 Combined GPT-5 financial analysis for: {hospital_name}")
            logger.info(f"🧠 Using GPT-5 with {FINANCIAL_REASONING_EFFORT} reasoning effort...")

            start_time = time.time()

            # Combined prompt for all financial analyses
            combined_prompt = f"""Perform comprehensive financial analysis for {hospital_name} in {location}.

Research and provide results for ALL of the following financial metrics:

1. RECENT DISCLOSURES: Find recent financial disclosures, annual reports, bond offerings, rating updates from 2023-2024.

2. WACC CALCULATION: Calculate Weighted Average Cost of Capital using bond rates, credit ratings, financial statements, industry benchmarks.

3. DEBT APPETITE: Analyze current debt levels, borrowing capacity, recent debt activity, credit line utilization.

4. OTHER DEBT INSTRUMENTS: Identify equipment financing, capital leases, pension obligations, development authority bonds.

5. FINANCIAL OUTLOOK: Review capital project history, funding sources, financial performance trends over 5-7 years.

6. OFF-BALANCE SHEET APPETITE: Assess appetite for operating leases, sale-leaseback, PPAs, ESCO contracts, joint ventures.

Return results in this exact JSON format:

{{
    "recent_disclosures": "• [Date] [Type]: $[Amount] - [Description]" or "No recent financial disclosures found",
    "wacc": "WACC: X.X% (Methodology: brief explanation, Confidence: High/Medium/Low)" or "WACC: Unable to calculate - insufficient data",
    "debt_appetite": "• Current debt: $[Amount]\\n• Capacity: $[Amount]\\n• Recent activity: [Description]" or "Debt capacity: Unable to assess - insufficient data",
    "other_debt": "• Equipment financing: $[Amount] - [Description]\\n• Capital leases: $[Amount] - [Description]" or "Other debt: Limited disclosure available",
    "financial_outlook": "Capital Projects: [recent major projects with amounts and dates]" or "Capital project history: Insufficient data",
    "off_balance_appetite": "Off-balance appetite: [High/Moderate/Low] - Recent arrangements: [details]" or "Off-balance appetite: Insufficient information"
}}"""

            response = self.openai_client.responses.create(
                model="gpt-5",
                reasoning={"effort": FINANCIAL_REASONING_EFFORT},
                tools=[
                    {
                        "type": "web_search",
                        "filters": {}
                    }
                ],
                tool_choice="auto",
                input=combined_prompt,
                include=["web_search_call.action.sources"]
            )

            end_time = time.time()
            execution_time = end_time - start_time

            logger.info(f"✅ Combined GPT-5 analysis completed in {execution_time:.1f}s")

            # Extract all results from the single response
            field_keys = ['recent_disclosures', 'wacc', 'debt_appetite', 'other_debt', 'financial_outlook', 'off_balance_appetite']
            results = self._extract_json_results(response.output_text, field_keys)

            # Validate each result
            validated_results = {}
            for field_key, value in results.items():
                if value and FieldValidator.is_valid_field_value(value, field_key):
                    validated_results[field_key] = value
                    logger.info(f"   ✅ {field_key}: {value[:100]}...")
                else:
                    logger.info(f"   ❌ {field_key}: Failed validation or no data")

            found_fields = list(validated_results.keys())
            logger.info(f"📊 Combined analysis found data for {len(found_fields)} fields: {found_fields}")

            return validated_results

        except Exception as e:
            logger.error(f"❌ Error in combined financial analysis: {str(e)}")
            return None

    def search_parallel_financial_analysis(self, hospital_name: str, location: str) -> Optional[Dict[str, str]]:
        """Parallel GPT-5 searches using threading for faster execution."""
        try:
            logger.info(f"⚡ Parallel GPT-5 financial analysis for: {hospital_name}")

            start_time = time.time()

            # Define individual search functions
            def search_disclosures():
                return self._single_search("recent_disclosures",
                    f"Find recent financial disclosures for {hospital_name} in {location}. "
                    f"Search for annual reports, bond offerings, rating updates from 2023-2024. "
                    f'Return: {{"disclosures_result": "• [Date] [Type]: $[Amount] - [Description]" or "No recent financial disclosures found"}}')

            def search_wacc():
                return self._single_search("wacc",
                    f"Calculate WACC for {hospital_name} in {location}. "
                    f"Find bond rates, credit ratings, financial statements, industry benchmarks. "
                    f'Return: {{"wacc_result": "WACC: X.X% (Confidence: High/Medium/Low)" or "WACC: Unable to calculate - insufficient data"}}')

            def search_debt_appetite():
                return self._single_search("debt_appetite",
                    f"Analyze debt capacity for {hospital_name} in {location}. "
                    f"Find current debt, borrowing capacity, recent activity. "
                    f'Return: {{"debt_result": "• Current debt: $[Amount]\\n• Capacity: $[Amount]" or "Debt capacity: Unable to assess - insufficient data"}}')

            def search_other_debt():
                return self._single_search("other_debt",
                    f"Identify other debt for {hospital_name} in {location}. "
                    f"Find equipment financing, capital leases, pension obligations. "
                    f'Return: {{"other_debt_result": "• Equipment financing: $[Amount]" or "Other debt: Limited disclosure available"}}')

            def search_outlook():
                return self._single_search("financial_outlook",
                    f"Review financial outlook for {hospital_name} in {location}. "
                    f"Find capital projects, funding sources, performance trends. "
                    f'Return: {{"outlook_result": "Capital Projects: [details]" or "Capital project history: Insufficient data"}}')

            def search_off_balance():
                return self._single_search("off_balance_appetite",
                    f"Assess off-balance appetite for {hospital_name} in {location}. "
                    f"Find operating leases, sale-leaseback, PPAs, joint ventures. "
                    f'Return: {{"off_balance_result": "Off-balance appetite: [High/Moderate/Low]" or "Off-balance appetite: Insufficient information"}}')

            # Execute searches in parallel using ThreadPoolExecutor
            functions = [search_disclosures, search_wacc, search_debt_appetite, search_other_debt, search_outlook, search_off_balance]

            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
                future_to_field = {executor.submit(func): func.__name__ for func in functions}
                results = {}

                for future in concurrent.futures.as_completed(future_to_field):
                    field_name = future_to_field[future]
                    try:
                        field_key, result = future.result()
                        if result:
                            results[field_key] = result
                            logger.info(f"   ✅ {field_key}: {result[:100]}...")
                    except Exception as e:
                        logger.error(f"   ❌ {field_name} failed: {str(e)}")

            end_time = time.time()
            execution_time = end_time - start_time

            found_fields = list(results.keys())
            logger.info(f"⚡ Parallel analysis completed in {execution_time:.1f}s")
            logger.info(f"📊 Found data for {len(found_fields)} fields: {found_fields}")

            return results

        except Exception as e:
            logger.error(f"❌ Error in parallel financial analysis: {str(e)}")
            return None

    def _single_search(self, field_type: str, prompt: str) -> tuple:
        """Perform a single GPT-5 search with error handling."""
        try:
            response = self.openai_client.responses.create(
                model="gpt-5",
                reasoning={"effort": FINANCIAL_REASONING_EFFORT},
                tools=[
                    {
                        "type": "web_search",
                        "filters": {}
                    }
                ],
                tool_choice="auto",
                input=prompt
            )

            # Extract result based on field type
            result_key = f"{field_type}_result" if field_type != "recent_disclosures" else "disclosures_result"
            if field_type == "wacc":
                result_key = "wacc_result"
            elif field_type == "debt_appetite":
                result_key = "debt_result"
            elif field_type == "financial_outlook":
                result_key = "outlook_result"
            elif field_type == "off_balance_appetite":
                result_key = "off_balance_result"

            extracted = self._extract_json_results(response.output_text, [result_key])
            result = extracted.get(result_key)

            if result and FieldValidator.is_valid_field_value(result, field_type):
                return field_type, result
            else:
                return field_type, None

        except Exception as e:
            logger.error(f"❌ Single search {field_type} failed: {str(e)}")
            return field_type, None

    def search_all_financial_data_optimized(self, hospital_name: str, location: str, method: str = "combined") -> Optional[Dict[str, str]]:
        """
        Optimized financial data search with choice of method.

        Args:
            method: "combined" for single API call, "parallel" for concurrent searches
        """
        logger.info(f"🚀 Starting optimized financial analysis using {method} method")

        if method == "combined":
            return self.search_combined_financial_analysis(hospital_name, location)
        elif method == "parallel":
            return self.search_parallel_financial_analysis(hospital_name, location)
        else:
            logger.error(f"❌ Unknown method: {method}")
            return None