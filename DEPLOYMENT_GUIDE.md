# Deployment Guide - Metrus Account Enrichment System

## 🎉 System Status: READY FOR DEPLOYMENT

The account enrichment system is **fully implemented** and ready for production deployment. All core functionality is working and tested.

---

## 🚀 Quick Deployment to Railway

### Step 1: Environment Variables Setup

Add these environment variables in Railway dashboard:

```env
# Database (Railway will provide PostgreSQL)
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db

# Redis (Railway will provide Redis)  
REDIS_URL=redis://user:pass@host:port

# Salesforce Configuration
SALESFORCE_DOMAIN=https://your-org.salesforce.com
SALESFORCE_USERNAME=your_salesforce_username
SALESFORCE_PASSWORD=your_salesforce_password
SALESFORCE_SECURITY_TOKEN=your_security_token

# External API Keys
APIFY_API_TOKEN=your_apify_api_token
HUNTER_API_KEY=your_hunter_io_api_key
GOOGLE_API_KEY=your_google_api_key
GOOGLE_SEARCH_ENGINE_ID=your_custom_search_engine_id
OPENAI_API_KEY=your_openai_api_key

# Application Settings
APP_ENV=production
DEBUG=false
SECRET_KEY=your_secret_key_change_me
```

### Step 2: Railway Services Setup

1. **PostgreSQL Database**:
   ```bash
   railway add postgresql
   ```

2. **Redis Service**:
   ```bash
   railway add redis
   ```

3. **Deploy Application**:
   ```bash
   git add .
   git commit -m "Production deployment"
   git push origin main
   ```

### Step 3: Verify Deployment

1. Check application health:
   ```bash
   curl https://your-railway-url.railway.app/health
   ```

2. Test webhook endpoint:
   ```bash
   curl -X POST https://your-railway-url.railway.app/webhook/salesforce-account \
        -H "Content-Type: application/json" \
        -d '{"Id":"test","Name":"Test Hospital"}'
   ```

---

## 🏥 Salesforce Configuration

### Step 1: Create Connected App

1. **Setup > App Manager > New Connected App**
2. **Enable OAuth Settings**: ✓
3. **Callback URL**: `https://your-railway-url.railway.app/oauth/callback`
4. **OAuth Scopes**:
   - Access and manage your data (api)
   - Perform requests on your behalf at any time (refresh_token)

### Step 2: Custom Fields

Add these custom fields to Account object:

```sql
-- Account Object Fields
Enrichment_Status__c (Picklist): Not Enriched, Queued, Processing, Complete, Failed
Last_Enrichment_Date__c (DateTime)
Enrichment_Job_ID__c (Text 50)
Total_Prospects_Found__c (Number)
Qualified_Leads_Created__c (Number)
Credit_Rating__c (Picklist): AAA, AA, A, BBB, BB, B, CCC, CC, C, D
Hospital_Type__c (Picklist): General Acute Care, Critical Access, Specialty
Hospital_Bed_Count__c (Number)
```

Add these custom fields to Lead object:

```sql  
-- Lead Object Fields
LinkedIn_Profile_URL__c (URL)
Persona_Type__c (Picklist): Director of Facilities, CFO, Sustainability Manager
Persona_Match_Score__c (Percent)
AI_Qualification_Score__c (Percent)
AI_Generated_Message__c (Long Text Area)
Source_Enrichment_Job__c (Text 50)
Email_Verification_Status__c (Picklist): Verified, Unverified, Invalid
```

### Step 3: Workflow Rule

Create workflow rule to trigger enrichment:

```sql
-- Workflow Rule: Trigger_Account_Enrichment
Object: Account
Criteria: 
  - Enrichment_Status__c = "Not Enriched"
  - Industry = "Healthcare" OR Hospital_Type__c != ""
  - AnnualRevenue >= 10,000,000

Actions:
  - Update Field: Enrichment_Status__c = "Queued for Enrichment"
  - Outbound Message to: https://your-railway-url.railway.app/webhook/salesforce-account
```

---

## 🔑 External API Setup

### 1. Apify (LinkedIn Scraping)
- Sign up at https://apify.com
- Get API token from Settings > Integrations
- Cost: ~$50-125/month for 100-500 profiles

### 2. Hunter.io (Email Discovery)
- Sign up at https://hunter.io
- Get API key from dashboard
- Start with Starter plan: $49/month for 1,000 searches

### 3. Google Search API (LinkedIn Discovery)
- Create project in Google Cloud Console
- Enable Custom Search API
- Create Custom Search Engine
- Cost: $5 per 1,000 queries

### 4. OpenAI (AI Qualification)
- Sign up at https://openai.com
- Get API key from dashboard
- Cost: ~$0.06 per 1K tokens (~$100-200/month)

### 5. Moody's CreditView (Optional)
- Enterprise licensing required
- Contact Moody's for pricing (~$500-2000/month)

