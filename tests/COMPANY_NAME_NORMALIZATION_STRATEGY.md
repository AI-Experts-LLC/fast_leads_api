# Company Name Normalization Strategy

## Problem

When searching LinkedIn profiles by company name, we face two challenges:

1. **Too Specific**: Exact matches miss valid variations
   - "Portneuf Medical Center" won't match "Portneuf Health Trust"

2. **Too Broad**: Removing all suffixes causes false positives
   - "Portneuf" would match "Portneuf Bakery", "Portneuf Auto Repair"

## Solution: Healthcare Identifier Strategy

**Keep healthcare-specific words** that distinguish healthcare facilities from other businesses:
- ✅ **Medical** - "Portneuf Medical" won't match "Portneuf Bakery"
- ✅ **Health/Healthcare** - "Logan Health" won't match "Logan Law Firm"
- ✅ **Clinic** - "Billings Clinic" won't match "Billings Accounting"

**Remove generic organizational suffixes** that don't add filtering value:
- Hospital, Center, Inc, LLC, Regional, System, Trust, etc.

## Implementation

```python
def normalize_company_name(self, company_name: str) -> str:
    """
    Strategy:
    - KEEP: Medical, Health, Healthcare, Clinic (healthcare identifiers)
    - REMOVE: Hospital, Center, Inc, LLC, Regional, etc. (generic suffixes)
    """
```

### Suffixes Removed

**Facility Types:**
- Hospital/Hospitals
- RMC (Regional Medical Center)
- Center

**Corporate Structures:**
- Inc, LLC, Corp, Corporation
- Company, Co.

**Organizational:**
- System/Systems
- Network
- Foundation
- Trust
- Group
- Associates
- Partners

**Descriptors:**
- Regional
- Service/Services
- Care (unless part of "Healthcare")

## Examples

### Portneuf Medical Center

**Original:** "Portneuf Medical Center"
**Normalized:** "Portneuf Medical"

**Filter searches for:**
1. "Portneuf Medical Center" (original)
2. "Portneuf Medical" (normalized)
3. "Portneuf Medical Center Pocatello" (original + city)
4. "Portneuf Medical Pocatello" (normalized + city)

**✅ Matches:**
- Portneuf Medical Center
- Portneuf Medical
- Portneuf Health Trust ✓ (contains "Health")
- Portneuf Healthcare ✓ (contains "Healthcare")

**🛡️ Avoids False Positives:**
- ✗ Portneuf Bakery (no healthcare identifier)
- ✗ Portneuf Veterinary Clinic (no "Medical" or "Health")
- ✗ Portneuf Auto Repair (no healthcare identifier)

### Billings Clinic Hospital

**Original:** "Billings Clinic Hospital"
**Normalized:** "Billings Clinic"

**✅ Matches:**
- Billings Clinic Hospital
- Billings Clinic
- Billings Clinic Medical Group
- Billings Healthcare

**🛡️ Avoids False Positives:**
- ✗ Billings Law Firm
- ✗ Billings Accounting
- ✗ Billings Restaurant Group

### Logan Health Medical Center

**Original:** "Logan Health Medical Center"
**Normalized:** "Logan Health Medical"

**✅ Matches:**
- Logan Health Medical Center
- Logan Health Medical
- Logan Health
- Logan Healthcare

**🛡️ Avoids False Positives:**
- ✗ Logan Pharmacy (no "Medical" or "Health")
- ✗ Logan Dental Care (no "Medical" or "Health")
- ✗ Logan Physical Therapy (no "Medical" or "Health")

## Results on Test Dataset

Testing on 13 hospitals from HospitalAccountsAndIDs.csv:

| Original | Normalized | Healthcare Identifier Kept |
|----------|------------|---------------------------|
| Benefis Hospitals Inc | Benefis | None (unique name) |
| Billings Clinic Hospital | Billings Clinic | ✓ Clinic |
| Bozeman Health Deaconess Regional Medical Center | Bozeman Health Deaconess Medical | ✓ Health, Medical |
| Community Medical Center | Community Medical | ✓ Medical |
| Logan Health Medical Center | Logan Health Medical | ✓ Health, Medical |
| Portneuf Medical Center | Portneuf Medical | ✓ Medical |
| Saint Alphonsus Regional Medical Center | Saint Alphonsus Medical | ✓ Medical |
| St. Joseph Regional Medical Center | St. Joseph Medical | ✓ Medical |
| St. Luke's Magic Valley RMC | St. Luke's Magic Valley | None (unique name) |
| St. Luke's Regional Medical Center | St. Luke's Medical | ✓ Medical |
| St. Patrick Hospital | St. Patrick | None (unique name) |
| St. Vincent Healthcare | St. Vincent Healthcare | ✓ Healthcare |
| West Valley Medical Center | West Valley Medical | ✓ Medical |

## Benefits

1. **Wider Match Coverage**: Catches company name variations on LinkedIn
2. **Maintains Precision**: Healthcare identifiers prevent false positives
3. **Flexible Matching**: Handles different naming conventions
4. **Scalable**: Works across different healthcare organizations

## Trade-offs

**Potential Under-Matching:**
- Very unique names like "Benefis" or "St. Patrick" might still need original form
- Solution: We search BOTH original and normalized forms

**Potential Over-Matching:**
- "Community Medical" is still fairly generic
- Mitigated by: Other filters (location, job titles) narrow results

## Integration with Bright Data Filter

Each company search now includes up to **8 variations**:

For "Portneuf Medical Center" in Pocatello:
1. Portneuf Medical Center (original)
2. Portneuf Medical (normalized)
3. Portneuf Medical Center Pocatello (original + city)
4. Portneuf Medical Pocatello (normalized + city)

If parent account exists (e.g., "Portneuf Health Trust"):
5. Portneuf Health Trust (parent original)
6. Portneuf Health (parent normalized)
7. Portneuf Health Trust Pocatello (parent + city)
8. Portneuf Health Pocatello (parent normalized + city)

All variations use OR logic - matching ANY variation returns the profile.

## Testing

Run normalization tests:
```bash
# Show normalization on all hospitals
python tests/test_company_normalization.py

# Show healthcare identifier strategy with examples
python tests/test_normalization_comparison.py

# Test actual Bright Data search with 3 hospitals
python tests/test_brightdata_three_hospitals.py
```

## Future Enhancements

1. **Add common abbreviations**: BHSF for "Baptist Health South Florida"
2. **Handle "&" variations**: "Providence Health & Services" vs "Providence Health and Services"
3. **State-based variations**: "Mayo Clinic Minnesota", "Baptist Health Florida"
4. **Fuzzy matching**: Handle typos and spelling variations
