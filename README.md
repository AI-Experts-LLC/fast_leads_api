# 🎯 Metrus Energy - Account Enrichment API

**AI-Powered Prospect Discovery & Lead Enrichment System**

Automated pipeline that discovers, qualifies, and enriches healthcare facility prospects using LinkedIn search, AI qualification, and Salesforce integration.

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/-NvLj4?referralCode=CRJ8FE)

---

## 🚀 **System Overview**

**Three-Step Pipeline** (Production-Ready for Railway):
```
Step 1: Search & Filter → Step 2: Scrape & Validate → Step 3: AI Ranking
30-90s                    15-35s                      5-25s
Total: ~1-2.5 minutes per hospital
```

### **🎯 Core Functionality:**
- **🔍 Prospect Discovery**: Find LinkedIn profiles by company and target job titles
- **✅ Company Validation**: Normalized name matching (St. ↔ Saint, state abbreviations)
- **🧠 AI Qualification**: Score and rank prospects using GPT-4 analysis
- **📊 Profile Enrichment**: Extract detailed LinkedIn data via Apify
- **⚡ Salesforce Integration**: Create qualified leads directly in Salesforce
- **💰 Cost Tracking**: ~$0.40 per hospital (October 2025 update)
- **📈 Success Rate**: 69% (9/13 hospitals, October 2025 production test)

---

## 🧠 **AI Qualification Scoring System**

### **📊 How Qualification Scores Are Calculated (0-100 Scale)**

Our AI uses **OpenAI GPT-4** to analyze each prospect with this precise scoring criteria:

#### **Enhanced Scoring Breakdown (Total: 100 points):**

**1. Job Title Relevance (35% - up to 35 points)** 🎯
- **Director of Facilities/Engineering** → 35-40 points (Primary target)
- **CFO/Financial Leadership** → 30-35 points (Budget authority)
- **Sustainability/Energy Manager** → 25-30 points (Environmental focus)
- **COO/Director of Operations** → 20-25 points (Operational efficiency)
- **Compliance Manager** → 15-20 points (Regulatory requirements)
- **Other titles** → 0-15 points (Not qualified if total <70)

**2. Decision-Making Authority (25% - up to 25 points)** 👑
- **High Authority** → 20-25 points (Can approve capital projects)
- **Medium Authority** → 12-20 points (Influences decisions)
- **Low Authority** → 4-12 points (Limited influence)

**🆕 3. Employment Validation Confidence (20% - up to 20 points)** ✅
- **High Confidence (90-100%)** → 18-20 points + 10 bonus points
- **Medium Confidence (70-89%)** → 12-18 points + 5 bonus points
- **Low Confidence (<70%)** → 0-12 points (no bonus)

**4. Company Size & Budget Likelihood (15% - up to 15 points)** 🏢
- **Large Healthcare Systems** → 12-15 points (Mayo Clinic, Johns Hopkins)
- **Medium Healthcare Facilities** → 8-12 points (Regional hospitals)
- **Small Organizations** → 4-8 points (Limited budgets)

**5. Accessibility & Engagement Potential (5% - up to 5 points)** 📱
- **Active LinkedIn Profile** → 8-10 points (Recent activity, connections)
- **Some LinkedIn Activity** → 5-8 points (Moderate engagement)
- **Inactive Profile** → 2-5 points (Hard to reach)

### **🎯 Target Buyer Personas (Priority Order):**
1. **Director of Facilities/Engineering/Maintenance** - Primary decision makers
2. **CFO/Financial Leadership** - Budget authority for capital projects  
3. **Sustainability Manager/Energy Manager** - Environmental goals
4. **COO/Director of Operations** - Operational efficiency focus
5. **Compliance Manager** - Regulatory requirements

### **✅ Qualification Threshold:**
- **≥70 points** = Qualified prospect (returned in results)
- **<70 points** = Not qualified (filtered out)