---

## 🔧 Infrastructure Monitoring

### Health Checks

1. **Application Health**:
   ```bash
   curl https://your-app.railway.app/health
   ```

2. **Webhook Health**:
   ```bash
   curl https://your-app.railway.app/webhook/health
   ```

3. **Queue Statistics**:
   ```bash
   curl https://your-app.railway.app/webhook/queue/stats
   ```

### Log Monitoring

Railway provides automatic log aggregation. Monitor for:

- **Error Patterns**: API failures, authentication issues
- **Performance**: Response times, queue processing times  
- **Cost Tracking**: API usage and spending
- **Success Rates**: Lead creation success percentage

---

## 📊 Performance Optimization

### Scaling Configuration

**Railway Environment Variables**:
```env
# Performance Tuning
MAX_CONCURRENT_JOBS=5
DAILY_API_BUDGET=100.00
APIFY_DAILY_LIMIT=100
HUNTER_DAILY_LIMIT=500

# Production Settings
HYPERCORN_WORKERS=2
HYPERCORN_WORKER_CONNECTIONS=1000
```

### RQ Worker Scaling

For high-volume processing, add RQ worker service:

```dockerfile
# worker.Dockerfile
FROM python:3.9
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-c", "from app.services.queue import start_worker; start_worker()"]
```

---

## 🧪 Testing Production

### 1. Basic Functionality Test

```python
import requests

# Test root endpoint
response = requests.get("https://your-app.railway.app/")
print("Status:", response.status_code)
print("Response:", response.json())

# Test webhook with mock data
mock_account = {
    "Id": "001XX000003DHP0YAO",
    "Name": "Test Hospital",
    "Industry": "Healthcare",
    "AnnualRevenue": 50000000
}

response = requests.post(
    "https://your-app.railway.app/webhook/salesforce-account",
    json=mock_account
)
print("Webhook Status:", response.status_code)
print("Job ID:", response.json().get("job_id"))
```

### 2. End-to-End Test

1. Create test Account in Salesforce
2. Trigger enrichment workflow  
3. Monitor job processing
4. Verify Lead creation
5. Check AI-generated messages

---

## 💰 Cost Management

### Monthly Cost Estimates

| Service | Usage | Cost |
|---------|--------|------|
| Railway Hosting | App + DB + Redis | $20-50 |
| Apify | 100-500 profiles | $50-125 |
| Hunter.io | 1,000 emails | $49-99 |
| Google Search | 1,000-3,000 queries | $5-15 |
| OpenAI | 100K-1M tokens | $100-200 |
| **Total** | | **$224-489** |

### Budget Alerts

The system includes automatic budget monitoring:
- Real-time cost tracking
- Daily/monthly spending alerts
- Automatic service throttling at limits

---

## 🎯 Success Metrics

### Business KPIs
- **Accounts Processed**: Target 50+ per month
- **Lead Creation Rate**: Target 85%+ success
- **Response Rate Improvement**: Target 15%+ vs generic outreach
- **Cost per Lead**: Target <$5 per qualified lead

### Technical KPIs  
- **System Uptime**: Target 99.5%
- **Average Processing Time**: Target <10 minutes per account
- **API Success Rate**: Target 95%+ for all external APIs
- **Error Recovery Rate**: Target 95%+ automatic recovery

---

## 🆘 Troubleshooting

### Common Issues

1. **Redis Connection Errors**:
   ```bash
   # Check Redis service in Railway
   railway logs --service redis
   ```

2. **Database Connection Issues**:
   ```bash
   # Verify DATABASE_URL format
   postgresql+asyncpg://user:pass@host:port/dbname
   ```

3. **Salesforce Authentication**:
   ```bash
   # Test credentials
   curl -X POST https://login.salesforce.com/services/oauth2/token \
        -d "grant_type=password&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET&username=YOUR_USERNAME&password=YOUR_PASSWORD_AND_TOKEN"
   ```

4. **API Rate Limits**:
   - Monitor usage in `/webhook/queue/stats`
   - Adjust `MAX_CONCURRENT_JOBS` if hitting limits
   - Check individual service dashboards

### Emergency Procedures

1. **System Down**: Check Railway service status
2. **High Costs**: Review `/webhook/queue/stats` for runaway jobs
3. **Failed Jobs**: Use RQ Dashboard to retry failed jobs
4. **Data Issues**: Check database connections and migrations

---

## 🎉 Go-Live Checklist

- [ ] Railway services deployed and running
- [ ] Environment variables configured
- [ ] Salesforce Connected App created  
- [ ] Custom fields added to Salesforce
- [ ] Workflow rules configured
- [ ] External API keys configured and tested
- [ ] Health checks passing
- [ ] Test webhook working
- [ ] Monitoring and alerting configured
- [ ] Documentation shared with team
- [ ] Success metrics baseline established

**The system is ready for production use!** 🚀
