#!/usr/bin/env python3
"""
Comprehensive test that runs enhanced prospect discovery and exports all data to files
This demonstrates the full 88-field LinkedIn data capture and analysis
"""

import requests
import json
import csv
from datetime import datetime
import os

API_BASE_URL = "https://fast-leads-api.up.railway.app"

def test_and_export_prospect_discovery():
    """Run prospect discovery and export all enhanced data to files"""
    
    print("🚀 Enhanced Prospect Discovery - Full Data Export Test")
    print("=" * 70)
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"prospect_discovery_export_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"📁 Export Directory: {output_dir}")
    
    # Test with multiple companies to show data variety
    test_companies = [
        {
            "company_name": "Mayo Clinic",
            "target_titles": ["Director of Facilities", "CFO", "COO", "Energy Manager"]
        },
        {
            "company_name": "Cleveland Clinic", 
            "target_titles": ["Director of Engineering", "VP Operations", "Facilities Manager"]
        }
    ]
    
    all_prospects = []
    test_results = []
    
    for i, test_case in enumerate(test_companies):
        print(f"\n{'='*50}")
        print(f"🏥 TEST CASE {i+1}: {test_case['company_name']}")
        print(f"{'='*50}")
        
        try:
            # Run prospect discovery
            print(f"📤 Running prospect discovery...")
            print(f"   Company: {test_case['company_name']}")
            print(f"   Target Titles: {test_case['target_titles']}")
            
            response = requests.post(
                f"{API_BASE_URL}/discover-prospects",
                json=test_case,
                timeout=120
            )
            
            print(f"📥 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success' and 'data' in data:
                    result = data['data']
                    
                    # Store test result
                    test_results.append({
                        "company": test_case['company_name'],
                        "success": True,
                        "pipeline_summary": result.get('pipeline_summary', {}),
                        "cost_estimates": result.get('cost_estimates', {}),
                        "prospects_found": len(result.get('qualified_prospects', []))
                    })
                    
                    # Process prospects
                    prospects = result.get('qualified_prospects', [])
                    print(f"✅ Found {len(prospects)} qualified prospects")
                    
                    for prospect in prospects:
                        # Add test case info
                        prospect['test_company'] = test_case['company_name']
                        prospect['test_timestamp'] = timestamp
                        all_prospects.append(prospect)
                    
                    # Export individual company data
                    export_company_data(result, test_case['company_name'], output_dir)
                    
                else:
                    error_msg = data.get('detail', 'Unknown error')
                    print(f"❌ Prospect discovery failed: {error_msg}")
                    test_results.append({
                        "company": test_case['company_name'],
                        "success": False,
                        "error": error_msg,
                        "prospects_found": 0
                    })
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', f'HTTP {response.status_code}')
                except:
                    error_msg = f'HTTP {response.status_code}'
                
                print(f"❌ Request failed: {error_msg}")
                test_results.append({
                    "company": test_case['company_name'],
                    "success": False,
                    "error": error_msg,
                    "prospects_found": 0
                })
                
        except Exception as e:
            print(f"❌ Test case failed: {e}")
            test_results.append({
                "company": test_case['company_name'],
                "success": False,
                "error": str(e),
                "prospects_found": 0
            })
    
    # Export combined data
    if all_prospects:
        export_combined_analysis(all_prospects, test_results, output_dir)
    
    # Generate summary report
    generate_summary_report(test_results, all_prospects, output_dir)
    
    print(f"\n{'='*70}")
    print("📊 EXPORT COMPLETE")
    print(f"{'='*70}")
    print(f"📁 All files exported to: {output_dir}/")
    print(f"📋 Files created:")
    
    for file in os.listdir(output_dir):
        file_path = os.path.join(output_dir, file)
        size_kb = os.path.getsize(file_path) / 1024
        print(f"   📄 {file} ({size_kb:.1f} KB)")

def export_company_data(result, company_name, output_dir):
    """Export data for a specific company"""
    safe_company_name = company_name.replace(" ", "_").replace("/", "_")
    
    # 1. Export full JSON response
    json_file = f"{output_dir}/{safe_company_name}_full_response.json"
    with open(json_file, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    # 2. Export prospects CSV
    prospects = result.get('qualified_prospects', [])
    if prospects:
        csv_file = f"{output_dir}/{safe_company_name}_prospects.csv"
        export_prospects_to_csv(prospects, csv_file)
    
    # 3. Export LinkedIn data analysis
    linkedin_file = f"{output_dir}/{safe_company_name}_linkedin_analysis.json"
    linkedin_analysis = analyze_linkedin_data(prospects)
    with open(linkedin_file, 'w') as f:
        json.dump(linkedin_analysis, f, indent=2, default=str)

def export_prospects_to_csv(prospects, filename):
    """Export prospect data to CSV with flattened structure"""
    flattened_prospects = []
    
    for prospect in prospects:
        flat_prospect = {}
        
        # Basic qualification data
        flat_prospect.update({
            'qualification_score': prospect.get('qualification_score', 0),
            'persona_match': prospect.get('persona_match', ''),
            'decision_authority': prospect.get('decision_authority', ''),
            'priority_rank': prospect.get('priority_rank', 0),
            'linkedin_url': prospect.get('linkedin_url', ''),
            'company_name': prospect.get('company_name', ''),
            'test_company': prospect.get('test_company', ''),
        })
        
        # LinkedIn summary data (business intelligence)
        linkedin_summary = prospect.get('linkedin_summary', {})
        for key, value in linkedin_summary.items():
            if not isinstance(value, (dict, list)):
                flat_prospect[f'linkedin_{key}'] = value
            elif isinstance(value, dict) and key == 'industry_experience':
                # Flatten industry experience
                for industry, years in value.items():
                    flat_prospect[f'experience_{industry}_years'] = years
            elif isinstance(value, list) and key in ['alma_maters']:
                flat_prospect[f'linkedin_{key}'] = ', '.join(map(str, value[:3]))
        
        # AI reasoning (truncated for CSV)
        ai_reasoning = prospect.get('ai_reasoning', '')
        flat_prospect['ai_reasoning'] = ai_reasoning[:200] + '...' if len(ai_reasoning) > 200 else ai_reasoning
        
        flattened_prospects.append(flat_prospect)
    
    # Write to CSV using standard library
    if flattened_prospects:
        fieldnames = list(flattened_prospects[0].keys())
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flattened_prospects)

def analyze_linkedin_data(prospects):
    """Analyze the LinkedIn data richness across prospects"""
    analysis = {
        'total_prospects': len(prospects),
        'prospects_with_linkedin_data': 0,
        'average_scores': {},
        'data_completeness': {},
        'field_availability': {},
        'top_companies': {},
        'experience_analysis': {},
        'education_analysis': {},
        'contact_intelligence': {}
    }
    
    if not prospects:
        return analysis
    
    prospects_with_data = []
    all_scores = {'authority': [], 'engagement': [], 'accessibility': [], 'completeness': []}
    field_counts = {}
    companies = {}
    industries = {}
    degrees = {}
    contact_methods = {'email': 0, 'phone': 0, 'website': 0}
    
    for prospect in prospects:
        linkedin_data = prospect.get('linkedin_data', {})
        linkedin_summary = prospect.get('linkedin_summary', {})
        
        if linkedin_summary.get('has_detailed_data'):
            prospects_with_data.append(prospect)
            analysis['prospects_with_linkedin_data'] += 1
            
            # Collect scores
            all_scores['authority'].append(linkedin_summary.get('professional_authority_score', 0))
            all_scores['engagement'].append(linkedin_summary.get('engagement_score', 0))
            all_scores['accessibility'].append(linkedin_summary.get('accessibility_score', 0))
            all_scores['completeness'].append(linkedin_summary.get('profile_completeness_score', 0))
            
            # Count field availability
            for field, value in linkedin_data.items():
                if value not in [None, '', [], {}]:
                    field_counts[field] = field_counts.get(field, 0) + 1
            
            # Company analysis
            company = linkedin_summary.get('company', '')
            if company:
                companies[company] = companies.get(company, 0) + 1
            
            # Industry experience
            industry_exp = linkedin_summary.get('industry_experience', {})
            for industry, years in industry_exp.items():
                if industry not in industries:
                    industries[industry] = []
                industries[industry].append(years)
            
            # Education analysis
            degree = linkedin_summary.get('highest_degree', '')
            if degree and degree != 'Unknown':
                degrees[degree] = degrees.get(degree, 0) + 1
            
            # Contact availability
            if linkedin_summary.get('email'):
                contact_methods['email'] += 1
            if linkedin_summary.get('phone'):
                contact_methods['phone'] += 1
            if linkedin_summary.get('website'):
                contact_methods['website'] += 1
    
    # Calculate averages
    for score_type, scores in all_scores.items():
        if scores:
            analysis['average_scores'][score_type] = {
                'average': round(sum(scores) / len(scores), 1),
                'min': min(scores),
                'max': max(scores)
            }
    
    # Data completeness
    total_prospects_with_data = len(prospects_with_data)
    if total_prospects_with_data > 0:
        for field, count in field_counts.items():
            analysis['field_availability'][field] = {
                'count': count,
                'percentage': round(count / total_prospects_with_data * 100, 1)
            }
    
    # Top companies
    analysis['top_companies'] = dict(sorted(companies.items(), key=lambda x: x[1], reverse=True)[:5])
    
    # Experience analysis
    for industry, years_list in industries.items():
        if years_list:
            analysis['experience_analysis'][industry] = {
                'average_years': round(sum(years_list) / len(years_list), 1),
                'total_professionals': len(years_list)
            }
    
    # Education analysis
    analysis['education_analysis'] = dict(sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:5])
    
    # Contact intelligence
    analysis['contact_intelligence'] = {
        'email_available': f"{contact_methods['email']}/{total_prospects_with_data} ({contact_methods['email']/total_prospects_with_data*100:.1f}%)" if total_prospects_with_data > 0 else "0/0",
        'phone_available': f"{contact_methods['phone']}/{total_prospects_with_data} ({contact_methods['phone']/total_prospects_with_data*100:.1f}%)" if total_prospects_with_data > 0 else "0/0",
        'website_available': f"{contact_methods['website']}/{total_prospects_with_data} ({contact_methods['website']/total_prospects_with_data*100:.1f}%)" if total_prospects_with_data > 0 else "0/0"
    }
    
    return analysis

