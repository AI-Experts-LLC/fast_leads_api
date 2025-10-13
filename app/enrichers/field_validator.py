#!/usr/bin/env python3
"""
Field Validation Utility for Salesforce Enrichers

Provides comprehensive validation to prevent inserting invalid, N/A, or insufficient data
into Salesforce fields. Used by all enricher scripts to maintain data quality.
"""

import re
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class FieldValidator:
    """Utility class for validating field values before Salesforce insertion."""
    
    # Comprehensive list of invalid response patterns
    INVALID_PATTERNS = [
        # Direct N/A variations
        "n/a", "na", "not applicable", "not available", "not found",
        
        # Insufficient information patterns
        "i don't have", "i don't know", "cannot find", "unable to", 
        "no information", "insufficient information", "insufficient data",
        "limited information", "no data", "no details", "no specific",
        
        # AI uncertainty patterns
        "sorry", "i apologize", "i cannot", "i'm unable", "i'm not able",
        "i don't see", "i couldn't find", "i wasn't able", "i can't find",
        
        # Error indicators
        "error", "failed", "failure", "problem", "issue",
        
        # Empty/null indicators
        "null", "none", "empty", "blank", "missing",
        
        # Unknown/unclear patterns
        "unknown", "unclear", "uncertain", "unsure", "unspecified",
        "undetermined", "undisclosed", "unconfirmed",
        
        # Generic responses
        "general", "various", "multiple", "several", "different",
        "standard", "typical", "common", "regular", "normal",
        
        # Placeholder text
        "to be determined", "tbd", "coming soon", "pending", "under review",
        "in progress", "being developed", "being planned",
        
        # Analysis incomplete indicators
        "analysis incomplete", "research ongoing", "investigation needed",
        "further research required", "more information needed",
        
        # Specific healthcare/business patterns that indicate no real data
        "healthcare professional", "hospital administrator", "facility manager",
        "works in healthcare", "employed at hospital", "member of team",
        
        # Generic location patterns
        "united states", "usa", "north america", "various locations",
        
        # Generic company patterns (but allow if part of longer description)
        "healthcare organization", "medical facility", "hospital system",
        "healthcare provider", "medical center",
        
        # Vague time patterns (only when standalone or at start)
        "recently", "currently", "presently", "at this time", "as of now",
        
        # Financial uncertainty patterns (only when standalone)
        "estimated", "approximately", "around", "roughly",
        "varies", "depends", "subject to change", "market conditions"
    ]
    
    # Patterns that indicate the response is too generic/vague to be useful
    GENERIC_PATTERNS = [
        # Single word responses (but allow longer single words like team names)
        r"^\w{1,8}$",  # Single short word
        
        # Very short responses (less than 8 characters) 
        r"^.{1,7}$",
        
        # Responses that are just punctuation or numbers
        r"^[\d\s\-\.\,\(\)]+$",
        
        # Responses that are just "Yes" or "No" 
        r"^(yes|no)\.?$",
        
        # Generic sentences without specific information (but be more specific)
        r"^(the|this|that|it|they)\s+\w+\s+(is|are|was|were)\s+\w+\.?$"
    ]
    
    @classmethod
    def is_valid_field_value(cls, value: Any, field_name: str = "") -> bool:
        """
        Validate if a field value is acceptable for Salesforce insertion.
        
        Args:
            value: The field value to validate
            field_name: Optional field name for context in logging
            
        Returns:
            True if value is valid and should be inserted, False otherwise
        """
        # Handle None or empty values
        if not value:
            return False
            
        # Convert to string and clean
        str_value = str(value).strip()
        
        # Check minimum length (must be at least 3 characters for meaningful data)
        if len(str_value) < 3:
            logger.debug(f"🔴 Field '{field_name}': Too short ({len(str_value)} chars): '{str_value}'")
            return False
        
        # Check for invalid patterns (case insensitive)
        str_value_lower = str_value.lower()
        
        # Special case: Allow longer meaningful content even if it contains some invalid patterns
        # If the content is substantial (>50 chars) and contains specific information, be more lenient
        if len(str_value) > 50:
            # Check if it contains specific, concrete information
            has_numbers = any(char.isdigit() for char in str_value)
            has_proper_nouns = any(word[0].isupper() for word in str_value.split() if len(word) > 1)
            
            # If it has concrete details, be more lenient with some patterns
            if has_numbers or has_proper_nouns:
                # Only check for the most definitive invalid patterns
                definitive_invalid = [
                    "n/a", "not available", "i don't have", "i don't know", 
                    "cannot find", "unable to", "insufficient information", "no information"
                ]
                for pattern in definitive_invalid:
                    if pattern in str_value_lower:
                        logger.info(f"🔴 Field '{field_name}': Contains definitive invalid pattern '{pattern}': '{str_value[:50]}...'")
                        return False
                # If no definitive invalid patterns, allow it
                logger.debug(f"✅ Field '{field_name}': Long content with concrete details, allowing despite potential minor issues")
                return True
        
        # Check for exact matches or patterns at the beginning/end of responses
        for pattern in cls.INVALID_PATTERNS:
            # For very short patterns, require exact match or at word boundaries
            if len(pattern) <= 4:  # Short patterns like "n/a", "none"
                if (pattern == str_value_lower or 
                    str_value_lower.startswith(pattern + " ") or 
                    str_value_lower.endswith(" " + pattern) or
                    (" " + pattern + " ") in str_value_lower):
                    logger.info(f"🔴 Field '{field_name}': Contains invalid pattern '{pattern}': '{str_value[:50]}...'")
                    return False
            else:
                # For longer patterns, be much more careful about context
                # Skip patterns that are too generic and commonly appear in valid content
                skip_patterns = [
                    "general", "various", "multiple", "several", "different", 
                    "standard", "typical", "common", "regular", "normal",
                    "recently", "currently", "presently", "estimated", "approximately", 
                    "around", "roughly", "varies", "depends"
                ]
                
                # Special handling for subject line fields - be very lenient
                if 'subject' in field_name.lower() or 'campaign' in field_name.lower():
                    # For subject lines, only check for the most definitive invalid patterns
                    definitive_subject_invalid = [
                        "i don't have", "i don't know", "cannot find", "unable to", 
                        "no information", "insufficient information", "not available",
                        "sorry", "i apologize", "i cannot", "error", "failed"
                    ]
                    if pattern in definitive_subject_invalid and pattern in str_value_lower:
                        logger.info(f"🔴 Field '{field_name}': Contains definitive invalid pattern '{pattern}': '{str_value[:50]}...'")
                        return False
                    # Skip other patterns for subject lines
                    continue
                
                if pattern in skip_patterns:
                    # Only reject if the entire response is just this generic word
                    if str_value_lower.strip() == pattern or str_value_lower.strip() in [f"{pattern}.", f"{pattern},"]:
                        logger.info(f"🔴 Field '{field_name}': Contains invalid pattern '{pattern}': '{str_value[:50]}...'")
                        return False
                else:
                    # For other longer patterns, check if it's a definitive failure indicator
                    definitive_failures = [
                        "i don't have", "i don't know", "cannot find", "unable to", 
                        "no information", "insufficient information", "insufficient data",
                        "not available", "sorry", "i apologize", "i cannot", "i'm unable",
                        "error", "failed", "null", "none", "unknown"
                    ]
                    if pattern in definitive_failures and pattern in str_value_lower:
                        logger.info(f"🔴 Field '{field_name}': Contains invalid pattern '{pattern}': '{str_value[:50]}...'")
                        return False
        
        # Check for generic patterns using regex
        for pattern in cls.GENERIC_PATTERNS:
            if re.match(pattern, str_value_lower):
                # Special exception for revenue fields - allow simple dollar amounts like $17.8B, $450M
                if 'revenue' in field_name.lower() and re.match(r'^\$[\d\.,]+[kmb]?$', str_value_lower):
                    logger.debug(f"✅ Field '{field_name}': Valid revenue format: '{str_value}'")
                    continue  # Skip this generic pattern check for valid revenue formats
                logger.info(f"🔴 Field '{field_name}': Matches generic pattern: '{str_value[:50]}...'")
                return False
        
        # Additional checks for specific field types
        if field_name:
            if not cls._validate_field_specific(str_value, field_name):
                return False
        
        # If we get here, the value passed all validation checks
        logger.debug(f"✅ Field '{field_name}': Valid value: '{str_value[:50]}...'")
        return True
    
    @classmethod
    def _validate_field_specific(cls, value: str, field_name: str) -> bool:
        """Apply field-specific validation rules."""
        value_lower = value.lower()
        
        # Email subject line validation
        if 'subject' in field_name.lower():
            # Subject lines are now very permissive - we trust the AI to generate appropriate content
            # Only block if it contains definitive invalid patterns (handled in main validation above)
            # Allow all greetings, questions, observations, and personalized content
            pass  # No additional subject line restrictions
        
        # Sports team validation
        if 'sports' in field_name.lower() or 'team' in field_name.lower():
            # Should contain actual team names, not generic responses
            generic_sports = ["local teams", "area teams", "regional teams", "city teams", "local sports teams"]
            if value_lower in generic_sports:
                logger.info(f"🔴 Field '{field_name}': Generic sports response: '{value[:50]}...'")
                return False
        
        # Financial data validation
        if any(fin_word in field_name.lower() for fin_word in ['wacc', 'debt', 'financial', 'capital']):
            # Financial fields should not be pure speculation without concrete data
            speculation_words = ["might", "could", "possibly", "perhaps", "maybe", "likely"]
            # Only reject if it's mostly speculation without concrete numbers or facts
            speculation_count = sum(1 for spec in speculation_words if spec in value_lower)
            if speculation_count > 0 and not any(char.isdigit() for char in value):
                logger.info(f"🔴 Field '{field_name}': Speculative financial data without concrete info: '{value[:50]}...'")
                return False
        
        return True
    
    @classmethod
    def clean_field_data(cls, field_data: Dict[str, Any], field_mapping: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Clean a dictionary of field data, removing invalid values.
        
        Args:
            field_data: Dictionary of field_key -> value
            field_mapping: Optional mapping of field_key -> salesforce_field for context
            
        Returns:
            Cleaned dictionary with only valid field values
        """
        cleaned_data = {}
        
        for field_key, value in field_data.items():
            # Get field name for logging context
            field_name = field_key
            if field_mapping and field_key in field_mapping:
                field_name = f"{field_key} ({field_mapping[field_key]})"
            
            if cls.is_valid_field_value(value, field_name):
                cleaned_data[field_key] = value
            else:
                logger.info(f"🧹 Filtered out invalid field: {field_name}")
        
        removed_count = len(field_data) - len(cleaned_data)
        if removed_count > 0:
            logger.info(f"🧹 Cleaned field data: Removed {removed_count}/{len(field_data)} invalid fields")
        
        return cleaned_data
    
    @classmethod
    def validate_salesforce_update_data(cls, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Final validation before Salesforce update.
        
        Args:
            update_data: Dictionary of salesforce_field -> value ready for SF update
            
        Returns:
            Cleaned dictionary safe for Salesforce update
        """
        cleaned_data = {}
        
        for sf_field, value in update_data.items():
            if cls.is_valid_field_value(value, sf_field):
                cleaned_data[sf_field] = value
            else:
                logger.warning(f"🛑 BLOCKED Salesforce update for field '{sf_field}': Invalid value")
        
        blocked_count = len(update_data) - len(cleaned_data)
        if blocked_count > 0:
            logger.warning(f"🛑 Blocked {blocked_count}/{len(update_data)} fields from Salesforce update due to invalid data")
        
        return cleaned_data


def validate_field_value(value: Any, field_name: str = "") -> bool:
    """Convenience function for single field validation."""
    return FieldValidator.is_valid_field_value(value, field_name)


def clean_field_data(field_data: Dict[str, Any], field_mapping: Dict[str, str] = None) -> Dict[str, Any]:
    """Convenience function for cleaning field data."""
    return FieldValidator.clean_field_data(field_data, field_mapping)


# Example usage and testing
if __name__ == "__main__":
    # Test cases
    test_cases = [
        ("Valid company description", "Cleveland Clinic is a leading healthcare provider with over 50,000 employees serving patients across Ohio and Florida."),
        ("N/A response", "N/A"),
        ("Insufficient data", "I don't have sufficient information about this company."),
        ("Generic response", "Healthcare organization"),
        ("Valid sports team", "Cleveland Browns, Cleveland Cavaliers"),
        ("Invalid sports team", "Local teams"),
        ("Valid subject line", "Impressive Cleveland Clinic recognition"),
        ("Invalid subject line", "Hello there"),
        ("Valid financial data", "WACC: 8.5% based on recent bond issuances"),
        ("Speculative financial without data", "WACC might be around 8-10% possibly"),
        ("Speculative with concrete data", "Based on recent $50M bond issuance at 4.2% and estimated equity cost of 12%, WACC might be approximately 7.8%"),
        ("Empty string", ""),
        ("None value", None),
        ("Too short", "OK"),
        ("Valid long text", "The hospital completed a $15M HVAC modernization project in 2023, focusing on energy efficiency improvements across three main buildings."),
        ("Long text with N/A", "The hospital has undertaken several infrastructure projects, but I don't have specific information about energy efficiency initiatives."),
        ("Concrete info despite uncertainty", "Cleveland Clinic completed a $25M energy upgrade in 2022, though exact WACC data is not publicly available.")
    ]
    
    print("🧪 Testing Field Validator:")
    print("=" * 60)
    
    for description, test_value in test_cases:
        is_valid = FieldValidator.is_valid_field_value(test_value, "test_field")
        status = "✅ VALID" if is_valid else "❌ INVALID"
        preview = str(test_value)[:50] + "..." if test_value and len(str(test_value)) > 50 else str(test_value)
        print(f"{status} | {description}: '{preview}'")
    
    print("\n" + "=" * 60)
    print("✅ Field Validator testing complete")
