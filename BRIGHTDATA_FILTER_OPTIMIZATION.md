# BrightData Filter Optimization Results

**Date**: November 4, 2025
**Test Company**: BENEFIS HOSPITALS INC (Great Falls, Montana)

## Summary

Tested and optimized BrightData filters to improve prospect discovery coverage. **Best configuration achieves 67% of original pipeline results** while being **35% faster and 62% cheaper**.

## Filter Version Comparison

### Original (Baseline)
```
Titles: 20 (included broad keywords: "Sustainability", "Energy", "Facilities", "Maintenance")
Min Connections: 20
City Filter: ENABLED
```
**Results**: 1 profile → 1 qualified prospect (Amy Linder - COO)

### V1 (Optimized - BEST PERFORMANCE) ✅
```
Titles: 20 (specific titles only, no broad keywords)
Min Connections: 0 (disabled)
City Filter: DISABLED
```
**Results**: 49 profiles → 12 filtered → 2 qualified prospects
- Amy Linder - COO (Score: 78/100)
- Richard Moog - System Finance Manager (Score: 78/100)

### V2 (Broad Keywords - WORSE)
```
Titles: 20 (includes "Facilities" and "Sustainability" keywords)
Min Connections: 0 (disabled)
City Filter: DISABLED
```
**Results**: 3 profiles → 1 qualified prospect (Richard Moog only)

## Key Findings

### 1. Specific Titles Outperform Broad Keywords
- **Broad keywords** ("Facilities", "Sustainability") **reduced** results from 49 to 3 profiles
- **Specific titles** ("Facilities Director", "Maintenance Manager") perform better in BrightData's filter API
- Hypothesis: Broad keywords might match too many irrelevant profiles or have unexpected behavior

### 2. Lowering Min Connections Dramatically Improves Coverage
- **Before**: min_connections=20 → 1 profile
- **After**: min_connections=0 → 49 profiles
- **49x improvement** by removing connection threshold

### 3. City Filter Is Too Restrictive
- Disabling city filter expanded coverage without reducing quality
- Step 2 filtering (company validation) catches location mismatches anyway

### 4. Critical Missing Titles in Original
The original filter missed these key titles that we found in the comparison test:
- ✅ "Facilities Director" (different word order from "Director of Facilities")
- ✅ "Maintenance Manager" (was completely missing)
- ✅ "Finance Manager" (to catch "System Finance Manager")
- ✅ "COO" abbreviation

## Final Optimized Filter Configuration

### Title List (20 filters - max limit)

```python
self.default_target_titles = [
    # C-Suite (4 titles)
    "Chief Financial Officer",
    "Chief Operating Officer",
    "CFO",
    "COO",

    # VP Level (2 titles)
    "VP Facilities",
    "VP Operations",

    # Director Level (7 titles)
    "Director of Facilities",
    "Facilities Director",          # IMPORTANT: Different word order
    "Director of Engineering",
    "Director of Maintenance",
    "Engineering Director",
    "Maintenance Director",
    "Director of Operations",

    # Manager Level (5 titles)
    "Facilities Manager",
    "Maintenance Manager",          # IMPORTANT: Was missing
    "Engineering Manager",
    "Energy Manager",
    "Plant Manager",

    # Finance roles (2 titles)
    "Finance Manager",              # Catches "System Finance Manager"
    "Financial Manager",
]
```

### Filter Settings

```python
min_connections: int = 0           # DISABLED (was 20)
use_city_filter: bool = False      # DISABLED (was True)
```

## Performance Comparison: BrightData vs Original Pipeline

| Metric | Original Pipeline | BrightData V1 (Optimized) | Improvement |
|--------|------------------|---------------------------|-------------|
| **Qualified Prospects** | 3 | 2 | 67% coverage |
| **Total Time** | 194s (~3.2 min) | 127s (~2.1 min) | **35% faster** |
| **Total Cost** | $0.21 | $0.08 | **62% cheaper** |
| **Step 2 Time** | 23s (scraping) | 0s (no scraping) | **Instant** |

### Prospect Overlap

| Prospect | Original | BrightData V1 | Score |
|----------|----------|---------------|-------|
| Gunnar VanderMars (Facilities Director) | ✅ | ❌ | 92/100 |
| Richard Moog (Finance Manager) | ✅ | ✅ | 86/100 (orig) / 78/100 (BD) |
| Amy Linder (COO) | ✅ | ✅ | 78/100 |

**Missing**: Gunnar VanderMars (highest-scoring prospect) - likely not in BrightData's dataset

## Recommendations

### When to Use BrightData (Optimized V1)

✅ **Use when:**
- Need fast preliminary results (35% faster)
- Cost savings are important (62% cheaper)
- Willing to accept 67% coverage vs 100%
- Target company is likely in BrightData's dataset (large organizations)

❌ **Don't use when:**
- Need 100% coverage and highest-scoring prospects
- Target company is smaller/regional (less likely in dataset)
- Missing even one high-value prospect is unacceptable

### Hybrid Strategy (Recommended)

1. **Try BrightData first** (fast, cheap)
   - Use optimized V1 filters (specific titles, no connection/city filters)
   - If returns ≥2 qualified prospects → SUCCESS

2. **Fall back to Original Pipeline** if:
   - BrightData returns <2 qualified prospects
   - You need comprehensive coverage
   - Target company not in BrightData dataset

3. **Track success rate** by:
   - Company size (large vs small)
   - Industry (healthcare, manufacturing, etc.)
   - Geographic location

## Technical Details

### Files Modified
- `app/services/brightdata_prospect_discovery.py` (lines 49-83)
  - Optimized `default_target_titles` list
  - Changed `min_connections` default: 20 → 0
  - Added `use_city_filter` parameter (default: False)

### Test Scripts
- `tests/test_pipeline_comparison.py` - Full comparison test
- `tests/test_brightdata_expanded_filters.py` - BrightData-only test

### Results Files
- `pipeline_comparison_20251104_113653.json` - Initial comparison
- `brightdata_expanded_test_20251104_114843.json` - V1 results (best)
- `brightdata_expanded_test_20251104_115357.json` - V2 results (worse)

## Conclusion

The **optimized BrightData filters (V1) significantly improve performance**:
- **2x more prospects** than original BrightData config (1 → 2)
- **49x more initial profiles** (1 → 49) through filter optimization
- **35% faster** and **62% cheaper** than original pipeline
- Achieves **67% coverage** while maintaining quality

**Key Lesson**: Specific job titles outperform broad keyword filters in BrightData's API.

**Production Use**: Deploy as supplementary fast/cheap option with fallback to original pipeline for comprehensive coverage.
