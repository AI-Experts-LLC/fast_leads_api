"""
AI-powered prospect qualification using OpenAI
"""

import os
import logging
from typing import List, Dict, Any, Optional
import openai
from openai import OpenAI
import json

logger = logging.getLogger(__name__)


class OpenAIQualificationService:
    """Service for AI-powered prospect qualification and ranking"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("OPENAI_API_KEY not found in environment variables")
    
    async def qualify_prospects(self, search_results: List[Dict], company_name: str) -> Dict[str, Any]:
        """
        Use AI to qualify and rank prospects from search results
        
        Args:
            search_results: List of search results with LinkedIn profiles
            company_name: Company name for context
        
        Returns:
            Dictionary with qualified prospects ranked by relevance
        """
        if not self.client:
            return {
                "success": False,
                "error": "OpenAI client not configured - missing API key"
            }
        
        if not search_results:
            return {
                "success": False,
                "error": "No search results to qualify"
            }
        
        try:
            # Prepare prospect data for AI analysis
            prospects_for_analysis = []
            for i, result in enumerate(search_results):  # Limit to 10 for cost control
                prospects_for_analysis.append({
                    "index": i,
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                    "linkedin_url": result.get("link", ""),
                    "target_title": result.get("target_title", ""),
                    "position": result.get("position", 0)
                })
            
            # Create the qualification prompt
            prompt = self._build_qualification_prompt(prospects_for_analysis, company_name)
            
            # Call OpenAI API (synchronous within async function)
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert sales research analyst specializing in identifying high-value prospects for energy efficiency and infrastructure solutions in healthcare facilities."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            # Parse AI response
            ai_response = json.loads(response.choices[0].message.content)
            
            # Rank prospects based on AI scoring
            qualified_prospects = self._process_ai_response(ai_response, search_results)
            
            return {
                "success": True,
                "company_name": company_name,
                "total_analyzed": len(prospects_for_analysis),
                "qualified_prospects": qualified_prospects,
                "ai_analysis": ai_response,
                "cost_estimate": 0.02  # Rough estimate for GPT-4 call
            }
            
        except Exception as e:
            logger.error(f"Error qualifying prospects: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_qualification_prompt(self, prospects: List[Dict], company_name: str) -> str:
        """Build the qualification prompt for OpenAI"""
        return f"""
Analyze these LinkedIn prospects for {company_name} and identify the most valuable targets for energy infrastructure and efficiency solutions.

IMPORTANT: These prospects have already been validated as CURRENTLY employed at {company_name} or its divisions/subsidiaries.

Target Buyer Personas (in order of priority):
1. Director of Facilities/Engineering/Maintenance - Primary decision maker for infrastructure projects
2. CFO/Financial Leadership - Budget authority for capital projects
3. Sustainability Manager/Energy Manager - Environmental goals and compliance
4. COO/Director of Operations - Operational efficiency focus
5. Compliance Manager - Regulatory requirements

Company Context: {company_name}
Industry Focus: Healthcare facilities, hospitals, medical centers

Pre-validated Prospects to analyze:
{json.dumps(prospects, indent=2)}

For each prospect, consider their employment validation data if available:
- employment_validation.confidence_score: How confident we are they currently work there
- employment_validation.company_match_type: Type of company match (exact/variation/subsidiary)
- employment_validation.detected_company_name: Actual company name found
- employment_validation.validation_reasoning: Evidence for current employment

Please analyze each prospect and return a JSON response with this structure:
{{
  "top_prospects": [
    {{
      "index": 0,
      "linkedin_url": "url",
      "qualification_score": 95,
      "persona_match": "Director of Facilities",
      "decision_authority": "High",
      "employment_confidence": "High",
      "reasoning": "Specific reasons why this person is a high-value target, including employment validation confidence",
      "pain_points": ["infrastructure costs", "deferred maintenance"],
      "outreach_approach": "Focus on infrastructure upgrades and off-balance sheet financing",
      "company_context": "Insights about their specific role at this organization"
    }}
  ],
  "analysis_summary": {{
    "total_qualified": 3,
    "highest_priority_persona": "Director of Facilities",
    "company_insights": "Key insights about this company's likely needs",
    "employment_validation_summary": "Summary of how employment validation affected scoring"
  }}
}}

