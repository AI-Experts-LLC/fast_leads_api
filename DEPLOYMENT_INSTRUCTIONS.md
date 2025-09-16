# 🚀 LinkedIn Testing Deployment Instructions

## Current Status
✅ **API is running and accessible** at https://fast-leads-api.up.railway.app/  
✅ **LinkedIn endpoints added** to main.py  
⚠️ **Deployment needed** to make new LinkedIn endpoints available  

## LinkedIn Test Profiles Ready
- `https://www.linkedin.com/in/lucaserb/` (Lucas Erb)
- `https://www.linkedin.com/in/emollick/` (Ethan Mollick)

---

## 🔧 Quick Deployment Steps

### Option 1: Railway Auto-Deploy (Recommended)
```bash
# If your Railway app is connected to this GitHub repo:
git add .
git commit -m "Add LinkedIn scraping endpoints for direct profile testing"
git push origin main
# Railway will auto-deploy the changes
```

### Option 2: Manual Railway Deploy
1. Go to your Railway dashboard
2. Find the fast-leads-api project
3. Click "Deploy" to trigger manual deployment
4. Wait for deployment to complete (~2-3 minutes)

---

## 🧪 Testing After Deployment

### Test the new LinkedIn endpoints:
```bash
# Test 1: LinkedIn service status
curl https://fast-leads-api.up.railway.app/linkedin/test

# Test 2: Scrape specific profiles
curl -X POST https://fast-leads-api.up.railway.app/linkedin/scrape-profiles \
  -H "Content-Type: application/json" \
  -d '{
    "linkedin_urls": [
      "https://www.linkedin.com/in/lucaserb/",
      "https://www.linkedin.com/in/emollick/"
    ],
    "include_detailed_data": true
  }'
```

### Or run the test script:
```bash
python test_linkedin_scraping.py
```

---

## 🔑 Required Environment Variables

Make sure these are set in Railway:

| Variable | Status | Required For |
|----------|--------|--------------|
| `APIFY_API_TOKEN` | ⚠️ **CRITICAL** | LinkedIn scraping |
| `SERPER_API_KEY` | ✅ Recommended | Google search |
| `OPENAI_API_KEY` | ✅ Recommended | AI qualification |
| `SALESFORCE_USERNAME` | ✅ Set | Salesforce integration |
| `EDFX_USERNAME` | ✅ Set | Credit enrichment |

### To add APIFY_API_TOKEN:
1. Get token from [apify.com](https://apify.com) → Settings → API tokens
2. In Railway: Project → Variables → Add `APIFY_API_TOKEN`
3. Redeploy after adding

---

## 📊 Expected Test Results

### ✅ Success Response:
```json
{
  "status": "success",
  "message": "LinkedIn profiles scraped successfully",
  "data": {
    "success": true,
    "profiles_requested": 2,
    "profiles_scraped": 2,
    "profiles": [
      {
        "url": "https://www.linkedin.com/in/lucaserb/",
        "name": "Lucas Erb",
        "headline": "Professional headline",
        "company": "Current company",
        "location": "Location",
        "experience": [...],
        "education": [...],
        "skills": [...]
      },
      {
        "url": "https://www.linkedin.com/in/emollick/",
        "name": "Ethan Mollick",
        "headline": "Professional headline",
        "company": "Current company",
        "location": "Location",
        "experience": [...],
        "education": [...],
        "skills": [...]
      }
    ],
    "cost_estimate": 0.30
  }
}
```

### ❌ Common Error Responses:
```json
// Missing API token
{
  "status": "error",
  "detail": "LinkedIn scraping failed: Apify client not configured - missing API token"
}

// Invalid URLs
{
  "status": "error", 
  "detail": "linkedin_urls is required"
}
```

---

## 🎯 After Successful Test

Once LinkedIn scraping works, you can:

1. **Use for lead discovery**: 
   ```bash
   POST /discover-prospects
   {
     "company_name": "Target Company",
     "target_titles": ["Director", "CFO"]
   }
   ```

2. **Direct profile analysis**:
   - Extract detailed work history
   - Identify decision-making authority
   - Get contact information (if available)

3. **AI qualification scoring**:
   - Score prospects 0-100
   - Identify best outreach targets
   - Generate personalized messaging

---

## 🚨 Troubleshooting

### If LinkedIn scraping fails:
1. **Check APIFY_API_TOKEN** in Railway environment
2. **Verify Apify account** has sufficient credits
3. **Test with single profile** first
4. **Check Apify actor status** at console.apify.com

### If prospect discovery returns 0 results:
1. Try different company names
2. Check if Google search (Serper) is working
3. Verify target titles are realistic
4. Look at service logs in Railway

---

## 📝 Files Updated
- ✅ `main.py` - Added LinkedIn endpoints
- ✅ `test_linkedin_scraping.py` - Comprehensive test script
- ✅ `test_existing_linkedin.py` - Current API test
- ✅ This deployment guide

**Ready for deployment! 🚀**
