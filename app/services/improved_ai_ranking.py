"""
Improved AI Ranking Service
AI ONLY ranks prospects based on complete LinkedIn data
AI does NOT create, modify, or invent data
"""

import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
import openai
from openai import OpenAI
import json

# Import centralized prompts
from app.prompts import (
    AI_RANKING_SYSTEM_PROMPT,
    AI_RANKING_USER_PROMPT_TEMPLATE
)

logger = logging.getLogger(__name__)


class ImprovedAIRankingService:
    """AI service that ONLY ranks prospects based on real LinkedIn data"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        # Use GPT-5 with Responses API
        self.model = os.getenv('OPENAI_MODEL', 'gpt-5-mini-2025-08-07')
        # Reasoning effort for reasoning models (minimal = fast, high = thorough)
        self.reasoning_effort = os.getenv('OPENAI_REASONING_EFFORT', 'minimal')

        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            logger.info(f"AI ranking service initialized with model: {self.model}, reasoning: {self.reasoning_effort}")
        else:
            self.client = None
            logger.warning("OPENAI_API_KEY not found in environment variables")
    
    async def rank_prospects(self, prospects: List[Dict], company_name: str) -> Dict[str, Any]:
        """
        Rank prospects using individual AI calls for each prospect
        
        Args:
            prospects: List of prospects with complete LinkedIn data
            company_name: Target company name for context
        
        Returns:
            Dictionary with ranked prospects (data unchanged, only rankings added)
        """
        if not self.client:
            return {
                "success": False,
                "error": "OpenAI client not configured - missing API key"
            }
        
        if not prospects:
            return {
                "success": False,
                "error": "No prospects to rank"
            }
        
        try:
            # Create individual ranking tasks for parallel processing
            ranking_tasks = []
            for i, prospect in enumerate(prospects):
                task = self._rank_single_prospect(prospect, company_name, i)
                ranking_tasks.append(task)

            # Execute all ranking calls in parallel
            logger.info(f"Starting AI ranking for {len(prospects)} prospects using {self.model}")
            ranking_results = await asyncio.gather(*ranking_tasks, return_exceptions=True)

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

            # Process results and apply rankings to prospects
            ranked_prospects = self._apply_individual_rankings_to_prospects(
                ranking_results, prospects
            )

            # Calculate successful rankings
            successful_rankings = len([r for r in ranking_results if isinstance(r, dict) and r.get("success")])

            logger.info(f"AI ranking complete: {successful_rankings}/{len(prospects)} succeeded")

            return {
                "success": True,
                "company_name": company_name,
                "total_prospects": len(prospects),
                "successfully_ranked": successful_rankings,
                "failed_rankings": len(prospects) - successful_rankings,
                "total_ranked": len(ranked_prospects),
                "ranked_prospects": ranked_prospects,
                "errors": errors if errors else None,
                "cost_estimate": successful_rankings * 0.003  # GPT-5 with minimal reasoning
            }

        except Exception as e:
            logger.error(f"Error ranking prospects: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    async def _rank_single_prospect(self, prospect: Dict, company_name: str, index: int) -> Dict[str, Any]:
        """
        Rank a single prospect with retry logic
        
        Args:
            prospect: Individual prospect with LinkedIn data
            company_name: Target company name
            index: Prospect index for tracking
        
        Returns:
            Dictionary with ranking result or error
        """
        linkedin_data = prospect.get("linkedin_data", {})
        
        # Extract prospect data for ranking
        # Safely get advanced_filter (handle None case)
        advanced_filter = prospect.get("advanced_filter") or {}

        prospect_data = {
            "name": linkedin_data.get("name", ""),
            "current_title": linkedin_data.get("job_title", ""),
            "current_company": linkedin_data.get("company", ""),
            "headline": linkedin_data.get("headline", ""),
            "summary": linkedin_data.get("summary", ""),
            "total_experience_years": linkedin_data.get("total_experience_years", 0),
            "professional_authority_score": linkedin_data.get("professional_authority_score", 0),
            "seniority_score": advanced_filter.get("seniority_score", 0),
            "recent_experience": linkedin_data.get("experience", [])[:3] if linkedin_data.get("experience") else [],
            "education": linkedin_data.get("education", [])[:2] if linkedin_data.get("education") else [],
            "skills": [skill.get("name", "") for skill in linkedin_data.get("skills", [])[:10]]
        }
        
        # Try ranking with one retry
        for attempt in range(2):
            try:
                prompt = self._build_individual_ranking_prompt(prospect_data, company_name)

                logger.debug(f"Ranking prospect {index} ({prospect_data.get('name', 'Unknown')}), attempt {attempt + 1}")

                # Use Responses API for GPT-5 models
                # Combine system prompt and user prompt into single input
                full_input = f"{AI_RANKING_SYSTEM_PROMPT}\n\n{prompt}"

                # Create response using Responses API
                # Note: reasoning.effort only supported by gpt-5 and o-series models
                # Note: temperature is NOT supported in Responses API for GPT-5/o-series
                api_params = {
                    "model": self.model,
                    "input": full_input,
                    "text": {"format": {"type": "json_object"}},
                    "max_output_tokens": 300,  # Reduced from 500 for faster responses
                    "timeout": 30
                }

                # Only add reasoning parameter for gpt-5 or o-series models
                if "gpt-5" in self.model or self.model.startswith("o"):
                    api_params["reasoning"] = {"effort": self.reasoning_effort}

                response = self.client.responses.create(**api_params)

                # Check if response is valid
                if not response:
                    error_msg = "API returned None response"
                    logger.warning(f"Prospect {index}, attempt {attempt + 1}: {error_msg}")
                    if attempt == 1:
                        return {"success": False, "index": index, "error": error_msg}
                    continue

                # Parse response from Responses API
                # Response format: response.output[0].content[0].text
                if not hasattr(response, 'output') or not response.output:
                    error_msg = "Response missing output field"
                    logger.warning(f"Prospect {index}, attempt {attempt + 1}: {error_msg}")
                    if attempt == 1:
                        return {"success": False, "index": index, "error": error_msg}
                    continue
                
                try:
                    # When reasoning is enabled, response.output has 2 items:
                    # [0] = ResponseReasoningItem (thinking, content=None)
                    # [1] = ResponseOutputMessage (actual response)
                    # So we need to access the last item which contains the actual output
                    output_item = response.output[-1]  # Get last item (the actual output message)
                    output_text = output_item.content[0].text
                except (IndexError, AttributeError, TypeError) as e:
                    error_msg = f"Error accessing response fields: {type(e).__name__}: {str(e)}"
                    logger.warning(f"Prospect {index}, attempt {attempt + 1}: {error_msg}")
                    if attempt == 1:
                        return {"success": False, "index": index, "error": error_msg}
                    continue
                
                ranking_data = json.loads(output_text)

                # Validate required fields
                if "score" in ranking_data:
                    # "reasoning" is optional but preferred
                    reasoning = ranking_data.get("reasoning", f"Score: {ranking_data['score']}")
                    logger.debug(f"Successfully ranked prospect {index}: {ranking_data['score']}/100")
                    return {
                        "success": True,
                        "index": index,
                        "reasoning": reasoning,
                        "score": int(ranking_data["score"])
                    }
                else:
                    error_msg = f"Missing 'score' field in response: {ranking_data}"
                    logger.warning(f"Prospect {index}, attempt {attempt + 1}: {error_msg}")
                    if attempt == 1:  # Last attempt
                        return {"success": False, "index": index, "error": error_msg}

            except json.JSONDecodeError as e:
                error_msg = f"JSON parse error: {str(e)}"
                logger.warning(f"Prospect {index}, attempt {attempt + 1}: {error_msg}")
                if attempt == 1:
                    return {"success": False, "index": index, "error": error_msg}
            except openai.APITimeoutError as e:
                error_msg = f"API timeout: {str(e)}"
                logger.warning(f"Prospect {index}, attempt {attempt + 1}: {error_msg}")
                if attempt == 1:
                    return {"success": False, "index": index, "error": error_msg}
            except openai.RateLimitError as e:
                error_msg = f"Rate limit exceeded: {str(e)}"
                logger.warning(f"Prospect {index}, attempt {attempt + 1}: {error_msg}")
                # Wait longer on rate limits
                await asyncio.sleep(2)
                if attempt == 1:
                    return {"success": False, "index": index, "error": error_msg}
            except Exception as e:
                import traceback
                error_msg = f"{type(e).__name__}: {str(e)}"
                stack_trace = traceback.format_exc()
                logger.warning(f"Prospect {index}, attempt {attempt + 1}: {error_msg}\n{stack_trace}")
                if attempt == 1:  # Last attempt
                    return {"success": False, "index": index, "error": error_msg}

        return {"success": False, "index": index, "error": "Failed after retries"}
    
    def _build_individual_ranking_prompt(self, prospect_data: Dict, company_name: str) -> str:
        """Build ranking prompt for individual prospect using centralized template"""
        # Safely handle None values
        summary = prospect_data.get('summary') or 'N/A'
        skills = prospect_data.get('skills') or []

        return AI_RANKING_USER_PROMPT_TEMPLATE.format(
            company_name=company_name,
            name=prospect_data.get('name') or 'N/A',
            title=prospect_data.get('current_title') or 'N/A',
            company=prospect_data.get('current_company') or 'N/A',
            summary=summary[:300],
            skills=', '.join(skills[:5]),
            experience_years=prospect_data.get('total_experience_years', 0)
        )
    
    def _build_ranking_prompt(self, prospects: List[Dict], company_name: str) -> str:
        """Build ranking prompt that focuses on scoring, not data creation"""
        return f"""
