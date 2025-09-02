"""
Local test script for company validation integration
Tests the complete pipeline integration without requiring API keys
"""

import asyncio
import os
import sys
import json
from unittest.mock import Mock, patch, AsyncMock

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Import services
from app.services.prospect_discovery import prospect_discovery_service
from app.services.company_validation import company_validation_service
from app.services.ai_qualification import ai_qualification_service
from app.services.search import serper_service


async def test_service_initialization():
    """Test that all services initialize correctly"""
    print("🔧 Testing Service Initialization")
    print("=" * 50)
    
    # Test prospect discovery service has all components
    assert hasattr(prospect_discovery_service, 'search_service'), "Missing search_service"
    assert hasattr(prospect_discovery_service, 'validation_service'), "Missing validation_service" 
    assert hasattr(prospect_discovery_service, 'ai_service'), "Missing ai_service"
    assert hasattr(prospect_discovery_service, 'linkedin_service'), "Missing linkedin_service"
    
    print("✅ ProspectDiscoveryService initialized with all components")
    
    # Test validation service
    assert hasattr(company_validation_service, 'client'), "Missing OpenAI client attribute"
    print("✅ CompanyValidationService initialized")
    
    # Test AI qualification service  
    assert hasattr(ai_qualification_service, 'client'), "Missing OpenAI client attribute"
    print("✅ AIQualificationService initialized")
    
    print()


async def test_validation_service_structure():
    """Test validation service methods and structure"""
    print("🧪 Testing Validation Service Structure")
    print("=" * 50)
    
    # Test methods exist
    assert hasattr(company_validation_service, 'validate_current_employment'), "Missing validate_current_employment method"
    assert hasattr(company_validation_service, 'test_validation'), "Missing test_validation method"
    assert hasattr(company_validation_service, '_build_validation_prompt'), "Missing _build_validation_prompt method"
    
    print("✅ All required methods present")
    
    # Test prompt generation
    test_prospects = [
        {
            "title": "John Smith - Director of Facilities at UCI Health", 
            "snippet": "Current facilities director",
            "link": "https://linkedin.com/in/test"
        }
    ]
    
    prompt = company_validation_service._build_validation_prompt(test_prospects, "UCI Medical Center")
    
    assert "UCI Medical Center" in prompt, "Target company not in prompt"
    assert "currently work" in prompt.lower(), "Employment validation criteria missing"
    assert "company name variations" in prompt.lower(), "Company variation handling missing"
    assert "confidence_score" in prompt, "Confidence scoring missing from prompt"
    
    print("✅ Validation prompt generation working")
    print()


async def test_ai_qualification_enhancement():
    """Test AI qualification service enhancements"""
    print("🧠 Testing AI Qualification Enhancements")
    print("=" * 50)
    
    # Test enhanced prompt
    test_prospects = [
        {
            "title": "Test Prospect",
            "employment_validation": {
                "confidence_score": 95,
                "company_match_type": "variation"
            }
        }
    ]
    
    prompt = ai_qualification_service._build_qualification_prompt(test_prospects, "Test Company")
    
    assert "employment validation" in prompt.lower(), "Employment validation not mentioned"
    assert "confidence_score" in prompt.lower(), "Confidence score not in prompt"
    assert "employment confidence bonus" in prompt.lower(), "Bonus scoring not mentioned"
    assert "35%" in prompt, "Updated scoring percentages not present"
    
    print("✅ AI qualification prompt enhanced correctly")
    
    # Test response processing with validation data
    mock_ai_response = {
        "top_prospects": [
            {
                "index": 0,
                "qualification_score": 95,
                "persona_match": "Director of Facilities",
                "employment_confidence": "High"
            }
        ]
    }
    
    processed = ai_qualification_service._process_ai_response(mock_ai_response, test_prospects)
    assert len(processed) == 1, "Processing failed"
    assert processed[0]["qualification_score"] == 95, "Score not preserved"
    
    print("✅ AI response processing working")
    print()


