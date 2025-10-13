#!/usr/bin/env python3
"""
Financial Data Enricher for Salesforce Accounts

Specialized module for searching and analyzing financial data including:
- WACC (Weighted Average Cost of Capital)
- Debt appetite and constraints
- Recent financial disclosures
- Off-balance sheet financing
- Credit quality analysis

Uses advanced search strategies and improved models for better data retrieval.

Usage:
    from financial_enricher import FinancialEnricher
    enricher = FinancialEnricher()
    data = enricher.search_all_financial_data("Hospital Name", "Location", "Website")
"""

import os
import time
import logging
import json
import re
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Import field validator for data quality
try:
    from .field_validator import FieldValidator
except ImportError:
    try:
        from field_validator import FieldValidator
    except ImportError:
        from enrichers.field_validator import FieldValidator

logger = logging.getLogger(__name__)

# Enhanced OpenAI Configuration for financial analysis
FINANCIAL_MODEL = os.getenv("OPENAI_FINANCIAL_MODEL", "gpt-5")  # GPT-5 with reasoning
FINANCIAL_REASONING_EFFORT = os.getenv("OPENAI_REASONING_EFFORT", "low")  # low, medium, high
FINANCIAL_MODEL_FALLBACK = os.getenv("OPENAI_MODEL", "gpt-4o-search-preview")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
WEB_TOOL_TYPE = os.getenv("OPENAI_WEB_SEARCH_TOOL_TYPE", "web_search")


