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

logger = logging.getLogger(__name__)


class ImprovedAIRankingService:
    """AI service that ONLY ranks prospects based on real LinkedIn data"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            logger.info(f"AI ranking service initialized with model: {self.model}")
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
            ranking_results = await asyncio.gather(*ranking_tasks, return_exceptions=True)
            
            # Process results and apply rankings to prospects
            ranked_prospects = self._apply_individual_rankings_to_prospects(
                ranking_results, prospects
            )
            
            # Calculate successful rankings
            successful_rankings = len([r for r in ranking_results if isinstance(r, dict) and r.get("success")])
            
            return {
                "success": True,
                "company_name": company_name,
                "total_prospects": len(prospects),
                "successfully_ranked": successful_rankings,
                "total_ranked": len(ranked_prospects),
                "ranked_prospects": ranked_prospects,
                "cost_estimate": successful_rankings * 0.001  # Estimate per individual call
            }
            
        except Exception as e:
            logger.error(f"Error ranking prospects: {str(e)}")
            return {
                "success": False,
                "error": str(e)
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
        prospect_data = {
            "name": linkedin_data.get("name", ""),
            "current_title": linkedin_data.get("job_title", ""),
            "current_company": linkedin_data.get("company", ""),
            "headline": linkedin_data.get("headline", ""),
            "summary": linkedin_data.get("summary", ""),
            "total_experience_years": linkedin_data.get("total_experience_years", 0),
            "professional_authority_score": linkedin_data.get("professional_authority_score", 0),
            "seniority_score": prospect.get("advanced_filter", {}).get("seniority_score", 0),
            "recent_experience": linkedin_data.get("experience", [])[:3] if linkedin_data.get("experience") else [],
            "education": linkedin_data.get("education", [])[:2] if linkedin_data.get("education") else [],
            "skills": [skill.get("name", "") for skill in linkedin_data.get("skills", [])[:10]]
        }
        
        # Try ranking with one retry
        for attempt in range(2):
            try:
                prompt = self._build_individual_ranking_prompt(prospect_data, company_name)
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert sales analyst. Analyze the prospect and return ONLY a JSON response with 'reasoning' and 'score' fields."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.2,
                    max_tokens=500,
                    response_format={"type": "json_object"}
                )
                
                # Parse response
                ranking_data = json.loads(response.choices[0].message.content)
                
                # Validate required fields
                if "reasoning" in ranking_data and "score" in ranking_data:
                    return {
                        "success": True,
                        "index": index,
                        "reasoning": ranking_data["reasoning"],
                        "score": int(ranking_data["score"])
                    }
                else:
                    logger.warning(f"Invalid response format for prospect {index}, attempt {attempt + 1}")
                    if attempt == 1:  # Last attempt
                        return {"success": False, "index": index, "error": "Invalid response format"}
                    
            except Exception as e:
                logger.warning(f"Error ranking prospect {index}, attempt {attempt + 1}: {str(e)}")
                if attempt == 1:  # Last attempt
                    return {"success": False, "index": index, "error": str(e)}
        
        return {"success": False, "index": index, "error": "Failed after retries"}
    
    def _build_individual_ranking_prompt(self, prospect_data: Dict, company_name: str) -> str:
        """Build ranking prompt for individual prospect"""
        return f"""
Analyze this prospect for {company_name} and rate their likelihood to make energy infrastructure purchasing decisions.

PROSPECT DATA:
Name: {prospect_data.get('name', 'N/A')}
Title: {prospect_data.get('current_title', 'N/A')}
Company: {prospect_data.get('current_company', 'N/A')}
Headline: {prospect_data.get('headline', 'N/A')}
Summary: {prospect_data.get('summary', 'N/A')[:200]}...
Experience Years: {prospect_data.get('total_experience_years', 0)}
Authority Score: {prospect_data.get('professional_authority_score', 0)}
Seniority Score: {prospect_data.get('seniority_score', 0)}

RANKING CRITERIA (0-100 scale):
- Decision-making authority (40%) - C-Suite, Directors, VPs
- Technical relevance (25%) - Facilities, engineering, energy background  
- Budget influence (20%) - Financial or operational responsibility
- Company seniority (15%) - Years of experience and authority indicators

TARGET PERSONAS (priority order):
1. C-Suite (CEO, CFO, COO) - Ultimate decision authority
2. Facilities/Engineering Directors - Technical decision makers
3. Sustainability/Energy Managers - Environmental compliance
4. Operations Directors - Efficiency focus
5. Finance Directors - Budget authority

Return ONLY this JSON format:
{{
  "reasoning": "Brief explanation of score based on title, experience, and decision authority",
  "score": 85
}}
"""
    
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
        """Apply individual AI rankings and return the BEST prospect per target job title (max 5-8 total)"""
        
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
        
        # Sort ALL prospects by score (highest first)
        all_ranked_prospects.sort(
            key=lambda x: x.get("ai_ranking", {}).get("ranking_score", 0),
            reverse=True
        )
        
        # Select the BEST prospect for each unique target title (max 8 prospects)
        prospects_by_title = {}
        final_prospects = []
        
        for prospect in all_ranked_prospects:
            target_title = prospect.get("target_title", "Unknown")
            
                # If we haven't seen this target title yet, take this prospect (the highest scoring one)
            if target_title not in prospects_by_title:
                prospects_by_title[target_title] = True
                final_prospects.append(prospect)
                
                # Stop at 8 prospects maximum
                if len(final_prospects) >= 8:
                    break
        
        # If no AI rankings were successful, fall back to seniority-based ranking
        if not final_prospects and original_prospects:
            logger.warning("No AI rankings available, falling back to seniority-based ranking")
            return self._fallback_ranking_by_seniority(original_prospects)
        
        # Add rank position based on final order
        for i, prospect in enumerate(final_prospects):
            prospect["ai_ranking"]["rank_position"] = i + 1
        
        logger.info(f"Selected top {len(final_prospects)} prospects (one per target title) from {len(all_ranked_prospects)} ranked prospects")
        
        return final_prospects
    
    def _fallback_ranking_by_seniority(self, prospects: List[Dict]) -> List[Dict]:
        """Fallback ranking using seniority scores when AI ranking fails"""
        logger.info("Using seniority-based fallback ranking")
        
        # Add fallback ranking based on seniority scores
        for prospect in prospects:
            seniority_score = prospect.get("advanced_filter", {}).get("seniority_score", 0)
            linkedin_data = prospect.get("linkedin_data", {})
            
            prospect["ai_ranking"] = {
                "ranking_score": seniority_score,  # Use seniority as fallback score
                "ranking_reasoning": f"Fallback ranking based on seniority score ({seniority_score})",
                "ranked_by": "seniority_fallback",
                "ranking_timestamp": None
            }
        
        # Sort by seniority score
        prospects.sort(
            key=lambda x: x.get("ai_ranking", {}).get("ranking_score", 0),
            reverse=True
        )
        
        # Select best prospect for each unique target title (max 8)
        prospects_by_title = {}
        final_prospects = []
        
        for prospect in prospects:
            target_title = prospect.get("target_title", "Unknown")
            
            if target_title not in prospects_by_title:
                prospects_by_title[target_title] = True
                final_prospects.append(prospect)
                
                if len(final_prospects) >= 8:
                    break
        
        # Add rank positions
        for i, prospect in enumerate(final_prospects):
            prospect["ai_ranking"]["rank_position"] = i + 1
        
        logger.info(f"Fallback ranking selected {len(final_prospects)} prospects using seniority scores")
        return final_prospects
    
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