CRITICAL: You are ONLY ranking prospects based on provided data. DO NOT create, modify, or invent any information.

Rank these prospects for {company_name} based on their likelihood to make energy infrastructure purchasing decisions.

Target Buyer Personas (in priority order):
1. C-Suite (CEO, CFO, COO) - Ultimate decision authority
2. Facilities/Engineering Directors - Technical decision makers  
3. Sustainability/Energy Managers - Environmental compliance
4. Operations Directors - Efficiency focus
5. Finance Directors - Budget authority

Prospects to rank (REAL LinkedIn data provided):
{json.dumps(prospects, indent=2)}

Ranking Criteria (0-100 scale):
- Decision-making authority (40%) - Based on actual title and experience
- Technical relevance (25%) - Facilities, engineering, energy background
- Budget influence (20%) - Financial or operational responsibility
- Company seniority (15%) - Years of experience and authority indicators

Return ONLY ranking scores in this JSON format:
{{
  "prospect_rankings": [
    {{
      "index": 0,
      "ranking_score": 85,
      "decision_authority_level": "High",
      "persona_category": "Facilities Director",
      "ranking_reasoning": "15+ years facilities experience, direct infrastructure responsibility",
      "key_qualifications": ["infrastructure management", "15 years experience", "director level"],
      "potential_influence": "Direct decision maker for capital projects"
    }}
  ],
  "ranking_summary": {{
    "highest_scoring": 0,
    "total_high_potential": 3,
    "most_common_persona": "Facilities Director",
    "average_score": 67
  }}
}}