def export_combined_analysis(all_prospects, test_results, output_dir):
    """Export combined analysis across all companies"""
    
    # 1. Combined prospects CSV
    combined_csv = f"{output_dir}/all_prospects_combined.csv"
    export_prospects_to_csv(all_prospects, combined_csv)
    
    # 2. Combined LinkedIn analysis
    combined_analysis = analyze_linkedin_data(all_prospects)
    analysis_file = f"{output_dir}/combined_linkedin_analysis.json"
    with open(analysis_file, 'w') as f:
        json.dump(combined_analysis, f, indent=2, default=str)
    
    # 3. Detailed prospect profiles
    detailed_file = f"{output_dir}/detailed_prospect_profiles.json"
    with open(detailed_file, 'w') as f:
        json.dump(all_prospects, f, indent=2, default=str)

def generate_summary_report(test_results, all_prospects, output_dir):
    """Generate a comprehensive summary report"""
    
    report = []
    report.append("# Enhanced Prospect Discovery - Test Report")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Test Summary
    report.append("## Test Summary")
    report.append(f"- **Total Companies Tested**: {len(test_results)}")
    successful_tests = sum(1 for r in test_results if r['success'])
    report.append(f"- **Successful Tests**: {successful_tests}/{len(test_results)}")
    total_prospects = sum(r['prospects_found'] for r in test_results)
    report.append(f"- **Total Qualified Prospects Found**: {total_prospects}")
    report.append("")
    
    # Individual Company Results
    report.append("## Company Results")
    for result in test_results:
        report.append(f"### {result['company']}")
        if result['success']:
            pipeline = result.get('pipeline_summary', {})
            costs = result.get('cost_estimates', {})
            report.append(f"- **Status**: ✅ Success")
            report.append(f"- **Search Results**: {pipeline.get('search_results_found', 0)}")
            report.append(f"- **Validated Prospects**: {pipeline.get('prospects_validated', 0)}")
            report.append(f"- **Qualified Prospects**: {pipeline.get('prospects_qualified', 0)}")
            report.append(f"- **LinkedIn Profiles Scraped**: {pipeline.get('linkedin_profiles_scraped', 0)}")
            report.append(f"- **Total Cost**: ${costs.get('total_estimated', 0):.3f}")
        else:
            report.append(f"- **Status**: ❌ Failed")
            report.append(f"- **Error**: {result.get('error', 'Unknown')}")
        report.append("")
    
    # LinkedIn Data Analysis
    if all_prospects:
        analysis = analyze_linkedin_data(all_prospects)
        report.append("## LinkedIn Data Analysis")
        report.append(f"- **Prospects with LinkedIn Data**: {analysis['prospects_with_linkedin_data']}/{analysis['total_prospects']}")
        
        if analysis['average_scores']:
            report.append("### Average Scores")
            for score_type, scores in analysis['average_scores'].items():
                report.append(f"- **{score_type.title()}**: {scores['average']}/100 (range: {scores['min']}-{scores['max']})")
        
        if analysis['experience_analysis']:
            report.append("### Industry Experience")
            for industry, data in analysis['experience_analysis'].items():
                report.append(f"- **{industry.title()}**: {data['average_years']} avg years ({data['total_professionals']} professionals)")
        
        if analysis['contact_intelligence']:
            report.append("### Contact Intelligence")
            ci = analysis['contact_intelligence']
            report.append(f"- **Email Available**: {ci['email_available']}")
            report.append(f"- **Phone Available**: {ci['phone_available']}")
            report.append(f"- **Website Available**: {ci['website_available']}")
    
    # Enhanced Data Fields
    report.append("## Enhanced Data Fields Available")
    report.append("Each prospect now includes 88 LinkedIn data fields organized into:")
    report.append("- Basic Profile Information (8 fields)")
    report.append("- Current Position Details (9 fields)")
    report.append("- Network & Social Proof (5 fields)")
    report.append("- Experience & Career Intelligence (4 fields)")
    report.append("- Education Background (4 fields)")
    report.append("- Skills & Expertise (4 fields)")
    report.append("- Contact & Accessibility (6 fields)")
    report.append("- Additional Profile Sections (20+ fields)")
    report.append("- Calculated Business Metrics (6 fields)")
    report.append("- Profile Quality Assessment (6 fields)")
    report.append("- Geographic Information (7 fields)")
    report.append("- Meta Information (5+ fields)")
    report.append("")
    
    # Files Generated
    report.append("## Files Generated")
    for file in os.listdir(output_dir):
        if file.endswith('.md'):
            continue
        file_path = os.path.join(output_dir, file)
        size_kb = os.path.getsize(file_path) / 1024
        report.append(f"- **{file}** ({size_kb:.1f} KB)")
    
    # Write report
    report_file = f"{output_dir}/test_report.md"
    with open(report_file, 'w') as f:
        f.write('\n'.join(report))

def main():
    """Main test and export function"""
    print("🔬 Enhanced Prospect Discovery - Full Data Export")
    print("This test demonstrates the complete 88-field LinkedIn data capture")
    print("and exports all results to files for analysis.")
    print("")
    
    test_and_export_prospect_discovery()
    
    print(f"\n🎯 Test Complete!")
    print(f"📊 All enhanced prospect data has been exported to files")
    print(f"📋 Use the generated files to analyze the rich LinkedIn intelligence")
    print(f"💼 Each prospect includes comprehensive business intelligence scores")

if __name__ == "__main__":
    main()