class FinancialEnricher:
    """Specialized financial data enricher for healthcare organizations."""

    # Financial field mapping
    FINANCIAL_FIELD_MAPPING = {
        'recent_disclosures': 'Recent_disclosures__c',
        'wacc': 'Weighted_average_cost_of_capital__c',
        'debt_appetite': 'Debt_appetite_constraints__c',
        'other_debt': 'Debt__c',
        'financial_outlook': 'Long_term_financial_outlook__c',
        'off_balance_appetite': 'Off_balance_sheet_financing__c',
        'revenue': 'Revenue__c',
        'credit_quality': 'Company_Credit_Quality__c',
        'credit_quality_detailed': 'Company_Credit_Quality_Detailed__c',
    }

    def __init__(self):
        """Initialize the financial enricher with enhanced OpenAI client."""
        self.openai_client = None
        load_dotenv()
        self._setup_openai_client()

    def _setup_openai_client(self) -> None:
        """Setup OpenAI client with enhanced configuration for financial analysis."""
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("Missing OPENAI_API_KEY in environment variables")

            from openai import OpenAI
            self.openai_client = OpenAI(api_key=api_key)
            logger.info(f"✅ Financial enricher configured with model: {FINANCIAL_MODEL}")

        except Exception as e:
            logger.error(f"❌ Failed to setup OpenAI for financial analysis: {str(e)}")
            raise

    def _extract_json_result(self, response_text: str, key: str) -> Optional[str]:
        """Extract JSON result from the end of a response."""
        try:
            # Look for JSON at the end of the response
            json_pattern = r'\{[^{}]*"' + key + r'"[^{}]*\}'
            json_matches = re.findall(json_pattern, response_text, re.DOTALL)

            if json_matches:
                # Try to parse the last JSON match
                json_str = json_matches[-1]
                data = json.loads(json_str)
                return data.get(key, "")

            return None
        except (json.JSONDecodeError, KeyError, AttributeError):
            return None

    def _make_financial_search(self, prompt: str, max_tokens: int = 1500, model: str = None) -> Optional[str]:
        """Make a financial search with enhanced error handling and model selection."""
        try:
            selected_model = model or FINANCIAL_MODEL

            # Use GPT-5 with Responses API and reasoning effort for better analysis
            if selected_model == "gpt-5":
                logger.info(f"🧠 Using GPT-5 with {FINANCIAL_REASONING_EFFORT} reasoning effort for enhanced analysis...")

                response = self.openai_client.responses.create(
                    model="gpt-5",
                    reasoning={"effort": FINANCIAL_REASONING_EFFORT},
                    tools=[
                        {
                            "type": "web_search",
                        }
                    ],
                    tool_choice="auto",
                    input=prompt,
                    include=["web_search_call.action.sources"]  # Get source URLs
                )

                return response.output_text.strip()

            # Fallback to search models for compatibility
            elif "search" in selected_model:
                resp = self.openai_client.chat.completions.create(
                    model=selected_model,
                    web_search_options={},
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens
                )
                return resp.choices[0].message.content.strip()

            # Regular models without search
            else:
                resp = self.openai_client.chat.completions.create(
                    model=selected_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0.1
                )
                return resp.choices[0].message.content.strip()

        except Exception as e:
            logger.warning(f"❌ Error with {selected_model}, trying fallback: {str(e)}")
            if selected_model != FINANCIAL_MODEL_FALLBACK:
                try:
                    # Use fallback model - try search model first
                    logger.info(f"🔄 Falling back to {FINANCIAL_MODEL_FALLBACK}...")
                    return self._make_financial_search(prompt, max_tokens, FINANCIAL_MODEL_FALLBACK)
                except Exception as fallback_error:
                    logger.error(f"❌ Fallback model also failed: {str(fallback_error)}")
                    raise
            else:
                raise

    def search_recent_disclosures(self, hospital_name: str, location: str) -> Optional[str]:
        """Search for recent financial disclosures with enhanced search strategy."""
        try:
            logger.info(f"💰 Searching for financial disclosures: {hospital_name}")

            prompt = f"""You are a financial analyst researching {hospital_name} in {location}.

SEARCH STRATEGY:
1. Start with the hospital's official website and investor relations pages
2. Search for "annual report", "financial statements", "bond offerings", "Medicare cost report"
3. Check EMMA (Municipal Securities Rulemaking Board) database for municipal bond disclosures
4. Look for Moody's, Fitch, or S&P rating reports and updates
5. Search for Form 990 filings if non-profit
6. Check local business journals and healthcare trade publications

SEARCH TERMS TO USE:
- "{hospital_name}" + "annual report" + "2023" OR "2024"
- "{hospital_name}" + "financial statements" + "audit"
- "{hospital_name}" + "bond" + "EMMA" + "disclosure"
- "{hospital_name}" + "Medicare cost report"
- "{hospital_name}" + "credit rating" + "Moody's" OR "Fitch" OR "S&P"
- "{hospital_name}" + "Form 990" (if applicable)

ANALYSIS REQUIREMENTS:
- Focus on disclosures from the last 24 months
- Include dollar amounts, dates, and disclosure types
- Prioritize regulatory filings and bond-related disclosures
- Note any credit rating changes or outlook updates

If you find multiple sources, synthesize them into a comprehensive summary.

Provide detailed analysis with sources, then end with this exact JSON format:

{{"disclosures_result": "• [Date] [Type]: $[Amount] - [Description] (Source: [URL])\\n• [Date] [Type]: $[Amount] - [Description] (Source: [URL])" or "No recent financial disclosures identified after comprehensive search"}}"""

            result = self._make_financial_search(prompt, max_tokens=1200)
            if not result:
                return None

            extracted_result = self._extract_json_result(result, 'disclosures_result')

            if extracted_result and FieldValidator.is_valid_field_value(extracted_result, 'recent_disclosures'):
                logger.info(f"   ✅ Found disclosure data: {extracted_result[:100]}...")
                return extracted_result
            else:
                logger.info(f"   🛑 Disclosures result failed validation: {str(extracted_result)[:50]}...")
                return None

        except Exception as e:
            logger.error(f"❌ Error searching recent disclosures: {str(e)}")
            return None

    def search_wacc(self, hospital_name: str, location: str) -> Optional[str]:
        """Search and calculate WACC with enhanced methodology."""
        try:
            logger.info(f"💹 Calculating WACC for: {hospital_name}")

            prompt = f"""You are a financial analyst calculating the Weighted Average Cost of Capital (WACC) for {hospital_name} in {location}.

COMPREHENSIVE SEARCH STRATEGY:
1. Hospital's audited financial statements (look for balance sheet, income statement)
2. Bond prospectuses and official statements on EMMA database
3. Credit rating reports from Moody's, Fitch, S&P (search "[hospital name] credit rating")
4. Medicare cost reports for revenue and expense data
5. Comparable hospital financial data for benchmarking
6. Healthcare industry WACC studies and benchmarks

SEARCH TERMS TO USE:
- "{hospital_name}" + "financial statements" + "balance sheet" + "debt"
- "{hospital_name}" + "bond" + "interest rate" + "yield"
- "{hospital_name}" + "credit rating" + "Moody's" OR "Fitch" OR "S&P"
- "{hospital_name}" + "annual report" + "cost of capital"
- "hospital WACC" + "healthcare cost of capital" + "benchmark"
- "{hospital_name}" + "EMMA" + "official statement"

WACC CALCULATION METHODOLOGY:
Step 1: Cost of Debt Analysis
- Find recent bond issuances and their yields
- Look for credit ratings (Aa2, A1, BBB+, etc.)
- Research current market rates for similar-rated healthcare debt
- Calculate weighted average interest rate on existing debt

Step 2: Cost of Equity Estimation
- Use CAPM: Risk-free rate + (Beta × Market risk premium)
- Healthcare beta typically 0.6-1.2
- For non-profits, estimate using comparable public hospitals
- Consider organization-specific risk factors

Step 3: Capital Structure Analysis
- Debt-to-total-capital ratio from latest financials
- Market values vs book values consideration
- Include all interest-bearing debt

Step 4: Tax Considerations
- Non-profit hospitals: No tax shield benefit (tax rate = 0)
- For-profit hospitals: Use appropriate corporate tax rate

QUALITY INDICATORS:
- "High confidence" = Recent audited financials + bond data available
- "Medium confidence" = Some financial data + industry benchmarks
- "Low confidence" = Limited data, mostly industry estimates

After thorough research and analysis, provide your detailed methodology and findings, then end with this exact JSON format:

{{"wacc_result": "WACC: X.X% (Methodology: [brief description], Confidence: High/Medium/Low, Sources: [key sources used])" or "WACC: Unable to calculate - insufficient financial data after comprehensive search"}}"""

            result = self._make_financial_search(prompt, max_tokens=2000)
            if not result:
                return None

            extracted_result = self._extract_json_result(result, 'wacc_result')

            if extracted_result and FieldValidator.is_valid_field_value(extracted_result, 'wacc'):
                logger.info(f"   ✅ Calculated WACC: {extracted_result}")
                return extracted_result
            else:
                logger.info(f"   🛑 WACC result failed validation: {str(extracted_result)[:50]}...")
                return None

        except Exception as e:
            logger.error(f"❌ Error calculating WACC: {str(e)}")
            return None

    def search_debt_appetite(self, hospital_name: str, location: str) -> Optional[str]:
        """Search for debt appetite and capacity with enhanced analysis."""
        try:
            logger.info(f"📊 Analyzing debt appetite for: {hospital_name}")

            prompt = f"""You are a credit analyst assessing debt capacity and appetite for {hospital_name} in {location}.

COMPREHENSIVE DEBT ANALYSIS STRATEGY:
1. Current debt position from latest financial statements
2. Historical debt issuance patterns and timing
3. Credit rating reports and commentary on debt capacity
4. Debt covenant analysis from bond documents
5. Management discussion of capital plans and financing strategy
6. Peer comparison for similar-sized hospitals

SEARCH TERMS TO USE:
- "{hospital_name}" + "debt" + "borrowing capacity" + "credit line"
- "{hospital_name}" + "bond issuance" + "financing" + "capital"
- "{hospital_name}" + "debt service coverage" + "financial ratios"
- "{hospital_name}" + "credit rating" + "debt capacity" + "leverage"
- "{hospital_name}" + "EMMA" + "official statement" + "covenants"
- "{hospital_name}" + "annual report" + "capital expenditure plan"

DEBT CAPACITY ANALYSIS FRAMEWORK:
1. Current Debt Position
   - Total debt outstanding
   - Types of debt (bonds, bank loans, equipment financing)
   - Debt maturity profile and refinancing needs

2. Financial Strength Metrics
   - Debt service coverage ratio (target typically >1.2x for hospitals)
   - Days cash on hand (target >150 days for investment grade)
   - Debt-to-capitalization ratio (varies by credit quality)
   - Operating margin trends

3. Debt Capacity Assessment
   - Available credit lines and their utilization
   - Maximum debt levels per rating agency guidance
   - Covenant restrictions and headroom
   - Management-stated debt targets or policies

4. Recent Debt Activity
   - New issuances in last 3 years
   - Refinancing activity and cost savings
   - Any debt paydowns or deferrals

5. Credit Rating Context
   - Current rating and outlook
   - Rating agency commentary on debt capacity
   - Peer comparison for leverage tolerance

After comprehensive analysis, provide detailed findings then end with this exact JSON format:

{{"debt_result": "• Current total debt: $[Amount] ([Date])\\n• Debt service coverage: [Ratio]x\\n• Days cash on hand: [Number] days\\n• Estimated additional debt capacity: $[Amount]\\n• Key constraints: [Covenant/Rating limits]\\n• Recent activity: $[Amount] issued in [Year] for [Purpose]\\n• Credit rating impact: [Analysis]" or "Debt capacity: Unable to assess - insufficient financial disclosure"}}"""

            result = self._make_financial_search(prompt, max_tokens=2000)
            if not result:
                return None

            extracted_result = self._extract_json_result(result, 'debt_result')

            if extracted_result and FieldValidator.is_valid_field_value(extracted_result, 'debt_appetite'):
                logger.info(f"   ✅ Analyzed debt capacity: {extracted_result[:100]}...")
                return extracted_result
            else:
                logger.info(f"   🛑 Debt appetite result failed validation: {str(extracted_result)[:50]}...")
                return None

        except Exception as e:
            logger.error(f"❌ Error analyzing debt appetite: {str(e)}")
            return None

    def search_other_debt(self, hospital_name: str, location: str) -> Optional[str]:
        """Search for other debt instruments and obligations."""
        try:
            logger.info(f"🔍 Searching other debt instruments: {hospital_name}")

            prompt = f"""You are a financial analyst cataloging all debt instruments and obligations for {hospital_name} in {location}.

COMPREHENSIVE DEBT INSTRUMENT SEARCH:
1. Equipment financing and capital leases
2. Operating leases with significant obligations
3. Pension and post-retirement benefit obligations
4. Self-insurance reserves and contingent liabilities
5. Development authority bonds and government loans
6. Derivatives and interest rate swaps
7. Guarantees and off-balance sheet commitments

SEARCH TERMS TO USE:
- "{hospital_name}" + "equipment lease" + "capital lease" + "financing"
- "{hospital_name}" + "pension obligation" + "OPEB" + "retirement benefits"
- "{hospital_name}" + "operating lease" + "facility lease" + "real estate"
- "{hospital_name}" + "development authority" + "IDA bonds" + "government loan"
- "{hospital_name}" + "derivatives" + "interest rate swap" + "hedging"
- "{hospital_name}" + "contingent liability" + "litigation" + "guarantees"

ANALYSIS FRAMEWORK:
1. Equipment and Capital Leases
   - Medical equipment financing arrangements
   - IT system leases and financing
   - Capital lease obligations on balance sheet

2. Pension and Benefit Obligations
   - Defined benefit pension plans (if any)
   - OPEB (Other Post-Employment Benefits) liabilities
   - Unfunded obligations and actuarial assumptions

3. Operating Lease Commitments
   - Facility and real estate leases
   - Equipment operating leases
   - Long-term service agreements

4. Government and Authority Debt
   - Industrial Development Authority bonds
   - State or local government financing
   - Grant repayment obligations

5. Contingent Liabilities
   - Self-insurance reserves
   - Legal settlements and litigation
   - Regulatory compliance obligations

After thorough research, provide analysis then end with this exact JSON format:

{{"other_debt_result": "• Equipment financing: $[Amount] - [Description] (Source: [URL])\\n• Pension obligations: $[Amount] - [Description] (Source: [URL])\\n• Operating leases: $[Amount] annual - [Description]\\n• Development authority: $[Amount] - [Description]\\n• Contingent liabilities: $[Amount] - [Description]" or "Other debt: Limited disclosure available - [what specific information is missing]"}}"""

            result = self._make_financial_search(prompt, max_tokens=1500)
            if not result:
                return None

            extracted_result = self._extract_json_result(result, 'other_debt_result')

            if extracted_result and FieldValidator.is_valid_field_value(extracted_result, 'other_debt'):
                logger.info(f"   ✅ Found other debt data: {extracted_result[:100]}...")
                return extracted_result
            else:
                logger.info(f"   🛑 Other debt result failed validation: {str(extracted_result)[:50]}...")
                return None

        except Exception as e:
            logger.error(f"❌ Error searching other debt: {str(e)}")
            return None

    def search_financial_outlook(self, hospital_name: str, location: str) -> Optional[str]:
        """Search for financial outlook and capital project history."""
        try:
            logger.info(f"📈 Analyzing financial outlook: {hospital_name}")

            prompt = f"""You are a healthcare industry analyst researching the capital investment history and financial outlook for {hospital_name} in {location}.

COMPREHENSIVE CAPITAL PROJECT RESEARCH:
1. Major facility expansions and construction projects (5-7 year history)
2. Equipment and technology investments
3. Energy efficiency and infrastructure upgrades
4. Strategic acquisitions and partnerships
5. Planned future capital expenditures
6. Financial performance trends affecting capital capacity

SEARCH TERMS TO USE:
- "{hospital_name}" + "expansion" + "construction" + "new facility"
- "{hospital_name}" + "capital project" + "investment" + "$" + "million"
- "{hospital_name}" + "renovation" + "upgrade" + "infrastructure"
- "{hospital_name}" + "energy" + "efficiency" + "sustainability"
- "{hospital_name}" + "acquisition" + "merger" + "partnership"
- "{hospital_name}" + "future plans" + "strategic plan" + "master plan"
- "{hospital_name}" + "EMMA" + "bond proceeds" + "construction fund"

ANALYSIS FRAMEWORK:
1. Historical Capital Projects (2018-2024)
   - Major construction and expansion projects
   - Technology and equipment investments
   - Infrastructure and energy projects
   - Total capital expenditures by year

2. Funding Sources Analysis
   - Bond financing for major projects
   - Cash funding vs. debt financing mix
   - Grant funding and philanthropic contributions
   - Government and state funding

3. Financial Performance Impact
   - Revenue growth from new facilities
   - Operating margin trends during expansion
   - Debt service coverage during heavy capital periods
   - Return on invested capital assessment

4. Future Capital Plans
   - Announced or planned major projects
   - Capital expenditure guidance from management
   - Strategic plan priorities and timeline
   - Capacity needs and market opportunity

After comprehensive research and analysis, provide findings then end with this exact JSON format:

{{"outlook_result": "Capital History (2018-2024): [{{year: 2024, project: '[name]', capex: $[Amount], status: completed/ongoing, funding: [bonds/cash/grants]}}] - Total 7-year capex: ~$[Amount] - Primary focus: [facilities/technology/energy] - Future pipeline: [upcoming projects] - Financial capacity: [Strong/Moderate/Constrained] based on [key metrics]" or "Capital project history: Limited information available - [specify what data is missing]"}}"""

            result = self._make_financial_search(prompt, max_tokens=2000)
            if not result:
                return None

            extracted_result = self._extract_json_result(result, 'outlook_result')

            if extracted_result and FieldValidator.is_valid_field_value(extracted_result, 'financial_outlook'):
                logger.info(f"   ✅ Analyzed financial outlook: {extracted_result[:100]}...")
                return extracted_result
            else:
                logger.info(f"   🛑 Financial outlook result failed validation: {str(extracted_result)[:50]}...")
                return None

        except Exception as e:
            logger.error(f"❌ Error analyzing financial outlook: {str(e)}")
            return None

    def search_off_balance_appetite(self, hospital_name: str, location: str) -> Optional[str]:
        """Search for off-balance sheet financing appetite and experience."""
        try:
            logger.info(f"📋 Analyzing off-balance appetite: {hospital_name}")

            prompt = f"""You are a structured finance analyst assessing off-balance sheet financing appetite and experience for {hospital_name} in {location}.

COMPREHENSIVE OFF-BALANCE SHEET ANALYSIS:
1. Operating lease arrangements (facilities, equipment)
2. Sale-leaseback transactions and history
3. Power Purchase Agreements (PPAs) and energy contracts
4. ESCO (Energy Service Company) financing arrangements
5. Joint ventures and partnership structures
6. Service agreements with significant commitments
7. Technology-as-a-Service (TaaS) arrangements

SEARCH TERMS TO USE:
- "{hospital_name}" + "operating lease" + "sale leaseback" + "real estate"
- "{hospital_name}" + "PPA" + "power purchase agreement" + "solar" + "energy"
- "{hospital_name}" + "ESCO" + "energy service" + "performance contract"
- "{hospital_name}" + "joint venture" + "partnership" + "management agreement"
- "{hospital_name}" + "outsourcing" + "service agreement" + "long-term contract"
- "{hospital_name}" + "TaaS" + "technology service" + "equipment service"

ANALYSIS FRAMEWORK:
1. Operating Lease Portfolio
   - Facility leases and terms
   - Equipment operating leases
   - Annual lease obligations and terms

2. Energy and Infrastructure Arrangements
   - Power Purchase Agreements (PPAs)
   - ESCO performance contracts
   - Utility service agreements
   - Co-generation or renewable energy projects

3. Service and Technology Arrangements
   - IT outsourcing and cloud services
   - Medical equipment service agreements
   - Laboratory and pharmacy partnerships
   - Revenue cycle management outsourcing

4. Real Estate Strategies
   - Sale-leaseback transactions (historical)
   - Ground leases and development arrangements
   - Medical office building partnerships

5. Risk Profile and Appetite Assessment
   - Comfort with long-term commitments
   - Preference for operational vs. capital risk
   - Experience with complex financing structures
   - Management philosophy on balance sheet optimization

After thorough research and analysis, provide findings then end with this exact JSON format:

{{"off_balance_result": "Off-balance appetite: [High/Moderate/Low] - Recent arrangements: [type]: $[Amount]/year ([start year]-[end year]) for [purpose] - Preferred structures: [operating leases/PPAs/ESCOs/partnerships] - Energy project experience: [Strong/Moderate/Limited] with [specific examples] - Risk tolerance: [Conservative/Moderate/Aggressive] based on [evidence] (Sources: [URLs])" or "Off-balance appetite: Insufficient information - [specify what data sources were searched but yielded limited results]"}}"""

            result = self._make_financial_search(prompt, max_tokens=1800)
            if not result:
                return None

            extracted_result = self._extract_json_result(result, 'off_balance_result')

            if extracted_result and FieldValidator.is_valid_field_value(extracted_result, 'off_balance_appetite'):
                logger.info(f"   ✅ Analyzed off-balance appetite: {extracted_result[:100]}...")
                return extracted_result
            else:
                logger.info(f"   🛑 Off-balance appetite result failed validation: {str(extracted_result)[:50]}...")
                return None

        except Exception as e:
            logger.error(f"❌ Error analyzing off-balance appetite: {str(e)}")
            return None

    def search_revenue(self, hospital_name: str, location: str) -> Optional[str]:
        """Search for annual revenue with simple format like $17.8B or $20.5M."""
        try:
            logger.info(f"💰 Searching for revenue: {hospital_name}")

            prompt = f"""You are a financial analyst researching the annual revenue for {hospital_name} in {location}.

COMPREHENSIVE REVENUE SEARCH STRATEGY:
1. Hospital's audited financial statements and annual reports
2. Medicare cost reports (Form 2552-10) for total patient revenue
3. Bond prospectuses and official statements with revenue data
4. Rating agency reports that include revenue figures
5. Form 990 filings for non-profit hospitals
6. Healthcare industry databases and trade publications
7. Local business journals and healthcare news

SEARCH TERMS TO USE:
- "{hospital_name}" + "annual revenue" + "2023" OR "2024"
- "{hospital_name}" + "financial statements" + "total revenue"
- "{hospital_name}" + "Medicare cost report" + "patient revenue"
- "{hospital_name}" + "Form 990" + "total revenue"
- "{hospital_name}" + "bond" + "EMMA" + "revenue"
- "{hospital_name}" + "annual report" + "net revenue"

REVENUE ANALYSIS REQUIREMENTS:
- Focus on most recent annual revenue (2023 or 2024)
- Look for total operating revenue or net patient revenue
- Convert to simple format: $17.8B, $20.5M, $1.2B, etc.
- Prioritize audited financial statements over estimates
- Note the source year and document type

FORMAT REQUIREMENTS:
- Use B for billions (e.g., $2.1B)
- Use M for millions (e.g., $450M)
- Round to 1 decimal place for clarity
- Do not include words, just the dollar amount

After thorough research, provide analysis then end with this exact JSON format:

{{"revenue_result": "$X.XB" or "$X.XM" or "Revenue: Unable to determine from available sources"}}"""

            result = self._make_financial_search(prompt, max_tokens=1200)
            if not result:
                return None

            extracted_result = self._extract_json_result(result, 'revenue_result')

            if extracted_result and FieldValidator.is_valid_field_value(extracted_result, 'revenue'):
                logger.info(f"   ✅ Found revenue data: {extracted_result}")
                return extracted_result
            else:
                logger.info(f"   🛑 Revenue result failed validation: {str(extracted_result)[:50]}...")
                return None

        except Exception as e:
            logger.error(f"❌ Error searching revenue: {str(e)}")
            return None

    def search_credit_quality(self, hospital_name: str, location: str) -> Optional[Dict[str, str]]:
        """Search for credit quality information including rating and detailed analysis."""
        try:
            logger.info(f"🏦 Searching for credit quality: {hospital_name}")

            prompt = f"""You are a credit analyst researching credit quality information for {hospital_name} in {location}.

COMPREHENSIVE CREDIT QUALITY SEARCH:
1. Credit rating agencies: Moody's, S&P Global Ratings, Fitch Ratings
2. EMMA database for municipal bond ratings and reports
3. Hospital's audited financial statements with auditor opinions
4. Recent rating actions, outlooks, and credit reports
5. Peer comparison and industry credit analysis
6. Medicare cost reports for financial stability indicators

SEARCH TERMS TO USE:
- "{hospital_name}" + "credit rating" + "Moody's" OR "S&P" OR "Fitch"
- "{hospital_name}" + "bond rating" + "EMMA" + "municipal"
- "{hospital_name}" + "credit quality" + "financial strength"
- "{hospital_name}" + "rating outlook" + "stable" OR "positive" OR "negative"
- "{hospital_name}" + "investment grade" + "credit analysis"
- "{hospital_name}" + "financial stability" + "credit risk"

CREDIT QUALITY ANALYSIS:
1. Simple Credit Quality (for Company_Credit_Quality__c):
   - Format: "Rating / Outlook" (e.g., "Aa2 / Stable", "BBB+ / Positive")
   - Use most recent rating from major agencies
   - If no rating available: "Not Rated" or "Private/No Rating"

2. Detailed Credit Quality (for Company_Credit_Quality_Detailed__c):
   - Include rating rationale and key credit factors
   - Mention financial metrics supporting the rating
   - Note any recent rating changes or outlook revisions
   - Include source and date of rating
   - Provide context on credit strengths and challenges

After comprehensive research, provide analysis then end with this exact JSON format:

{{"credit_quality_simple": "Rating / Outlook" or "Not Rated", "credit_quality_detailed": "Detailed credit analysis with rating rationale, key metrics, and recent developments (Source: [agency/date])" or "Credit quality: Limited rating information available"}}"""

            result = self._make_financial_search(prompt, max_tokens=1800)
            if not result:
                return None

            # Extract both credit quality fields from the response
            import json
            import re
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    credit_results = {}
                    
                    simple_quality = data.get('credit_quality_simple', '')
                    detailed_quality = data.get('credit_quality_detailed', '')
                    
                    if simple_quality and FieldValidator.is_valid_field_value(simple_quality, 'credit_quality'):
                        credit_results['credit_quality'] = simple_quality
                        logger.info(f"   ✅ Found simple credit quality: {simple_quality}")
                    
                    if detailed_quality and FieldValidator.is_valid_field_value(detailed_quality, 'credit_quality_detailed'):
                        credit_results['credit_quality_detailed'] = detailed_quality
                        logger.info(f"   ✅ Found detailed credit quality: {detailed_quality[:100]}...")
                    
                    return credit_results if credit_results else None
                    
                except json.JSONDecodeError:
                    logger.warning("   🛑 Failed to parse credit quality JSON response")
                    return None
            else:
                logger.warning("   🛑 No JSON found in credit quality response")
                return None

        except Exception as e:
            logger.error(f"❌ Error searching credit quality: {str(e)}")
            return None

    def search_all_financial_data(self, hospital_name: str, location: str, website: str = None, skip_credit_fields: bool = False) -> Optional[Dict[str, str]]:
        """
        Search for comprehensive financial data using enhanced search strategies.

        Args:
            hospital_name: Name of the hospital/organization
            location: Location of the organization
            website: Optional website URL
            skip_credit_fields: If True, skip searching for credit quality fields (they're already populated by credit enricher)

        Returns:
            Dict of financial data fields
        """

        # Check if combined search should be used (faster single API call)
        use_combined_search = os.getenv("OPENAI_USE_COMBINED_SEARCH", "true").lower() == "true"

        if use_combined_search and FINANCIAL_MODEL == "gpt-5":
            return self._search_combined_financial_data(hospital_name, location, skip_credit_fields)
        else:
            return self._search_sequential_financial_data(hospital_name, location, skip_credit_fields)

    def _search_combined_financial_data(self, hospital_name: str, location: str, skip_credit_fields: bool = False) -> Optional[Dict[str, str]]:
        """Combined GPT-5 search for all financial metrics in one API call."""
        try:
            logger.info(f"🚀 Combined GPT-5 financial analysis for: {hospital_name}")
            logger.info(f"🧠 Using GPT-5 with {FINANCIAL_REASONING_EFFORT} reasoning effort...")

            if skip_credit_fields:
                logger.info("⚠️ Skipping credit quality fields (already populated by credit enricher)")

            start_time = time.time()

            # Build the prompt, optionally excluding credit quality
            credit_section = "" if skip_credit_fields else """
7. CREDIT QUALITY: Research credit ratings from Moody's, S&P, Fitch. Provide both simple rating format and detailed analysis."""

            credit_json_fields = "" if skip_credit_fields else """
    "credit_quality": "Rating / Outlook" or "Not Rated",
    "credit_quality_detailed": "Detailed credit analysis with rating rationale and key metrics (Source: [agency/date])" or "Credit quality: Limited rating information available"
"""

            combined_prompt = f"""Perform comprehensive financial analysis for {hospital_name} in {location}.

Research and provide results for ALL of the following financial metrics:

1. RECENT DISCLOSURES: Find recent financial disclosures, annual reports, bond offerings, rating updates from 2023-2024.

2. WACC CALCULATION: Calculate Weighted Average Cost of Capital using bond rates, credit ratings, financial statements, industry benchmarks.

3. DEBT APPETITE: Analyze current debt levels, borrowing capacity, recent debt activity, credit line utilization.

4. OTHER DEBT INSTRUMENTS: Identify equipment financing, capital leases, pension obligations, development authority bonds.

5. FINANCIAL OUTLOOK: Review capital project history, funding sources, financial performance trends over 5-7 years.

6. REVENUE: Find most recent annual revenue (2023-2024) from financial statements, Medicare cost reports, Form 990s. Format as simple dollar amount like $17.8B or $450M.{credit_section}

Note: Off-balance sheet appetite will be synthesized separately based on all collected data.

Return results in this exact JSON format:

{{
    "recent_disclosures": "• [Date] [Type]: $[Amount] - [Description]" or "No recent financial disclosures found",
    "wacc": "WACC: X.X% (Methodology: brief explanation, Confidence: High/Medium/Low)" or "WACC: Unable to calculate - insufficient data",
    "debt_appetite": "• Current debt: $[Amount]\\n• Capacity: $[Amount]\\n• Recent activity: [Description]" or "Debt capacity: Unable to assess - insufficient data",
    "other_debt": "• Equipment financing: $[Amount] - [Description]\\n• Capital leases: $[Amount] - [Description]" or "Other debt: Limited disclosure available",
    "financial_outlook": "Capital Projects: [recent major projects with amounts and dates]" or "Capital project history: Insufficient data",
    "revenue": "$X.XB" or "$X.XM" or "Revenue: Unable to determine from available sources"{("," + credit_json_fields) if credit_json_fields else ""}
}}"""

            response = self.openai_client.responses.create(
                model="gpt-5",
                reasoning={"effort": FINANCIAL_REASONING_EFFORT},
                tools=[
                    {
                        "type": "web_search",
                    }
                ],
                tool_choice="auto",
                input=combined_prompt,
                include=["web_search_call.action.sources"]
            )

            end_time = time.time()
            execution_time = end_time - start_time

            logger.info(f"✅ Combined analysis completed in {execution_time:.1f}s")

            # Extract all results from the single response
            financial_results = {}
            field_keys = ['recent_disclosures', 'wacc', 'debt_appetite', 'other_debt', 'financial_outlook', 'revenue']
            if not skip_credit_fields:
                field_keys.extend(['credit_quality', 'credit_quality_detailed'])

            # Try to extract JSON from response
            import json
            import re

            # Debug: Log the raw response
            logger.info(f"📄 Raw response length: {len(response.output_text)} chars")
            logger.info(f"📄 First 500 chars of response: {response.output_text[:500]}")

            json_match = re.search(r'\{.*\}', response.output_text, re.DOTALL)
            if json_match:
                try:
                    json_str = json_match.group(0)
                    logger.info(f"📄 Extracted JSON length: {len(json_str)} chars")
                    data = json.loads(json_str)
                    logger.info(f"📄 Parsed JSON keys: {list(data.keys())}")

                    for field_key in field_keys:
                        value = data.get(field_key)
                        logger.info(f"🔍 Checking {field_key}: value={'<present>' if value else '<empty>'}, length={len(str(value)) if value else 0}")

                        if value and FieldValidator.is_valid_field_value(value, field_key):
                            financial_results[field_key] = value
                            logger.info(f"   ✅ {field_key}: {value[:100]}...")
                        else:
                            if not value:
                                logger.info(f"   ❌ {field_key}: No data in response")
                            else:
                                logger.info(f"   ❌ {field_key}: Failed validation - {str(value)[:50]}")
                except json.JSONDecodeError as e:
                    logger.warning(f"❌ Failed to parse JSON from combined response: {e}")
                    logger.warning(f"❌ JSON string was: {json_str[:500]}")
                    return None
            else:
                logger.warning("❌ No JSON pattern found in response")
                logger.warning(f"❌ Response was: {response.output_text[:500]}")

            found_fields = list(financial_results.keys())
            logger.info(f"🚀 Combined search found data for {len(found_fields)} fields: {found_fields}")
            return financial_results

        except Exception as e:
            logger.error(f"❌ Error in combined financial analysis: {str(e)}")
            # Fallback to sequential search
            logger.info("🔄 Falling back to sequential search...")
            return self._search_sequential_financial_data(hospital_name, location, skip_credit_fields)

    def _search_sequential_financial_data(self, hospital_name: str, location: str, skip_credit_fields: bool = False) -> Optional[Dict[str, str]]:
        """Original sequential search method."""
        try:
            logger.info(f"💰 Sequential financial data search for: {hospital_name}")

            if skip_credit_fields:
                logger.info("⚠️ Skipping credit quality fields (already populated by credit enricher)")

            financial_results = {}

            # 1. Recent Disclosures
            disclosures_data = self.search_recent_disclosures(hospital_name, location)
            if disclosures_data:
                financial_results['recent_disclosures'] = disclosures_data
            time.sleep(2)  # Rate limiting

            # 2. Weighted Average Cost of Capital (WACC)
            wacc_data = self.search_wacc(hospital_name, location)
            if wacc_data:
                financial_results['wacc'] = wacc_data
            time.sleep(2)

            # 3. Debt Appetite and Constraints
            debt_appetite_data = self.search_debt_appetite(hospital_name, location)
            if debt_appetite_data:
                financial_results['debt_appetite'] = debt_appetite_data
            time.sleep(2)

            # 4. Other Debt Information
            other_debt_data = self.search_other_debt(hospital_name, location)
            if other_debt_data:
                financial_results['other_debt'] = other_debt_data
            time.sleep(2)

            # 5. Long-term Financial Outlook
            outlook_data = self.search_financial_outlook(hospital_name, location)
            if outlook_data:
                financial_results['financial_outlook'] = outlook_data
            time.sleep(2)

            # 6. Revenue
            revenue_data = self.search_revenue(hospital_name, location)
            if revenue_data:
                financial_results['revenue'] = revenue_data
            time.sleep(2)

            # 7. Credit Quality (both simple and detailed) - ONLY if not skipped
            if not skip_credit_fields:
                credit_data = self.search_credit_quality(hospital_name, location)
                if credit_data:
                    financial_results.update(credit_data)
            else:
                logger.info("⏭️ Skipped credit quality search (already populated)")

            found_fields = [k for k, v in financial_results.items() if v]
            logger.info(f"   ✅ Sequential search found financial data for {len(found_fields)} fields: {found_fields}")
            return financial_results

        except Exception as e:
            logger.error(f"❌ Error in sequential financial data search: {str(e)}")
            return None