### **✅ Company Validation System:**
**Enhanced name matching to handle healthcare facility variations**
- ✅ Normalizes "St." ↔ "Saint" (St. Patrick Hospital = Saint Patrick Hospital)
- 🏢 Removes healthcare suffixes (Medical Center, Hospital, Health System)
- 📍 Strips state abbreviations ("Hospital MT" → "Hospital")
- 🔗 Validates current employment vs. former employees
- 📊 See [Three-Step Pipeline Documentation](THREE_STEP_PIPELINE.md) for details

### **🏆 Example Scoring (Johns Hopkins Hospital):**

| Prospect | Score | Title Relevance | Authority | Company Size | Engagement |
|----------|-------|----------------|-----------|--------------|------------|
| **Michael Drenta, CHFM** | **95** | 40 (Director) | 30 (High) | 20 (Large) | 5 (Moderate) |
| **Lavell Rollins** | **90** | 38 (Director) | 28 (High) | 18 (Large) | 6 (Active) |
| **Doug Coleman, MBA** | **85** | 35 (Former Dir) | 25 (Medium) | 18 (Large) | 7 (Active) |

---

## 📡 **API Endpoints**

### **🎯 Three-Step Prospect Discovery** (Recommended)

**Step 1: Search & Filter**
```bash
POST /discover-prospects-step1
```
Returns qualified LinkedIn URLs after search and title filtering.

**Step 2: Scrape & Validate**
```bash
POST /discover-prospects-step2
```
Scrapes profiles and validates company/employment/location.

**Step 3: AI Ranking**
```bash
POST /discover-prospects-step3
```
AI ranks prospects and returns top qualified (score ≥65).

**Complete Example:**
```json
// Step 1 Request
{
  "company_name": "Mayo Clinic",
  "company_city": "Rochester",
  "company_state": "Minnesota"
}

// Step 3 Final Response
{
  "qualified_prospects": [
    {
      "linkedin_data": {
        "name": "John Smith",
        "job_title": "Director of Facilities",
        "email": "john@mayo.edu",
        "connections": 450
      },
      "ai_ranking": {
        "ranking_score": 92,
        "ranking_reasoning": "Director-level facilities role...",
        "rank_position": 1
      }
    }
  ]
}
```

📚 **Full Documentation**: See [THREE_STEP_PIPELINE.md](THREE_STEP_PIPELINE.md)

### **⚡ Salesforce Integration**
```bash
POST /salesforce/connect    # Test Salesforce authentication
GET  /salesforce/status     # Check connection status
GET  /account/{id}          # Get account details
POST /lead                  # Create new lead
```

### **🧪 Testing & Debug**
```bash
GET  /test-services         # Test all API integrations
GET  /health               # Health check
GET  /debug/environment    # Environment variable check
```

---

## 🛠 **Setup & Installation**

### **1. Clone Repository**
```bash
git clone <repository-url>
cd fast_leads_api
```

### **2. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **3. Environment Configuration**

Create `.env` file:
```bash
# Salesforce Configuration
SALESFORCE_DOMAIN=https://test.salesforce.com
SALESFORCE_USERNAME=your_username
SALESFORCE_PASSWORD=your_password
SALESFORCE_SECURITY_TOKEN=your_token

# Prospect Discovery API Keys (Required)
SERPER_API_KEY=your_serper_key          # Google Search API for LinkedIn
OPENAI_API_KEY=your_openai_key          # AI Qualification & Enrichment
APIFY_API_TOKEN=your_apify_token        # LinkedIn Profile Scraping

# Credit Enrichment (EDF-X) - Optional
EDFX_USERNAME=your_edfx_username        # Company credit ratings
EDFX_PASSWORD=your_edfx_password        # Probability of default data

# API Security (Required for enrichment endpoints)
API_KEY=your-secure-api-key             # Protect /enrich/* endpoints

# Email Validation (Optional)
ZEROBOUNCE_API_KEY=your_zerobounce_key  # Email deliverability validation

# ZoomInfo Integration (Optional, not currently active)
ZOOMINFO_CLIENT_ID=your_client_id       # Contact validation
ZOOMINFO_CLIENT_SECRET=your_secret      # Requires OAuth setup

# Optional Settings
ENVIRONMENT=development
PORT=8000
```

