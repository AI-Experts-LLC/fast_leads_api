# Salesforce Login Configuration Guide

## ✅ **YES! Works with Standard Salesforce.com Accounts**

The system **automatically detects** whether you're using a standard Salesforce.com account or a custom domain. No special configuration needed!

---

## 🔧 **Configuration for Different Account Types**

### **1️⃣ Standard Salesforce.com Account (Most Common)**

**What you have:** Login at `https://login.salesforce.com`

**Environment Variables:**
```bash
# Leave SALESFORCE_DOMAIN empty or set to login.salesforce.com
SALESFORCE_DOMAIN=
# OR
SALESFORCE_DOMAIN=https://login.salesforce.com

SALESFORCE_USERNAME=your.email@company.com
SALESFORCE_PASSWORD=yourpassword
SALESFORCE_SECURITY_TOKEN=YourSecurityToken123
```

**The system automatically uses:** `domain='login'` for authentication ✅

---

### **2️⃣ Custom Domain Account (Enterprise)**

**What you have:** Login at `https://yourcompany.my.salesforce.com`

**Environment Variables:**
```bash
SALESFORCE_DOMAIN=https://yourcompany.my.salesforce.com
SALESFORCE_USERNAME=your.email@company.com
SALESFORCE_PASSWORD=yourpassword
SALESFORCE_SECURITY_TOKEN=YourSecurityToken123
```

**The system automatically uses:** `domain='yourcompany.my.salesforce.com'` ✅

---

## 🔑 **How to Get Your Salesforce Credentials**

### **Step 1: Get Your Security Token**
1. Log into Salesforce
2. Click your profile picture → **Settings**
3. In the left sidebar: **My Personal Information** → **Reset My Security Token**
4. Click **Reset Security Token**
5. Check your email for the new token

### **Step 2: Create Connected App (for API access)**
1. In Salesforce: **Setup** → **App Manager**
2. Click **New Connected App**
3. Fill out basic info:
   - **Connected App Name:** Metrus Account Enrichment
   - **API Name:** Metrus_Account_Enrichment
   - **Contact Email:** your-email@company.com
4. **Enable OAuth Settings:** ✅
5. **Callback URL:** `https://your-app.railway.app/auth/callback`
6. **Selected OAuth Scopes:**
   - Full access (full)
   - Perform requests on your behalf at any time (refresh_token, offline_access)
7. **Save** and wait 2-10 minutes for activation

---

## 🧪 **Test Your Configuration**

### **Method 1: Quick Test Script**
```bash
cd /Users/lucaserb/Documents/MetrusEnergy/fast_leads_api

# Create test file
cat > test_salesforce.py << 'EOF'
import os
from simple_salesforce import Salesforce

# Test standard salesforce.com login
try:
    sf = Salesforce(
        username=os.getenv('SALESFORCE_USERNAME'),
        password=os.getenv('SALESFORCE_PASSWORD'),
        security_token=os.getenv('SALESFORCE_SECURITY_TOKEN'),
        domain='login'  # Standard salesforce.com
    )
    print("✅ Standard Salesforce.com login successful!")
    print(f"   Instance: {sf.sf_instance}")
    print(f"   Session ID: {sf.session_id[:20]}...")
    
    # Test basic query
    result = sf.query("SELECT Id, Name FROM Account LIMIT 1")
    print(f"   Test query: Found {result['totalSize']} accounts")
    
except Exception as e:
    print(f"❌ Login failed: {e}")
EOF

# Run test
python3 test_salesforce.py
```

### **Method 2: Using Our Service**
```bash
python3 -c "
import asyncio
from app.services.salesforce import SalesforceService

async def test():
    async with SalesforceService() as sf:
        print('✅ Salesforce authentication successful!')
        print(f'   Instance: {sf.instance_url}')
        
        # Test account query
        accounts = await sf.query_accounts({'Industry': 'Healthcare'})
        print(f'   Found {len(accounts)} healthcare accounts')

asyncio.run(test())
"
```

---

## 🔍 **Troubleshooting Common Issues**

### **Issue 1: "Invalid username, password, security token"**
**Solution:**
```bash
# 1. Reset your security token (see Step 1 above)
# 2. Make sure password + security token are combined correctly
# Your password should be: yourpassword + securitytoken (no space)
# But in the config, they're separate fields:
SALESFORCE_PASSWORD=yourpassword
SALESFORCE_SECURITY_TOKEN=YourSecurityToken123
```

### **Issue 2: "INVALID_LOGIN: Invalid username, password, security token"**
**Solution:**
```bash
# Check if you have 2FA enabled - you may need to:
# 1. Use a Connected App instead of username/password
# 2. Or get an app-specific password
# 3. Or use IP restrictions in your profile
```

### **Issue 3: "Domain not found"**
**Solution:**
```bash
# For standard accounts, try both:
SALESFORCE_DOMAIN=
# OR
SALESFORCE_DOMAIN=https://login.salesforce.com

# Check your actual login URL in your browser
```

---

## ⚡ **Quick Setup for Standard Salesforce.com**

```bash
# 1. Copy environment template
cp .env.template .env

# 2. Edit your .env file with these settings:
cat >> .env << 'EOF'
# Standard Salesforce.com Account
SALESFORCE_DOMAIN=
SALESFORCE_USERNAME=your.email@company.com
SALESFORCE_PASSWORD=yourpassword
SALESFORCE_SECURITY_TOKEN=YourSecurityToken123
EOF

# 3. Test it works
python3 -c "
from app.services.salesforce import SalesforceService
import asyncio

async def test():
    service = SalesforceService()
    success = await service.authenticate()
    print('✅ SUCCESS!' if success else '❌ FAILED')

asyncio.run(test())
"
```

---

## 🎯 **Summary**

### ✅ **What Works:**
- Standard `@salesforce.com` logins ✅
- Custom domain accounts ✅  
- Developer Edition accounts ✅
- Production orgs ✅
- Sandbox orgs ✅

### 🔧 **Auto-Detection Logic:**
```python
if 'salesforce.com' in domain:
    use_domain = 'login'  # Standard
else:
    use_domain = custom_domain  # Custom
```

### 🚀 **Result:**
**No matter what type of Salesforce account you have, the system will work automatically!** 

Just provide your username, password, and security token - the system handles the rest! 🎉