IMPORTANT RULES:
- Use ONLY the provided LinkedIn data for ranking decisions
- DO NOT create job titles, companies, or experience data
- DO NOT modify any prospect information
- ONLY provide ranking scores and reasoning based on existing data
"""
    
    def _apply_individual_rankings_to_prospects(self, ranking_results: List[Dict], original_prospects: List[Dict]) -> List[Dict]:
        """Apply individual AI rankings and return ALL prospects with scores >= 70"""

        # Create list of all successfully ranked prospects
        all_ranked_prospects = []

        for i, prospect in enumerate(original_prospects):
            # Find corresponding ranking result
            ranking_result = None
            for result in ranking_results:
                if isinstance(result, dict) and result.get("index") == i and result.get("success"):
                    ranking_result = result
                    break

            if ranking_result:  # Only process prospects that got successfully ranked
                # Add ranking data WITHOUT modifying original prospect data
                ranked_prospect = {
                    **prospect,  # Original prospect data (unchanged)
                    "ai_ranking": {
                        "ranking_score": ranking_result.get("score", 0),
                        "ranking_reasoning": ranking_result.get("reasoning", ""),
                        "ranked_by": "ai_individual",
                        "ranking_timestamp": None  # Would add in production
                    }
                }
                all_ranked_prospects.append(ranked_prospect)
            else:
                logger.warning(f"No successful ranking for prospect {i}: {prospect.get('linkedin_data', {}).get('name', 'Unknown')}")

        # Sort ALL ranked prospects by score (highest first)
        # Let the main discovery service handle the final threshold filtering
        all_ranked_prospects.sort(
            key=lambda x: x.get("ai_ranking", {}).get("ranking_score", 0),
            reverse=True
        )

        # Add rank position based on final order
        for i, prospect in enumerate(all_ranked_prospects):
            prospect["ai_ranking"]["rank_position"] = i + 1

        # If no AI rankings were successful, return empty list
        if not all_ranked_prospects:
            logger.error("No AI rankings were successful - returning empty prospect list")
            return []

        logger.info(f"Returning {len(all_ranked_prospects)} ranked prospects")

        return all_ranked_prospects
    
    
    async def generate_outreach_strategy(self, top_prospect: Dict, company_context: Dict = None) -> Dict[str, Any]:
        """Generate outreach strategy based on ranked prospect data"""
        if not self.client:
            return {
                "success": False,
                "error": "OpenAI client not configured"
            }
        
        try:
            linkedin_data = top_prospect.get("linkedin_data", {})
            ranking_data = top_prospect.get("ai_ranking", {})
            
            prompt = f"""
