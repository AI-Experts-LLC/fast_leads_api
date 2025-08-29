# Environment Variables Setup Guide

## 🔧 Where Environment Variables Go

### **Local Development (.env file)**

Create a `.env` file in the `/fast_leads_api/` directory with these variables:

```bash
# =============================================================================
# APPLICATION SETTINGS
# =============================================================================
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key-here-generate-a-strong-one

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/metrus_leads

# =============================================================================
# REDIS CONFIGURATION
# =============================================================================
REDIS_URL=redis://localhost:6379/0

# =============================================================================
# SALESFORCE INTEGRATION
# =============================================================================
SALESFORCE_DOMAIN=https://yourcompany.my.salesforce.com
SALESFORCE_CLIENT_ID=your_connected_app_client_id
SALESFORCE_CLIENT_SECRET=your_connected_app_client_secret
SALESFORCE_USERNAME=your_salesforce_username
SALESFORCE_PASSWORD=your_salesforce_password
SALESFORCE_SECURITY_TOKEN=your_security_token

# =============================================================================
# EXTERNAL API SERVICES
# =============================================================================
APIFY_API_TOKEN=apify_api_xxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
HUNTER_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GOOGLE_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GOOGLE_CSE_ID=xxxxxxxxxxxxxxxxxx
MOODYS_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
MOODYS_API_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# =============================================================================
# RATE LIMITING & COSTS
# =============================================================================
DAILY_API_BUDGET=50.00
MAX_ACCOUNTS_PER_DAY=100
MAX_PROSPECTS_PER_ACCOUNT=10
```

### **Railway Deployment (Environment Variables Tab)**

In Railway, go to your project → Variables tab and add:

```
APP_ENV=production
DEBUG=false
SECRET_KEY=generate-a-secure-production-key
SALESFORCE_DOMAIN=https://yourcompany.my.salesforce.com
SALESFORCE_CLIENT_ID=your_production_client_id
SALESFORCE_CLIENT_SECRET=your_production_client_secret
SALESFORCE_USERNAME=your_production_username
SALESFORCE_PASSWORD=your_production_password
SALESFORCE_SECURITY_TOKEN=your_production_token
APIFY_API_TOKEN=your_apify_token
OPENAI_API_KEY=your_openai_key
HUNTER_API_KEY=your_hunter_key
GOOGLE_API_KEY=your_google_key
GOOGLE_CSE_ID=your_google_cse_id
```

## 🔑 How to Get API Keys

### **1. Salesforce Setup**
```bash
# 1. Create Connected App in Salesforce
# Setup → App Manager → New Connected App
# - Enable OAuth Settings
# - Add scopes: Full access, Perform requests at any time
# - Set callback URL: https://your-domain.railway.app/auth/callback

# 2. Get your security token
# Personal Settings → My Personal Information → Reset My Security Token
```

### **2. Apify (LinkedIn Scraping)**
```bash
# 1. Sign up at https://apify.com
# 2. Go to Account → Integrations
# 3. Copy your API token
# Cost: ~$0.10 per LinkedIn profile
```

### **3. OpenAI (AI Messages)**
```bash
# 1. Sign up at https://platform.openai.com
# 2. Go to API Keys
# 3. Create new secret key
# Cost: ~$0.01 per message generated
```

### **4. Hunter.io (Email Discovery)**
```bash
# 1. Sign up at https://hunter.io
# 2. Go to API → API Keys
# 3. Copy your API key
# Cost: ~$0.05 per email found
```

### **5. Google Search API (LinkedIn Discovery)**
```bash
# 1. Go to https://console.developers.google.com
# 2. Create project → Enable Custom Search API
# 3. Create credentials → API Key
# 4. Set up Custom Search Engine
# Cost: $5 per 1000 searches
```

## 🚀 Setup Instructions

### **Step 1: Create Local .env File**
```bash
cd /Users/lucaserb/Documents/MetrusEnergy/fast_leads_api
cp ENVIRONMENT_SETUP.md .env
# Edit .env with your actual values
```

### **Step 2: Set up Local Infrastructure**
```bash
# Install and start Redis
brew install redis
brew services start redis

# Install and start PostgreSQL
brew install postgresql
brew services start postgresql
createdb metrus_leads
```

### **Step 3: Test Configuration**
```bash
python3 -c "from app.core.config import get_settings; print('✅ Config loaded:', get_settings().app_name)"
```

### **Step 4: Railway Deployment**
1. Push code to GitHub
2. Connect Railway to your GitHub repo
3. Add environment variables in Railway dashboard
4. Deploy!

## 🔒 Security Best Practices

### **Environment Variable Security:**
- ✅ Never commit `.env` files to git
- ✅ Use different API keys for dev/prod
- ✅ Rotate keys regularly
- ✅ Use Railway's encrypted environment variables
- ✅ Set up proper Salesforce IP restrictions

### **API Rate Limiting:**
- ✅ Set daily budget limits
- ✅ Monitor API usage costs
- ✅ Implement exponential backoff
- ✅ Cache responses when possible

## 🔍 Troubleshooting

### **Common Issues:**

1. **"ModuleNotFoundError"** → Make sure you're in the virtual environment
2. **"Redis connection refused"** → Start Redis: `brew services start redis`
3. **"Database connection failed"** → Check DATABASE_URL format
4. **"Salesforce auth failed"** → Verify username/password/token
5. **"API key invalid"** → Check key format and permissions

### **Testing Your Setup:**
```bash
# Test all environment variables are loaded
python3 -c "from app.core.config import get_settings; s=get_settings(); print('✅' if s.openai_api_key else '❌', 'OpenAI')"

# Test database connection
python3 -c "from app.models.database import test_connection; import asyncio; asyncio.run(test_connection())"

# Test Redis connection
python3 -c "from app.services.queue import QueueService; q=QueueService(); print('✅ Redis working')"
```

## 💡 Pro Tips

1. **Start with free tiers** of all APIs to test
2. **Use Railway's PostgreSQL** and **Redis** add-ons for production
3. **Set up monitoring** to track API costs
4. **Test with small batches** before going live
5. **Keep backup API keys** in case of issues

This setup will give you a fully functional system ready for production! 🚀
