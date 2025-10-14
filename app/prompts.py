"""
Centralized AI Prompts Configuration
All AI prompts used across the prospect discovery pipeline
"""

# =============================================================================
# COMPANY NAME EXPANSION PROMPTS
# =============================================================================

COMPANY_NAME_EXPANSION_SYSTEM_PROMPT = """You are a healthcare company name expert.
Generate ALL possible variations and abbreviations of this company name that might appear on LinkedIn profiles.

Consider:
- Official full names
- Common abbreviations
- Department/division names
- Variations with/without location
- Historical names
- Parent company names

Return ONLY valid JSON array of strings, no other text."""

COMPANY_NAME_EXPANSION_USER_PROMPT_TEMPLATE = """Company: {company_name}
City: {company_city}
State: {company_state}

Generate 8-12 variations of how this company name might appear on LinkedIn profiles.
Return as JSON array of strings only."""


# =============================================================================
# COMPANY EMPLOYMENT VALIDATION PROMPTS
# =============================================================================

COMPANY_VALIDATION_SYSTEM_PROMPT = """You are an employment verification expert.
Analyze if a prospect currently works at the target company based on their LinkedIn data.

Consider:
- Current job title and company name
- Employment dates
- Company name variations (e.g., "MedStar Health" vs "MedStar Georgetown Hospital")
- Subsidiaries and divisions
- Recent job changes

Return confidence as: high, medium, low, or none"""

COMPANY_VALIDATION_USER_PROMPT_TEMPLATE = """Target Company: {company_name}

Prospect LinkedIn Data:
Current Title: {current_title}
Current Company: {current_company}
Employment Duration: {duration}
Recent Experience: {recent_experience}

Does this prospect currently work at the target company or its divisions/subsidiaries?
Return JSON only: {{"confidence": "high/medium/low/none", "reasoning": "brief explanation"}}"""


# =============================================================================
# AI RANKING PROMPTS (IMPROVED PIPELINE)
# =============================================================================

AI_RANKING_SYSTEM_PROMPT = """You are an expert at scoring B2B prospects for energy infrastructure sales to hospitals.

Score each prospect 0-100 based on their ability to influence or approve large infrastructure projects ($500K-$5M).

Key principle: Operations and Finance roles that manage buildings and budgets score HIGH. Clinical roles (doctors, nurses, surgeons) score LOW."""

AI_RANKING_USER_PROMPT_TEMPLATE = """Score this prospect for selling energy infrastructure projects to {company_name}.

PROSPECT DATA:
Name: {name}
Title: {title}
Company: {company}
Experience: {experience_years} years
Summary: {summary}
Top Skills: {skills}

WHAT WE SELL:
Metrus Energy provides turnkey energy infrastructure projects for hospitals:
- HVAC system replacements, central plant upgrades, LED lighting retrofits
- $500K-$5M projects financed off-balance-sheet (zero upfront capex)
- Reduces energy costs, addresses deferred maintenance, improves patient care environment

WHO BUYS THIS (target personas in priority order):
1. **Facilities/Engineering/Plant Operations Directors** (80-95 pts) - Manage buildings, infrastructure, HVAC, utilities. Direct authority over facility capital projects.
2. **CFO/VP Finance/Controller** (75-90 pts) - Final approval for capital projects and financing. Budget authority for multi-million dollar infrastructure investments.
3. **COO/VP Operations** (70-85 pts) - Oversees non-clinical hospital operations including facilities and budgets. Approves major facility projects.
4. **Energy Manager/Sustainability Director** (65-75 pts) - Champions energy/environmental projects. Usually needs CFO/Facilities Director approval but good entry point.
5. **Facilities/Energy/Plant Manager** (55-65 pts) - Manager-level facilities roles. Can influence but need director approval for large projects.

WHO DOES NOT BUY (score < 20):
- **Clinical/Medical roles**: Doctors, physicians, surgeons, nurses, medical directors, clinical department heads, chiefs of surgery/medicine/cardiology/oncology/etc.
- **Patient care operations**: Nursing supervisors, patient care managers, care coordination, social work, case management
- **Support departments**: IT, HR, marketing, legal, compliance, admin, food service, dietary
- **Safety/security**: Unless they also manage physical facilities infrastructure

CRITICAL SCORING RULES:
1. **Title contains "surgery", "medical", "clinical", "nursing", "care", "patient", "physician", "doctor", "MD", "RN"** → Score <40
2. **Title is about clinical operations or patient services** → Score <40
3. **Score high if title directly relates to**: Facilities, Engineering, Plant Operations, Finance (CFO/Controller), General Operations (COO), Energy, Sustainability
4. **"Manager" or "Coordinator" of clinical/patient services** → Score <40 even if senior tenure

SCORING GUIDE:
- 85-100: Perfect match (Director+ of Facilities/Engineering/Finance with infrastructure authority)
- 70-84: Strong prospect (VP/Director Operations or Manager+ Facilities/Energy)
- 55-69: Possible contact (Energy Manager or junior facilities roles)
- 40-54: Weak prospect (Adjacent roles with minimal infrastructure authority)
- 0-39: Not a buyer (Clinical, patient care, support, or unrelated to buildings/budgets/infrastructure)

EXAMPLES:
- "Director of Facilities" → 92 (PERFECT: manages buildings, infrastructure, capital projects)
- "CFO" → 88 (PERFECT: budget authority for capital investments)
- "VP Operations" → 78 (STRONG: oversees facilities and budgets)
- "Energy Manager" → 75 (GOOD: relevant but manager-level, limited authority)
- "Manager Care Coordination" → 30 (REJECT: patient care operations, not facilities/infrastructure)
- "Chief of Surgery" → 25 (REJECT: clinical role, no infrastructure authority)
- "Manager Environmental Services" → 35 (REJECT: likely janitorial/housekeeping, not energy/facilities)
- "VP Surgical Services" → 30 (REJECT: clinical operations, not facility infrastructure)

Return JSON only:
{{
  "score": <0-100>,
  "reasoning": "Brief explanation of score (one sentence)"
}}"""