Generate an outreach strategy for this validated prospect:

Prospect Details (REAL LinkedIn data):
- Name: {linkedin_data.get('name', 'Professional')}
- Title: {linkedin_data.get('job_title', '')}
- Company: {linkedin_data.get('company', '')}
- Experience: {linkedin_data.get('total_experience_years', 0)} years
- Summary: {linkedin_data.get('summary', '')[:200]}

AI Ranking Analysis:
- Score: {ranking_data.get('ranking_score', 0)}/100
- Authority: {ranking_data.get('decision_authority_level', '')}
- Persona: {ranking_data.get('persona_category', '')}
- Reasoning: {ranking_data.get('ranking_reasoning', '')}

Create a personalized outreach strategy with:
1. Specific pain points they likely face
2. Value proposition tailored to their role
3. Recommended approach and timing
4. Key talking points for initial contact

Return JSON format:
{{
  "outreach_strategy": {{
    "primary_pain_points": ["specific challenges based on role"],
    "value_proposition": "Tailored value statement",
    "recommended_approach": "Email/LinkedIn/Phone preference",
    "key_talking_points": ["specific discussion topics"],
    "timing_recommendation": "Best time to reach out",
    "success_probability": "High/Medium/Low with reasoning"
  }}
}}
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert sales strategist creating outreach plans based on real prospect data."
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
            
            strategy_data = json.loads(response.choices[0].message.content)
            
            return {
                "success": True,
                "outreach_strategy": strategy_data.get("outreach_strategy", {}),
                "cost_estimate": 0.001
            }
            
        except Exception as e:
            logger.error(f"Error generating outreach strategy: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_ranking(self) -> Dict[str, Any]:
        """Test the ranking functionality"""
        if not self.client:
            return {
                "success": False,
                "error": "OpenAI client not configured"
            }
        
        # Test with sample complete LinkedIn data
        test_prospects = [
            {
                "linkedin_data": {
                    "name": "John Smith",
                    "job_title": "Director of Facilities",
                    "company": "City General Hospital",
                    "headline": "Facilities Director managing infrastructure and maintenance",
                    "total_experience_years": 12,
                    "professional_authority_score": 85
                },
                "advanced_filter": {"seniority_score": 70}
            },
            {
                "linkedin_data": {
                    "name": "Jane Doe",
                    "job_title": "Marketing Intern",
                    "company": "City General Hospital", 
                    "headline": "Marketing intern studying business",
                    "total_experience_years": 1,
                    "professional_authority_score": 20
                },
                "advanced_filter": {"seniority_score": 15}
            }
        ]
        
        try:
            result = await self.rank_prospects(test_prospects, "City General Hospital")
            return {
                "success": result.get("success", False),
                "test_data": "Sample hospital prospects",
                "ranking_result": result.get("ranked_prospects", [])
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Global instance  
improved_ai_ranking_service = ImprovedAIRankingService()
