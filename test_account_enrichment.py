#!/usr/bin/env python3
"""
Test Account Enrichment Logic
"""

import asyncio
from app.services.enrichment import (
    validate_account_for_enrichment,
    determine_buyer_personas,
    generate_persona_message
)

async def test_account_enrichment():
    print("🏥 TESTING ACCOUNT ENRICHMENT LOGIC")
    print("=" * 50)
    
    # Test different hospital types
    test_accounts = [
        {
            "Id": "001XX000003DHP0YAO",
            "Name": "City General Hospital",
            "Industry": "Healthcare", 
            "AnnualRevenue": 75000000,
            "NumberOfEmployees": 300,
            "BillingCity": "New York",
            "BillingState": "NY"
        },
        {
            "Id": "001XX000003DHP0YAP", 
            "Name": "Metro Medical Center",
            "Industry": "Healthcare",
            "AnnualRevenue": 150000000,
            "NumberOfEmployees": 800,
            "BillingCity": "Chicago", 
            "BillingState": "IL"
        },
        {
            "Id": "001XX000003DHP0YAQ",
            "Name": "Small Community Clinic", 
            "Industry": "Healthcare",
            "AnnualRevenue": 5000000,
            "NumberOfEmployees": 25,
            "BillingCity": "Austin",
            "BillingState": "TX"
        }
    ]
    
    for i, account in enumerate(test_accounts, 1):
        print(f"\n{i}️⃣ Testing: {account['Name']}")
        print(f"   Revenue: ${account['AnnualRevenue']:,}")
        print(f"   Employees: {account['NumberOfEmployees']}")
        
        # Test validation
        is_valid = await validate_account_for_enrichment(account)
        print(f"   Valid for enrichment: {'✅ Yes' if is_valid else '❌ No'}")
        
        # Test personas
        personas = determine_buyer_personas(account)
        print(f"   Buyer personas ({len(personas)}):")
        for persona in personas:
            print(f"     - {persona}")
        
        # Test message generation for first persona
        if personas:
            test_prospect = {
                "first_name": "John",
                "title": personas[0],
                "company": account["Name"]
            }
            
            message = generate_persona_message(
                test_prospect, 
                personas[0], 
                ["Energy Costs", "Compliance"]
            )
            print(f"   Sample message ({len(message)} chars):")
            print(f"     {message[:150]}...")

if __name__ == "__main__":
    asyncio.run(test_account_enrichment())