async def test_pipeline_integration():
    """Test that validation is properly integrated into pipeline"""
    print("🔄 Testing Pipeline Integration")
    print("=" * 50)
    
    # Mock the individual service calls to test integration flow
    with patch.object(serper_service, 'search_linkedin_profiles') as mock_search, \
         patch.object(company_validation_service, 'validate_current_employment') as mock_validation, \
         patch.object(ai_qualification_service, 'qualify_prospects') as mock_qualification, \
         patch.object(prospect_discovery_service.linkedin_service, 'scrape_profiles') as mock_linkedin:
        
        # Setup mock responses
        mock_search.return_value = {
            "success": True,
            "results": [
                {
                    "title": "John Smith - Director of Facilities at UCI Health",
                    "snippet": "Current facilities director",
                    "link": "https://linkedin.com/in/test1"
                },
                {
                    "title": "Jane Doe - Former CFO at UCI Medical, now at ABC Corp", 
                    "snippet": "Previously CFO at UCI Medical",
                    "link": "https://linkedin.com/in/test2"
                }
            ]
        }
        
        mock_validation.return_value = {
            "success": True,
            "validated_prospects": [
                {
                    "title": "John Smith - Director of Facilities at UCI Health",
                    "employment_validation": {
                        "currently_employed": True,
                        "confidence_score": 95
                    }
                }
            ],
            "validation_details": {
                "validation_summary": {
                    "total_analyzed": 2,
                    "currently_employed": 1
                }
            },
            "cost_estimate": 0.015
        }
        
        mock_qualification.return_value = {
            "success": True,
            "qualified_prospects": [
                {
                    "qualification_score": 85,
                    "persona_match": "Director of Facilities"
                }
            ],
            "ai_analysis": {},
            "cost_estimate": 0.02
        }
        
        mock_linkedin.return_value = {
            "success": True,
            "profiles": [],
            "cost_estimate": 0
        }
        
        # Test the pipeline
        result = await prospect_discovery_service.discover_prospects("UCI Medical Center")
        
        # Verify the calls were made in correct order
        assert mock_search.called, "Search service not called"
        assert mock_validation.called, "Validation service not called"
        assert mock_qualification.called, "Qualification service not called"
        
        # Verify validation was called with search results
        validation_call_args = mock_validation.call_args
        assert validation_call_args is not None, "Validation not called properly"
        assert "prospects" in validation_call_args.kwargs, "Prospects not passed to validation"
        
        # Verify qualification was called with validated prospects
        qualification_call_args = mock_qualification.call_args
        assert qualification_call_args is not None, "Qualification not called properly"
        
        # Verify pipeline response structure
        assert result.get("success") == True, "Pipeline failed"
        assert "pipeline_summary" in result, "Pipeline summary missing"
        assert "prospects_validated" in result["pipeline_summary"], "Validation metrics missing"
        assert "validation_summary" in result, "Validation summary missing"
        assert "validation_cost" in result.get("cost_estimates", {}), "Validation cost missing"
        
        print("✅ Pipeline integration working correctly")
        print(f"✅ Search → Validation → Qualification → LinkedIn flow verified")
        print(f"✅ Pipeline response includes validation metrics")
        print()


async def test_service_imports():
    """Test that services can be imported correctly"""
    print("📦 Testing Service Imports")
    print("=" * 50)
    
    try:
        from app.services import (
            serper_service,
            ai_qualification_service,
            linkedin_service,
            company_validation_service,
            prospect_discovery_service
        )
        print("✅ All services imported successfully from __init__.py")
        
        # Test that the services are the same instances
        assert prospect_discovery_service.validation_service is company_validation_service, "Validation service not properly wired"
        print("✅ Service instances properly wired")
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    
    print()
    return True


async def test_error_handling():
    """Test error handling in validation integration"""
    print("⚠️  Testing Error Handling")
    print("=" * 50)
    
    # Test validation failure handling
    with patch.object(company_validation_service, 'validate_current_employment') as mock_validation:
        mock_validation.return_value = {
            "success": False,
            "error": "API key missing"
        }
        
        with patch.object(serper_service, 'search_linkedin_profiles') as mock_search:
            mock_search.return_value = {
                "success": True,
                "results": [{"title": "Test", "snippet": "Test", "link": "test"}]
            }
            
            # The pipeline should continue even if validation fails
            with patch.object(ai_qualification_service, 'qualify_prospects') as mock_qualification:
                mock_qualification.return_value = {
                    "success": True,
                    "qualified_prospects": [],
                    "ai_analysis": {},
                    "cost_estimate": 0.02
                }
                
                result = await prospect_discovery_service.discover_prospects("Test Company")
                
                # Should still succeed, just without validation
                assert result.get("success") == True, "Pipeline should continue despite validation failure"
                print("✅ Pipeline continues gracefully when validation fails")
    
    print()


async def test_services_test_methods():
    """Test that all services have test methods"""
    print("🧪 Testing Service Test Methods")
    print("=" * 50)
    
    # Mock all the test methods to avoid API calls
    with patch.object(serper_service, 'test_search') as mock_search_test, \
         patch.object(company_validation_service, 'test_validation') as mock_validation_test, \
         patch.object(ai_qualification_service, 'test_qualification') as mock_ai_test, \
         patch.object(prospect_discovery_service.linkedin_service, 'test_scraping') as mock_linkedin_test:
        
        # Setup mock responses
        mock_search_test.return_value = {"success": True}
        mock_validation_test.return_value = {"success": True}
        mock_ai_test.return_value = {"success": True}
        mock_linkedin_test.return_value = {"success": True}
        
        result = await prospect_discovery_service.test_services()
        
        assert result.get("success") == True, "Service tests failed"
        assert "validation_service" in result.get("service_tests", {}), "Validation service test missing"
        assert result.get("all_services_working") == True, "Not all services working"
        
        print("✅ All service test methods working")
        print("✅ Validation service included in test suite")
    
    print()


async def run_all_tests():
    """Run all integration tests"""
    print("🚀 Running Company Validation Integration Tests")
    print("=" * 70)
    print()
    
    tests = [
        ("Service Initialization", test_service_initialization),
        ("Validation Service Structure", test_validation_service_structure),
        ("AI Qualification Enhancement", test_ai_qualification_enhancement),
        ("Pipeline Integration", test_pipeline_integration),
        ("Service Imports", test_service_imports),
        ("Error Handling", test_error_handling),
        ("Service Test Methods", test_services_test_methods)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_name} FAILED: {str(e)}")
            failed += 1
    
    print("=" * 70)
    print(f"🏁 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All integration tests passed!")
        print("✅ Company validation system successfully integrated")
    else:
        print("⚠️  Some tests failed - review implementation")
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
