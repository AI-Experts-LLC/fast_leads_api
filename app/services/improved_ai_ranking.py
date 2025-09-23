"""
Improved AI Ranking Service
AI ONLY ranks prospects based on complete LinkedIn data
AI does NOT create, modify, or invent data
"""

import os
import logging
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
        Rank prospects based on their complete LinkedIn data
        
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
            # Prepare prospect data for ranking (extract only relevant fields)
            prospects_for_ranking = []
            for i, prospect in enumerate(prospects):
                linkedin_data = prospect.get("linkedin_data", {})
                
                # Extract ONLY the data needed for ranking decisions
                ranking_data = {
                    "index": i,
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
                    "skills": linkedin_data.get("skills", [])[:10] if linkedin_data.get("skills") else []
                }
                prospects_for_ranking.append(ranking_data)
            
            # Create ranking prompt
            prompt = self._build_ranking_prompt(prospects_for_ranking, company_name)
            
            # Call OpenAI API for ranking ONLY
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert sales analyst who ranks prospects based on their likelihood to make energy infrastructure purchasing decisions. You ONLY provide ranking scores - you do NOT modify, create, or invent any prospect data."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            # Parse ranking response
            ranking_response = json.loads(response.choices[0].message.content)
            
            # Apply rankings to original prospects (data unchanged)
            ranked_prospects = self._apply_rankings_to_prospects(
                ranking_response, prospects
            )
            
            return {
                "success": True,
                "company_name": company_name,
                "total_ranked": len(ranked_prospects),
                "ranked_prospects": ranked_prospects,
                "ranking_analysis": ranking_response,
                "cost_estimate": 0.002
            }
            
        except Exception as e:
            logger.error(f"Error ranking prospects: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
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
- Rank only prospects with scores ≥ 60
"""
    
    def _apply_rankings_to_prospects(self, ranking_response: Dict, original_prospects: List[Dict]) -> List[Dict]:
        """Apply AI rankings to original prospects without modifying prospect data"""
        ranked_prospects = []
        
        prospect_rankings = ranking_response.get("prospect_rankings", [])
        
        # Create ranking lookup
        ranking_lookup = {}
        for ranking in prospect_rankings:
            index = ranking.get("index", -1)
            if index >= 0:
                ranking_lookup[index] = ranking
        
        # Apply rankings to prospects and sort
        for i, prospect in enumerate(original_prospects):
            ranking_data = ranking_lookup.get(i, {})
            
            if ranking_data:  # Only include prospects that got ranked
                # Add ranking data WITHOUT modifying original prospect data
                ranked_prospect = {
                    **prospect,  # Original prospect data (unchanged)
                    "ai_ranking": {
                        "ranking_score": ranking_data.get("ranking_score", 0),
                        "decision_authority_level": ranking_data.get("decision_authority_level", ""),
                        "persona_category": ranking_data.get("persona_category", ""),
                        "ranking_reasoning": ranking_data.get("ranking_reasoning", ""),
                        "key_qualifications": ranking_data.get("key_qualifications", []),
                        "potential_influence": ranking_data.get("potential_influence", ""),
                        "ranked_by": "ai",
                        "ranking_timestamp": None  # Would add in production
                    }
                }
                ranked_prospects.append(ranked_prospect)
        
        # Sort by ranking score (highest first)
        ranked_prospects.sort(
            key=lambda x: x.get("ai_ranking", {}).get("ranking_score", 0),
            reverse=True
        )
        
        # Add rank position
        for i, prospect in enumerate(ranked_prospects):
            prospect["ai_ranking"]["rank_position"] = i + 1
        
        return ranked_prospects
    
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