### **4. Run Locally**
```bash
hypercorn main:app --reload
```

### **5. Deploy to Railway**
1. Connect GitHub repository to Railway
2. Add environment variables in Railway dashboard
3. Deploy automatically on git push

---

## 🔑 **Required API Services**

### **Core Services (Required)**

| Service | Purpose | Cost | Setup Link |
|---------|---------|------|------------|
| **Serper** | Google Search for LinkedIn profiles | $50/month (5,000 searches) | [serper.dev](https://serper.dev) |
| **OpenAI** | AI qualification, enrichment & analysis | ~$20-50/month usage | [platform.openai.com](https://platform.openai.com) |
| **Apify** | LinkedIn profile scraping | $49/month + usage | [apify.com](https://apify.com) |
| **Salesforce** | CRM integration | Existing account | Your Salesforce org |

### **Optional Services**

| Service | Purpose | Cost | Setup Link |
|---------|---------|------|------------|
| **EDF-X** | Company credit ratings & PD data | Custom pricing | Contact EDF-X |
| **ZeroBounce** | Email deliverability validation | $16/month (2,000 credits) | [zerobounce.net](https://www.zerobounce.net) |
| **ZoomInfo** | Contact validation & enrichment | Enterprise pricing | [zoominfo.com](https://www.zoominfo.com) |

**Core Services Cost**: ~$120-150/month
**With Optional Services**: ~$150-200+/month

---

## 📊 **Performance Metrics** (October 2025 Production Test)

### **Pipeline Efficiency:**
- **Processing Time**: 50-150 seconds per hospital (~1-2.5 minutes)
- **Success Rate**: 69% (9 of 13 hospitals)
- **Prospects Per Hospital**: 2.6 average for successful hospitals
- **Total Prospects**: 23 qualified from 13 hospitals
- **Cost Per Hospital**: ~$0.40

### **Filtering Effectiveness:**
- **Initial Search Results**: 40-61 profiles per hospital
- **After Title Filter**: 2-17 qualified for scraping
- **After Company Validation**: 1-9 pass employment checks
- **After AI Ranking (≥65)**: 1-6 final qualified prospects

### **Common Failure Modes:**
- **Low Connections** (3 hospitals): All prospects <50 LinkedIn connections
- **Employment Status** (1 hospital): All prospects identified as former employees

---

## 🎯 **Real-World Examples** (October 2025)

### **Saint Alphonsus Regional Medical Center** (Boise, ID)
**Best Performer**: 6 qualified prospects in 130 seconds

**Top 3 Prospects:**
1. **Joel DeBlasio** - Director of Operations (Score: 92)
   - Email: joel.deblasio@saintalphonsus.org
2. **Lannie Checketts** - VP Finance (Score: 88)
3. **Shawn Dammarell** - Director of Finance (Score: 88)

### **Benefis Hospitals Inc** (Great Falls, MT)
**3 qualified prospects in 113 seconds**

**Top Prospect:**
- **Gunnar VanderMars** - Facilities Director (Score: 92)
- 450+ LinkedIn connections, 15+ years experience

---

## 🔧 **Technical Architecture**

```
FastAPI App
├── 🔍 Search Service (Serper)
├── 🧠 AI Qualification (OpenAI)
├── 📊 LinkedIn Scraping (Apify)
├── ⚡ Salesforce Integration
└── 🎯 Prospect Discovery Orchestrator
```

**Built with**: FastAPI, Python 3.9+, async/await, Railway deployment

---

## 📝 **Development Notes**

- **Async Architecture**: All services use async/await for optimal performance
- **Error Handling**: Comprehensive error handling with detailed logging
- **Cost Control**: Configurable limits on search results and profile scraping
- **Security**: Environment-based configuration, no hardcoded credentials
- **Monitoring**: Health checks and service status endpoints

**Ready for production use with healthcare facility prospect discovery!**