Enhanced Scoring criteria (0-100):
- Job title relevance to energy/facilities decisions (35%)
- Decision-making authority level (25%) 
- Employment validation confidence (20%)
- Company size and budget likelihood (15%)
- Accessibility and engagement potential (5%)

Employment confidence bonus:
- Add +10 points for high employment validation confidence (90-100%)
- Add +5 points for medium employment validation confidence (70-89%)
- No bonus for low confidence (<70%)

Only include prospects with scores ≥ 70. Rank by qualification score descending.
"""
    
    def _process_ai_response(self, ai_response: Dict, original_results: List[Dict]) -> List[Dict]:
        """Process AI response and combine with original search results"""
        qualified_prospects = []
        
        top_prospects = ai_response.get("top_prospects", [])
        
        for prospect in top_prospects:
            index = prospect.get("index", -1)
            if 0 <= index < len(original_results):
                # Combine AI analysis with original search data
                qualified_prospect = {
                    **original_results[index],  # Original search result
                    "qualification_score": prospect.get("qualification_score", 0),
                    "persona_match": prospect.get("persona_match", ""),
                    "decision_authority": prospect.get("decision_authority", ""),
                    "ai_reasoning": prospect.get("reasoning", ""),
                    "pain_points": prospect.get("pain_points", []),
                    "outreach_approach": prospect.get("outreach_approach", ""),
                    "priority_rank": len(qualified_prospects) + 1
                }
                qualified_prospects.append(qualified_prospect)
        
        return qualified_prospects
    
    async def generate_personalized_message(self, prospect: Dict, company_context: Dict = None) -> Dict[str, Any]:
        """Generate a personalized outreach message for a qualified prospect"""
        if not self.client:
            return {
                "success": False,
                "error": "OpenAI client not configured"
            }
        
        try:
            prompt = f"""
Generate a personalized LinkedIn outreach message for this prospect:

Prospect Details:
- Name: {prospect.get('title', 'Professional')}
- Title/Role: {prospect.get('persona_match', 'Decision Maker')}
- Company: {company_context.get('name', 'their organization') if company_context else 'their organization'}
- LinkedIn Profile: {prospect.get('snippet', '')}

Pain Points Identified: {', '.join(prospect.get('pain_points', []))}
Recommended Approach: {prospect.get('outreach_approach', '')}

Create a professional, personalized message that:
1. Shows you've researched their role and company
2. Addresses their likely pain points
3. Offers clear value proposition for energy/infrastructure solutions
4. Includes a soft call-to-action
5. Keeps it under 150 wordsx
6. Maintains a consultative, helpful tone

Return JSON format:
{{
  "message": "Hi [Name], I noticed your role as [Title] at [Company]...",
  "subject_line": "Energy cost optimization for [Company]",
  "personalization_elements": ["role research", "company mention", "pain point focus"],
  "tone": "professional consultative"
}}
"""
            
            # Call OpenAI API (synchronous within async function)
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert sales copywriter specializing in B2B energy infrastructure solutions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            message_data = json.loads(response.choices[0].message.content)
            
            return {
                "success": True,
                "personalized_message": message_data,
                "cost_estimate": 0.01
            }
            
        except Exception as e:
            logger.error(f"Error generating personalized message: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_qualification(self) -> Dict[str, Any]:
        """Test the qualification functionality"""
        if not self.client:
            return {
                "success": False,
                "error": "OpenAI client not configured"
            }
        
        # Test with sample data
        test_prospects = [
            {
                "title": "John Smith - Director of Facilities at City General Hospital",
                "snippet": "Experienced facilities director managing infrastructure and maintenance for 500-bed hospital",
                "link": "https://linkedin.com/in/test",
                "target_title": "Director of Facilities"
            }
        ]
        
        try:
            result = await self.qualify_prospects(test_prospects, "City General Hospital")
            return {
                "success": result.get("success", False),
                "test_data": "Sample hospital facilities director",
                "qualification_result": result.get("qualified_prospects", [])
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Global instance
ai_qualification_service = OpenAIQualificationService()
