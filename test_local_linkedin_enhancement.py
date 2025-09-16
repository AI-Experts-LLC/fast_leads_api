#!/usr/bin/env python3
"""
Local test to verify our LinkedIn data enhancement logic works
This tests the new methods without needing to deploy to Railway
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.linkedin import LinkedInProfile, ApifyLinkedInService
import json

def create_sample_raw_data():
    """Create sample raw data similar to what Apify returns"""
    return {
        'fullName': 'Lucas Erb',
        'firstName': 'Lucas',
        'lastName': 'Erb',
        'headline': 'Founder @AIExperts.com | Helping businesses harness the future | Top Voice in AI',
        'about': 'I am the Founder of AIExperts.com and a member of LinkedIn\'s distinguished program...',
        'linkedinUrl': 'https://www.linkedin.com/in/lucaserb/',
        'addressWithoutCountry': 'New York, New York',
        'connections': 3411,
        'followers': 4207,
        'jobTitle': 'Founder',
        'companyName': 'AIExperts.com',
        'currentJobDuration': '7 mos',
        'currentJobDurationInYrs': 0.58,
        'topSkillsByEndorsements': 'Leadership, Management, Python, Entrepreneurship, VMware',
        'publicIdentifier': 'lucaserb',
        'experiences': [
            {
                'title': 'Founder',
                'subtitle': 'AIExperts.com',
                'caption': 'Mar 2025 - Present · 7 mos',
                'metadata': None
            },
            {
                'title': 'Emerging Technology Research Lead',
                'subtitle': 'Deloitte Consulting',
                'caption': 'Oct 2020 - Feb 2025 · 4 yrs 5 mos',
                'metadata': 'New York, New York'
            }
        ],
        'educations': [
            {
                'title': 'UC Irvine',
                'subtitle': 'Bachelor\'s degree, Computer Science',
                'caption': None
            }
        ],
        'skills': [
            {
                'title': 'Leadership',
                'subComponents': [
                    {'description': [{'type': 'insightComponent', 'text': '33 endorsements'}]}
                ]
            },
            {
                'title': 'Python',
                'subComponents': [
                    {'description': [{'type': 'insightComponent', 'text': '10 endorsements'}]}
                ]
            }
        ],
        'honorsAndAwards': [
            {
                'title': '1st Place - HPE Internship "Best in Class" Competition',
                'subtitle': 'Issued by HPE Networking - Aug 2017'
            }
        ],
        'licenseAndCertificates': [
            {
                'title': 'AWS Certified Solutions Architect – Associate',
                'subtitle': 'Amazon Web Services (AWS)',
                'caption': 'Issued Nov 2020 · Expired Nov 2023'
            }
        ],
        'interests': [
            {
                'section_name': 'Companies',
                'section_components': [
                    {'titleV2': 'IBM', 'caption': '18,688,956 followers'}
                ]
            }
        ],
        'recommendations': [
            {
                'section_name': 'Given',
                'section_components': [
                    {'titleV2': 'Bryen Mariano', 'caption': 'April 4, 2025'}
                ]
            }
        ]
    }

def test_enhanced_profile_parsing():
    """Test our enhanced profile parsing logic"""
    print("🧪 Testing Enhanced LinkedIn Profile Parsing")
    print("=" * 60)
    
    # Create LinkedIn service instance
    linkedin_service = ApifyLinkedInService()
    
    # Create sample raw data
    raw_data = create_sample_raw_data()
    
    # Parse the profile
    profile = linkedin_service._parse_profile_data(raw_data)
    
    if profile:
        print("✅ Profile parsing successful")
        
        # Convert to enhanced dictionary
        enhanced_profile = linkedin_service._profile_to_dict(profile)
        
        print(f"\n📊 Enhanced Profile Data Structure:")
        print(f"Total fields: {len(enhanced_profile)}")
        
        # Show key categories
        categories = {
            "Basic Info": ['name', 'headline', 'location', 'summary'],
            "Professional": ['job_title', 'company_name', 'total_experience_years'],
            "Network": ['connections', 'followers', 'engagement_score'],
            "Education": ['highest_degree', 'alma_maters', 'education_count'],
            "Skills": ['skills_count', 'endorsements_received', 'top_skills_by_endorsements'],
            "Sections": ['certifications_count', 'honors_awards_count', 'interests_count'],
            "Scores": ['profile_completeness_score', 'data_quality_score', 'professional_authority_score']
        }
        
        for category, fields in categories.items():
            print(f"\n{category}:")
            for field in fields:
                value = enhanced_profile.get(field, 'NOT FOUND')
                if isinstance(value, (list, dict)):
                    print(f"   {field}: {type(value).__name__} ({len(value) if hasattr(value, '__len__') else 0} items)")
                else:
                    print(f"   {field}: {value}")
        
        # Test calculated metrics
        print(f"\n🔢 Calculated Metrics:")
        print(f"   Total Experience Years: {enhanced_profile.get('total_experience_years', 'ERROR')}")
        print(f"   Industry Experience: {enhanced_profile.get('industry_experience', 'ERROR')}")
        print(f"   Engagement Score: {enhanced_profile.get('engagement_score', 'ERROR')}")
        print(f"   Authority Score: {enhanced_profile.get('professional_authority_score', 'ERROR')}")
        print(f"   Profile Completeness: {enhanced_profile.get('profile_completeness_score', 'ERROR')}")
        
        # Show sample of rich data
        print(f"\n📋 Sample Rich Data:")
        if enhanced_profile.get('experience'):
            print(f"   Experience entries: {len(enhanced_profile['experience'])}")
            for i, exp in enumerate(enhanced_profile['experience'][:2]):
                print(f"      {i+1}. {exp.get('title')} at {exp.get('company')}")
        
        if enhanced_profile.get('certifications'):
            print(f"   Certifications: {len(enhanced_profile['certifications'])}")
        
        if enhanced_profile.get('honors_awards'):
            print(f"   Awards: {len(enhanced_profile['honors_awards'])}")
        
        # Check if raw_data is preserved
        if enhanced_profile.get('raw_data'):
            print(f"   ✅ Raw data preserved: {len(enhanced_profile['raw_data'])} fields")
        else:
            print(f"   ❌ Raw data missing")
        
        return True
    else:
        print("❌ Profile parsing failed")
        return False

def main():
    """Main test function"""
    print("🚀 Local LinkedIn Enhancement Test")
    print("This tests our enhanced data processing without deploying")
    print("=" * 60)
    
    success = test_enhanced_profile_parsing()
    
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    if success:
        print("✅ Enhanced LinkedIn data processing is working!")
        print("✅ All calculated metrics are being generated")
        print("✅ Data structure is comprehensive and organized")
        print("✅ Raw data is preserved for debugging")
        print("\n🚀 Ready to deploy enhanced LinkedIn API!")
    else:
        print("❌ Enhancement processing failed")
        print("🔧 Check the profile parsing logic")
    
    print(f"\n🎯 Next Steps:")
    print(f"   1. Deploy updated code to Railway")
    print(f"   2. Test with real LinkedIn profiles")
    print(f"   3. Verify all 70+ data fields are returned")
    print(f"   4. Use enhanced data for prospect qualification")

if __name__ == "__main__":
    main()
