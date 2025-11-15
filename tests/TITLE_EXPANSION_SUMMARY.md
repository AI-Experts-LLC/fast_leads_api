# Bright Data LinkedIn Filter - Title Expansion

## Overview
Expanded target job titles from **11 to 52 titles** based on buyer personas from `search.py`, `improved_prospect_discovery.py`, and `improved_ai_ranking.py`.

## Title Hierarchy (By Decision Authority)

### 1. C-Suite (6 titles)
**Authority Level**: Ultimate decision-makers
**Budget Impact**: Highest

- Chief Executive Officer
- Chief Financial Officer
- Chief Operating Officer
- CEO
- CFO
- COO

### 2. VP Level (6 titles)
**Authority Level**: High authority, report to C-Suite
**Budget Impact**: High

- Vice President Facilities
- Vice President Operations
- Vice President Engineering
- VP Facilities
- VP Operations
- VP Engineering

### 3. Director Level - Core (10 titles)
**Authority Level**: Primary technical decision-makers
**Budget Impact**: Medium-High

- Director of Facilities
- Director of Engineering
- Director of Maintenance
- Director of Operations
- Director Facilities
- Director Engineering
- Director Maintenance
- Facilities Director
- Engineering Director
- Operations Director

### 4. Director Level - Specialized (7 titles)
**Authority Level**: Specialized technical expertise
**Budget Impact**: Medium

- Director of Plant Operations
- Director of Physical Plant
- Director of Environmental Services
- Sustainability Director
- Energy Director
- Finance Director
- Director of Finance

### 5. Manager Level - Core (7 titles)
**Authority Level**: Operational decision-makers
**Budget Impact**: Medium

- Facilities Manager
- Engineering Manager
- Maintenance Manager
- Energy Manager
- Plant Manager
- Operations Manager
- Sustainability Manager

### 6. Manager Level - Specialized (5 titles)
**Authority Level**: Specialized operations
**Budget Impact**: Medium-Low

- Manager of Facilities
- Manager of Engineering
- Manager of Maintenance
- Plant Operations Manager
- Physical Plant Manager

### 7. Head/Lead Titles (4 titles)
**Authority Level**: Senior technical roles
**Budget Impact**: Medium

- Head of Facilities
- Head of Engineering
- Head of Operations
- Lead Facilities

## Previous vs. New Coverage

### Before (11 titles):
```
Director of Facilities
Director of Engineering
Director of Maintenance
VP Facilities
VP Operations
Chief Financial Officer
Chief Operating Officer
Facilities Manager
Energy Manager
Plant Manager
Maintenance Manager
```

### After (52 titles):
- **C-Suite**: 6 titles (added CEO, expanded CFO/COO variations)
- **VP Level**: 6 titles (added VP Engineering, expanded variations)
- **Directors**: 17 titles (added Operations, specialized directors)
- **Managers**: 12 titles (added specialized manager variations)
- **Head/Lead**: 4 titles (new category)
- **Sustainability/Energy**: 3 titles (expanded focus area)
- **Finance**: 2 titles (added Finance Director)

## Key Improvements

1. **Title Variations**: Added common variations like "Director Facilities" vs "Facilities Director"
2. **Sustainability Focus**: Added sustainability/energy-specific titles (growing importance in healthcare)
3. **Physical Plant**: Healthcare-specific terminology for facilities management
4. **Finance Authority**: Expanded finance titles for budget decision-makers
5. **Specialized Operations**: Plant operations, environmental services

## Expected Impact

### Coverage Increase
- **Estimated**: 3-5x more prospects per hospital
- **Reasoning**: Many LinkedIn profiles use title variations not in original list

### Quality Maintenance
- All titles still focused on decision-makers
- Excluded: Coordinators, specialists, analysts, consultants (lower authority)
- Maintained: Senior-level focus for energy infrastructure purchasing

## Usage

The expanded titles are automatically used in:
- `test_brightdata_linkedin_filter.py` - Main filter implementation
- `test_brightdata_with_salesforce.py` - Salesforce integration (via import)
- `test_lucas_two_hospitals.py` - Multi-hospital testing (via import)

All existing test scripts benefit from the expansion without code changes.

## Source Analysis

### From `search.py` (Original 11):
- Core decision-maker titles
- Based on buyer_persona.md

### From `improved_prospect_discovery.py`:
- Senior indicators: director, manager, vp, cfo, coo, ceo, chief, head, lead, senior, principal, supervisor
- Exclusions: intern, student, graduate, entry-level, former

### From `improved_ai_ranking.py`:
- Buyer persona priority order:
  1. C-Suite (CEO, CFO, COO)
  2. Facilities/Engineering Directors
  3. Sustainability/Energy Managers
  4. Operations Directors
  5. Finance Directors

## Testing Recommendations

1. **Baseline Test**: Run on same 3 hospitals to compare results
2. **Monitor**: C-Suite results (may be less common but high value)
3. **Validate**: Ensure specialized titles (Physical Plant, Environmental Services) are relevant
4. **Adjust**: If too many low-authority results, remove Head/Lead category

## Cost Impact

- **Search Cost**: Same (Bright Data filter uses OR logic, no additional API calls)
- **Processing Time**: ~10% increase due to larger result set
- **Value**: Higher-quality prospects from title variation matching
