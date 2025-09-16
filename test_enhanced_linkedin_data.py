#!/usr/bin/env python3
"""
Test script to verify all enhanced LinkedIn data is being returned
This will show the complete structure with all the new fields
"""

import requests
import json
from datetime import datetime

API_BASE_URL = "https://fast-leads-api.up.railway.app"

def test_enhanced_linkedin_data():
    """Test that all enhanced data fields are being returned"""
    
    test_profiles = [
        "https://www.linkedin.com/in/lucaserb/",
        "https://www.linkedin.com/in/emollick/"
    ]
    
    print("🔍 Testing Enhanced LinkedIn Data Structure")
    print("=" * 60)
    
    try:
        # Prepare the request
        request_data = {
            "linkedin_urls": test_profiles,
            "include_detailed_data": True
        }
        
        # Make the API call
        response = requests.post(
            f"{API_BASE_URL}/linkedin/scrape-profiles",
            json=request_data,
            timeout=90
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data and data['data'].get('profiles'):
                profiles = data['data']['profiles']
                
                print(f"✅ Successfully retrieved {len(profiles)} profiles with enhanced data")
                
                for i, profile in enumerate(profiles):
                    print(f"\n{'='*60}")
                    print(f"📊 ENHANCED PROFILE {i+1} DATA STRUCTURE")
                    print(f"{'='*60}")
                    
                    # Show all available fields organized by category
                    show_profile_data_structure(profile)
                    
                    # Show calculated metrics
                    show_calculated_metrics(profile)
                    
                    # Show data quality assessment
                    show_data_quality_assessment(profile)
                
                print(f"\n{'='*60}")
                print("🎯 ENHANCED DATA SUMMARY")
                print(f"{'='*60}")
                
                # Count total fields available
                total_fields = len(profiles[0].keys()) if profiles else 0
                print(f"Total data fields per profile: {total_fields}")
                
                # Show key enhancements
                print(f"\n🆕 New Enhanced Fields:")
                enhanced_fields = [
                    'total_experience_years', 'industry_experience', 'highest_degree',
                    'alma_maters', 'recommendations_count', 'endorsements_received',
                    'engagement_score', 'accessibility_score', 'professional_authority_score',
                    'profile_completeness_score', 'data_quality_score', 'total_sections_completed'
                ]
                
                for field in enhanced_fields:
                    if profiles and field in profiles[0]:
                        value = profiles[0][field]
                        print(f"   ✅ {field}: {value}")
                
            else:
                print("❌ No profile data in response")
        else:
            print(f"❌ Request failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

def show_profile_data_structure(profile):
    """Display the organized data structure of a profile"""
    
    categories = {
        "Basic Information": [
            'url', 'name', 'first_name', 'last_name', 'headline', 
            'summary', 'about', 'location'
        ],
        "Current Position": [
            'job_title', 'company', 'company_name', 'company_industry',
            'company_website', 'company_linkedin', 'company_size',
            'current_job_duration', 'current_job_duration_years'
        ],
        "Network & Social Proof": [
            'connections', 'followers', 'engagement_score',
            'accessibility_score', 'professional_authority_score'
        ],
        "Experience & Career": [
            'experience_count', 'total_experience_years', 'industry_experience',
            'experience'
        ],
        "Education": [
            'education_count', 'highest_degree', 'alma_maters', 'education'
        ],
        "Skills & Expertise": [
            'skills_count', 'top_skills_by_endorsements', 'endorsements_received',
            'skills'
        ],
        "Additional Sections": [
            'interests_count', 'languages_count', 'certifications_count',
            'honors_awards_count', 'volunteer_work_count', 'projects_count',
            'publications_count', 'recommendations_count'
        ],
        "Contact & Accessibility": [
            'email', 'mobile_number', 'phone', 'website',
            'is_open_to_work', 'is_hiring'
        ],
        "Profile Quality Metrics": [
            'profile_completeness_score', 'data_quality_score',
            'total_sections_completed', 'has_profile_picture'
        ]
    }
    
    for category, fields in categories.items():
        print(f"\n📋 {category}:")
        for field in fields:
            if field in profile:
                value = profile[field]
                if isinstance(value, (list, dict)):
                    print(f"   {field}: {type(value).__name__} with {len(value) if hasattr(value, '__len__') else 'N/A'} items")
                else:
                    # Truncate long strings
                    str_value = str(value)
                    display_value = str_value[:100] + "..." if len(str_value) > 100 else str_value
                    print(f"   {field}: {display_value}")

def show_calculated_metrics(profile):
    """Show the calculated enhancement metrics"""
    print(f"\n🔢 CALCULATED METRICS:")
    
    metrics = {
        'Total Experience Years': profile.get('total_experience_years', 'N/A'),
        'Industry Experience': profile.get('industry_experience', {}),
        'Highest Degree': profile.get('highest_degree', 'N/A'),
        'Alma Maters': profile.get('alma_maters', []),
        'Total Endorsements': profile.get('endorsements_received', 0),
        'Recommendations Given/Received': profile.get('recommendations_count', {}),
        'Engagement Score (0-100)': profile.get('engagement_score', 0),
        'Accessibility Score (0-100)': profile.get('accessibility_score', 0),
        'Authority Score (0-100)': profile.get('professional_authority_score', 0),
        'Profile Completeness (0-100)': profile.get('profile_completeness_score', 0),
        'Data Quality Score (0-100)': profile.get('data_quality_score', 0),
        'Completed Sections': profile.get('total_sections_completed', 0)
    }
    
    for metric, value in metrics.items():
        if isinstance(value, dict) and value:
            print(f"   {metric}: {json.dumps(value, indent=6)}")
        elif isinstance(value, list) and value:
            print(f"   {metric}: {', '.join(map(str, value[:3]))}{'...' if len(value) > 3 else ''}")
        else:
            print(f"   {metric}: {value}")

def show_data_quality_assessment(profile):
    """Show assessment of data richness and quality"""
    print(f"\n📈 DATA RICHNESS ASSESSMENT:")
    
    # Count non-empty fields
    total_fields = len(profile)
    non_empty_fields = sum(1 for v in profile.values() if v not in [None, '', [], {}])
    completion_rate = (non_empty_fields / total_fields * 100) if total_fields > 0 else 0
    
    print(f"   Total Fields: {total_fields}")
    print(f"   Non-Empty Fields: {non_empty_fields}")
    print(f"   Completion Rate: {completion_rate:.1f}%")
    
    # Check for rich sections
    rich_sections = []
    if profile.get('experience') and len(profile['experience']) > 2:
        rich_sections.append("Rich Experience History")
    if profile.get('recommendations') and len(profile['recommendations']) > 0:
        rich_sections.append("Has Recommendations")
    if profile.get('certifications') and len(profile['certifications']) > 0:
        rich_sections.append("Has Certifications")
    if profile.get('projects') and len(profile['projects']) > 0:
        rich_sections.append("Has Projects")
    if profile.get('honors_awards') and len(profile['honors_awards']) > 0:
        rich_sections.append("Has Awards/Honors")
    if profile.get('volunteer_work') and len(profile['volunteer_work']) > 0:
        rich_sections.append("Has Volunteer Experience")
    if profile.get('followers', 0) > 1000:
        rich_sections.append("High Social Proof (>1K followers)")
    
    if rich_sections:
        print(f"   Rich Data Indicators: {', '.join(rich_sections)}")
    else:
        print(f"   Rich Data Indicators: Basic profile data available")

def main():
    """Main function to test enhanced data"""
    print("🚀 Enhanced LinkedIn Data Test")
    print("=" * 60)
    print("This test verifies that all the rich LinkedIn data")
    print("we saw in the raw response is now properly structured")
    print("and enhanced with calculated metrics.")
    print("=" * 60)
    
    test_enhanced_linkedin_data()
    
    print(f"\n🎯 SUMMARY:")
    print(f"If successful, you should see:")
    print(f"   ✅ 70+ data fields per profile")
    print(f"   ✅ Organized data categories")
    print(f"   ✅ Calculated metrics (scores, totals, etc.)")
    print(f"   ✅ Data quality assessments")
    print(f"   ✅ All the detailed info from the raw Apify response")

if __name__ == "__main__":
    main()
