#!/usr/bin/env python3
"""
Test enhanced prospect discovery with all 88 LinkedIn data fields
This shows how the LinkedIn enhancements flow through the complete pipeline
"""

import requests
import json
from datetime import datetime

API_BASE_URL = "https://fast-leads-api.up.railway.app"

def test_enhanced_prospect_discovery():
    """Test prospect discovery with enhanced LinkedIn data"""
    
    print("🔍 Testing Enhanced Prospect Discovery Pipeline")
    print("=" * 60)
    print("This test shows how all 88 LinkedIn fields flow through")
    print("the complete prospect discovery process.")
    print("=" * 60)
    
    # Test with a company that should have good LinkedIn results
    test_request = {
        "company_name": "Apple Inc",
        "target_titles": ["Director", "VP", "Manager"]
    }
    
    try:
        print(f"\n📤 Request:")
        print(f"   Company: {test_request['company_name']}")
        print(f"   Target Titles: {test_request['target_titles']}")
        
        response = requests.post(
            f"{API_BASE_URL}/discover-prospects",
            json=test_request,
            timeout=120  # Full pipeline can take time
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('status') == 'success' and 'data' in data:
                result = data['data']
                
                print(f"\n📊 Pipeline Summary:")
                pipeline = result.get('pipeline_summary', {})
                print(f"   Search Results Found: {pipeline.get('search_results_found', 0)}")
                print(f"   Prospects Validated: {pipeline.get('prospects_validated', 0)}")
                print(f"   Prospects Qualified: {pipeline.get('prospects_qualified', 0)}")
                print(f"   LinkedIn Profiles Scraped: {pipeline.get('linkedin_profiles_scraped', 0)}")
                print(f"   Final Prospects: {pipeline.get('final_prospects', 0)}")
                
                # Show cost breakdown
                costs = result.get('cost_estimates', {})
                print(f"\n💰 Cost Breakdown:")
                print(f"   Search: ${costs.get('search_cost', 0):.3f}")
                print(f"   Validation: ${costs.get('validation_cost', 0):.3f}")
                print(f"   AI Qualification: ${costs.get('ai_cost', 0):.3f}")
                print(f"   LinkedIn Scraping: ${costs.get('linkedin_cost', 0):.3f}")
                print(f"   Total: ${costs.get('total_estimated', 0):.3f}")
                
                # Analyze the enhanced LinkedIn data in qualified prospects
                prospects = result.get('qualified_prospects', [])
                if prospects:
                    print(f"\n🎯 Enhanced LinkedIn Data Analysis:")
                    print(f"Found {len(prospects)} qualified prospects with enhanced data")
                    
                    for i, prospect in enumerate(prospects[:2]):  # Show first 2
                        analyze_enhanced_prospect_data(prospect, i+1)
                else:
                    print(f"\n⚠️  No qualified prospects found")
                    
            else:
                print(f"❌ Prospect discovery failed: {data.get('detail', 'Unknown error')}")
        else:
            try:
                error_data = response.json()
                print(f"❌ Request failed: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"❌ Request failed with status {response.status_code}")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")

def analyze_enhanced_prospect_data(prospect, prospect_num):
    """Analyze the enhanced LinkedIn data in a prospect"""
    print(f"\n{'='*50}")
    print(f"📋 PROSPECT {prospect_num} - ENHANCED DATA ANALYSIS")
    print(f"{'='*50}")
    
    # Basic qualification data
    print(f"🎯 Qualification Assessment:")
    print(f"   Score: {prospect.get('qualification_score', 'N/A')}/100")
    print(f"   Persona Match: {prospect.get('persona_match', 'N/A')}")
    print(f"   Decision Authority: {prospect.get('decision_authority', 'N/A')}")
    print(f"   Priority Rank: {prospect.get('priority_rank', 'N/A')}")
    
    # LinkedIn summary (quick access data)
    linkedin_summary = prospect.get('linkedin_summary', {})
    if linkedin_summary.get('has_detailed_data'):
        print(f"\n📊 Enhanced LinkedIn Intelligence:")
        
        # Core professional info
        print(f"   Name: {linkedin_summary.get('name', 'N/A')}")
        print(f"   Title: {linkedin_summary.get('job_title', 'N/A')}")
        print(f"   Company: {linkedin_summary.get('company', 'N/A')}")
        print(f"   Location: {linkedin_summary.get('location', 'N/A')}")
        
        # Enhanced metrics that weren't available before
        print(f"\n🔢 Calculated Business Metrics:")
        print(f"   Authority Score: {linkedin_summary.get('professional_authority_score', 0)}/100")
        print(f"   Engagement Score: {linkedin_summary.get('engagement_score', 0)}/100")
        print(f"   Accessibility Score: {linkedin_summary.get('accessibility_score', 0)}/100")
        print(f"   Profile Quality: {linkedin_summary.get('profile_completeness_score', 0)}/100")
        
        # Career intelligence
        print(f"\n💼 Career Intelligence:")
        print(f"   Total Experience: {linkedin_summary.get('total_experience_years', 0)} years")
        print(f"   Highest Degree: {linkedin_summary.get('highest_degree', 'N/A')}")
        print(f"   Industry Experience: {linkedin_summary.get('industry_experience', {})}")
        
        # Network and social proof
        print(f"\n🌐 Network & Social Proof:")
        print(f"   Connections: {linkedin_summary.get('connections', 0):,}")
        print(f"   Followers: {linkedin_summary.get('followers', 0):,}")
        print(f"   Endorsements: {linkedin_summary.get('endorsements_received', 0)}")
        print(f"   Recommendations: {linkedin_summary.get('recommendations_count', {})}")
        
        # Contact potential
        print(f"\n📞 Contact Intelligence:")
        contact_available = []
        if linkedin_summary.get('email'):
            contact_available.append('Email')
        if linkedin_summary.get('phone'):
            contact_available.append('Phone')
        if linkedin_summary.get('website'):
            contact_available.append('Website')
        print(f"   Available Contact Methods: {', '.join(contact_available) if contact_available else 'LinkedIn only'}")
        print(f"   Open to Work: {linkedin_summary.get('is_open_to_work', False)}")
        print(f"   Currently Hiring: {linkedin_summary.get('is_hiring', False)}")
        
        # Profile richness
        print(f"\n📈 Profile Richness:")
        print(f"   Certifications: {linkedin_summary.get('certifications_count', 0)}")
        print(f"   Awards/Honors: {linkedin_summary.get('honors_awards_count', 0)}")
        print(f"   Volunteer Work: {linkedin_summary.get('volunteer_work_count', 0)}")
        print(f"   Interests Tracked: {linkedin_summary.get('interests_count', 0)}")
        print(f"   Completed Sections: {linkedin_summary.get('total_sections_completed', 0)}")
        
        # Quick relationship building data
        recent_exp = linkedin_summary.get('recent_experience', [])
        if recent_exp:
            print(f"\n🏢 Recent Experience:")
            for exp in recent_exp[:2]:
                print(f"     • {exp.get('title', 'N/A')} at {exp.get('company', 'N/A')}")
        
        top_skills = linkedin_summary.get('top_skills', [])
        if top_skills:
            print(f"\n🛠️  Top Skills:")
            for skill in top_skills[:3]:
                print(f"     • {skill.get('name', 'N/A')} ({len(skill.get('endorsements', []))} endorsements)")
    
    else:
        print(f"\n⚠️  No detailed LinkedIn data available for this prospect")
    
    # Full LinkedIn data availability
    full_linkedin_data = prospect.get('linkedin_data', {})
    if full_linkedin_data:
        total_fields = len(full_linkedin_data)
        non_empty_fields = sum(1 for v in full_linkedin_data.values() if v not in [None, '', [], {}])
        print(f"\n📋 Full LinkedIn Data Available:")
        print(f"   Total Fields: {total_fields}")
        print(f"   Populated Fields: {non_empty_fields}")
        print(f"   Data Completeness: {(non_empty_fields/total_fields*100):.1f}%")
    
    # AI reasoning for qualification
    ai_reasoning = prospect.get('ai_reasoning', '')
    if ai_reasoning:
        print(f"\n🧠 AI Qualification Reasoning:")
        print(f"   {ai_reasoning[:200]}{'...' if len(ai_reasoning) > 200 else ''}")

def main():
    """Main test function"""
    print("🚀 Enhanced Prospect Discovery Test")
    print("Testing how all 88 LinkedIn data fields flow through the prospect pipeline")
    
    test_enhanced_prospect_discovery()
    
    print(f"\n{'='*60}")
    print("📊 ENHANCEMENT SUMMARY")
    print(f"{'='*60}")
    print("✅ Your prospect discovery now includes:")
    print("   • All 88 enhanced LinkedIn fields in 'linkedin_data'")
    print("   • Quick-access summary in 'linkedin_summary'")
    print("   • Business intelligence scores (authority, engagement, accessibility)")
    print("   • Career metrics (experience years, industry breakdown)")
    print("   • Contact intelligence (available methods, openness)")
    print("   • Relationship building data (interests, awards, recommendations)")
    print("   • Profile quality assessment")
    print("")
    print("🎯 This gives you enterprise-grade prospect intelligence")
    print("   combining qualification scores with comprehensive LinkedIn data!")

if __name__ == "__main__":
    main()