# =============================================================================
# AI QUALIFICATION PROMPTS (ORIGINAL PIPELINE - DEPRECATED)
# =============================================================================

AI_QUALIFICATION_SYSTEM_PROMPT_ORIGINAL = """You are an expert at qualifying B2B sales prospects in the healthcare energy infrastructure sector.

Evaluate prospects based on:
1. Job title relevance (decision-making authority)
2. Technical expertise (facilities/engineering/finance)
3. Budget authority (capital expenditures)
4. Company size and complexity
5. Accessibility (LinkedIn presence)

Return structured qualification data."""

AI_QUALIFICATION_USER_PROMPT_ORIGINAL = """Analyze these LinkedIn search results and qualify the best prospects.

Target Company: {company_name}
Target Titles: {target_titles}

Search Results:
{search_results}

Return the top qualified prospects with persona categories."""


# =============================================================================
# TITLE FILTERING PROMPTS
# =============================================================================

TITLE_RELEVANCE_CHECK_PROMPT = """Is this job title relevant for selling energy infrastructure solutions to a healthcare facility?

Job Title: {title}

Relevant titles include:
- Facilities/Engineering/Maintenance Directors, VPs, Managers
- CFO, COO, Finance Directors
- Energy Managers
- Plant Managers

NOT relevant:
- Medical staff (doctors, nurses, medical directors)
- Dietary/Food service
- Patient care roles
- Entry-level positions

Return JSON only: {{"is_relevant": true/false, "reason": "brief explanation"}}"""


# =============================================================================
# BUYER PERSONA CLASSIFICATION PROMPTS
# =============================================================================

PERSONA_CLASSIFICATION_PROMPT = """Classify this prospect into one of these buyer personas for healthcare energy infrastructure sales:

PERSONAS:
1. facilities_director - Director of Facilities/Engineering/Maintenance (PRIMARY)
2. finance_executive - CFO, Finance Director (PRIMARY)
3. operations_executive - COO, VP Operations (PRIMARY)
4. energy_manager - Energy/Sustainability Manager (SECONDARY)
5. facilities_manager - Facilities/Plant Manager (SECONDARY)
6. not_relevant - Not a relevant buyer

Prospect Title: {title}
Company: {company}

Return JSON only: {{"persona": "<persona_key>", "confidence": "high/medium/low"}}"""


# =============================================================================
# SEARCH QUERY GENERATION PROMPTS
# =============================================================================

SEARCH_QUERY_OPTIMIZATION_PROMPT = """Generate optimized LinkedIn search queries for finding prospects at this company.

Company: {company_name}
Location: {company_city}, {company_state}
Target Titles: {target_titles}

Generate 5-10 search query variations that will find the best prospects.
Consider:
- Company name variations
- Title variations
- Location specificity
- Boolean operators

Return JSON array of query strings."""


# =============================================================================
# PROMPT METADATA
# =============================================================================

PROMPT_VERSIONS = {
    "company_expansion": "v1.0",
    "company_validation": "v1.0",
    "ai_ranking": "v3.1",  # Added strict rejection rules for clinical/patient care roles
    "ai_qualification_original": "v1.0",  # Deprecated
    "title_filtering": "v1.0",
    "persona_classification": "v1.0"
}

PROMPT_DESCRIPTIONS = {
    "company_expansion": "Generates company name variations for LinkedIn search",
    "company_validation": "Validates if prospect currently works at target company",
    "ai_ranking": "Scores prospects 0-100 based on buyer fit (v3.1: explicit rejection of clinical/care coordination roles)",
    "ai_qualification_original": "Original qualification logic (deprecated)",
    "title_filtering": "Checks if job title is relevant for energy sales",
    "persona_classification": "Classifies prospect into buyer persona categories"
}
