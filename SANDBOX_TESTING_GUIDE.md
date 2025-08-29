# 🧪 Salesforce Sandbox Testing Guide

## ✅ **Perfect for Testing! Sandbox Environment Fully Supported**

Testing on a Salesforce sandbox is the **recommended approach** - it's safe, isolated, and won't affect your production data.

---

## 🔧 **Sandbox Configuration**

### **Environment Variables for Sandbox Testing:**

```bash
# For Salesforce SANDBOX testing
SALESFORCE_DOMAIN=https://test.salesforce.com
# OR include "sandbox" anywhere in the domain:
# SALESFORCE_DOMAIN=https://mycompany--sandbox.my.salesforce.com

SALESFORCE_USERNAME=your.email@company.com.sandbox
SALESFORCE_PASSWORD=yourpassword
SALESFORCE_SECURITY_TOKEN=YourSandboxSecurityToken123
```

### **Key Differences from Production:**
- **Domain:** Uses `test.salesforce.com` instead of `login.salesforce.com`
- **Username:** Often has `.sandbox` suffix (but not always)
- **Security Token:** Different token from production
- **Data:** Safe test environment, no risk to production

---

## 🎯 **Auto-Detection Logic**

The system now **automatically detects** sandbox environments:

```python
# Updated detection logic
if 'test.salesforce.com' in domain or 'sandbox' in domain:
    domain = 'test'        # ← Sandbox authentication
elif 'salesforce.com' in domain:
    domain = 'login'       # ← Production authentication
else:
    domain = custom_domain # ← Custom domain
```

**Result:** Just set the domain to include "test" or "sandbox" and it works! ✅

---

## 🧪 **Sandbox Detection Test**

Let me test the updated logic:

```python
test_cases = [
    # Sandbox environments
    ('https://test.salesforce.com', 'Standard Sandbox'),
    ('https://mycompany--sandbox.my.salesforce.com', 'Named Sandbox'),
    ('https://dev--sandbox.my.salesforce.com', 'Dev Sandbox'),
    
    # Production environments  
    ('https://login.salesforce.com', 'Production'),
    ('', 'Production (default)'),
    
    # Custom domains
    ('https://company.lightning.force.com', 'Lightning Custom')
]

for domain, description in test_cases:
    if domain:
        domain_lower = domain.lower()
        if 'test.salesforce.com' in domain_lower or 'sandbox' in domain_lower:
            result = 'test'
        elif 'salesforce.com' in domain_lower:
            result = 'login'
        else:
            result = 'custom'
    else:
        result = 'login'
    
    print(f"{description}: domain='{result}'")
```

**Expected Results:**
- Standard Sandbox: `domain='test'` ✅
- Named Sandbox: `domain='test'` ✅  
- Dev Sandbox: `domain='test'` ✅
- Production: `domain='login'` ✅

---

## 🔑 **Getting Sandbox Credentials**

### **Step 1: Access Your Sandbox**
```bash
# If you have a sandbox, login at:
https://test.salesforce.com

# Your username might be:
# - Same as production: your.email@company.com
# - With suffix: your.email@company.com.sandbox
# - Org-specific: your.email@company.com.mysandbox
```

### **Step 2: Get Sandbox Security Token**
```bash
# In your sandbox:
# 1. Click profile → Settings
# 2. My Personal Information → Reset My Security Token
# 3. Check email for the SANDBOX token (different from production!)
```

### **Step 3: Create Test Data**
```bash
# Add some test accounts with healthcare industry:
# - Name: "Test General Hospital"
# - Industry: "Healthcare"  
# - Annual Revenue: $50,000,000
# - Employees: 250
# - Custom fields as needed
```

---

## 🚀 **Quick Sandbox Setup**

### **Create .env for Sandbox Testing:**
```bash
# Copy template
cp .env.template .env.sandbox

# Edit .env.sandbox with sandbox credentials
cat > .env.sandbox << 'EOF'
# SANDBOX TESTING CONFIGURATION
APP_ENV=development
DEBUG=true

# Salesforce Sandbox
SALESFORCE_DOMAIN=https://test.salesforce.com
SALESFORCE_USERNAME=your.email@company.com
SALESFORCE_PASSWORD=yoursandboxpassword
SALESFORCE_SECURITY_TOKEN=YourSandboxToken123

# Test API keys (use free tiers)
OPENAI_API_KEY=sk-your-test-key
APIFY_API_TOKEN=apify_api_test_token

# Local testing infrastructure
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/metrus_test
REDIS_URL=redis://localhost:6379/1

# Low limits for testing
DAILY_API_BUDGET=10.00
MAX_ACCOUNTS_PER_DAY=5
MAX_PROSPECTS_PER_ACCOUNT=3
EOF
```

### **Use Sandbox Environment:**
```bash
# Load sandbox environment
cp .env.sandbox .env

# Or set environment variable
export ENV_FILE=".env.sandbox"
```

---

## 🧪 **Test Sandbox Connection**

Let me create a sandbox-specific test:

```python
#!/usr/bin/env python3
"""Test Salesforce sandbox connectivity"""

def test_sandbox_connection():
    import os
    from dotenv import load_dotenv
    
    # Load environment
    load_dotenv('.env.sandbox' if os.path.exists('.env.sandbox') else '.env')
    
    domain = os.getenv('SALESFORCE_DOMAIN', '')
    username = os.getenv('SALESFORCE_USERNAME')
    
    print("🧪 SANDBOX CONNECTION TEST")
    print("=" * 40)
    print(f"Domain: {domain}")
    print(f"Username: {username}")
    
    # Check if it looks like sandbox
    is_sandbox = 'test.salesforce.com' in domain.lower() or 'sandbox' in domain.lower()
    print(f"Detected as: {'SANDBOX ✅' if is_sandbox else 'PRODUCTION ⚠️'}")
    
    if not is_sandbox:
        print("⚠️  This doesn't look like a sandbox configuration!")
        print("   For sandbox testing, use:")
        print("   SALESFORCE_DOMAIN=https://test.salesforce.com")
    
    return is_sandbox

if __name__ == "__main__":
    test_sandbox_connection()
```

---

## 🔍 **Testing Strategy**

### **Phase 1: Connection Test**
```bash
# Test sandbox authentication
python3 -c "
import asyncio
from app.services.salesforce import SalesforceService

async def test():
    service = SalesforceService()
    success = await service.authenticate()
    print('✅ Sandbox connection works!' if success else '❌ Connection failed')

asyncio.run(test())
"
```

### **Phase 2: Data Test**
```bash
# Query test accounts
python3 -c "
import asyncio
from app.services.salesforce import SalesforceService

async def test():
    async with SalesforceService() as sf:
        accounts = await sf.query_accounts({'Industry': 'Healthcare'})
        print(f'Found {len(accounts)} healthcare accounts in sandbox')

asyncio.run(test())
"
```

### **Phase 3: Full Webhook Test**
```bash
# Test full enrichment pipeline with sandbox data
curl -X POST http://localhost:8000/webhook/salesforce-account \
  -H "Content-Type: application/json" \
  -d '{
    "Id": "001XX000003DHP0YAO",
    "Name": "Test General Hospital", 
    "Industry": "Healthcare"
  }'
```

---

## ⚠️ **Sandbox Limitations**

### **What Works in Sandbox:**
- ✅ Account/Lead CRUD operations
- ✅ Custom fields and objects
- ✅ Workflow rules and validation
- ✅ API calls and authentication
- ✅ Full system testing

### **What's Different:**
- 🔄 Data refreshed periodically
- 📊 Limited to sandbox data size
- 🚫 No production integrations
- 🎯 Perfect for testing new features

---

## 🎉 **Benefits of Sandbox Testing**

### **Safety First:**
- ✅ **Zero risk** to production data
- ✅ **Isolated environment** for testing
- ✅ **Full feature parity** with production
- ✅ **Reset capability** if needed

### **Perfect for Development:**
- 🧪 Test enrichment logic
- 📝 Validate lead creation
- 🔄 Test error handling
- 📊 Monitor API usage safely

---

## 🚀 **Ready to Test!**

Your sandbox environment is now **fully supported** and ready for testing. The system will:

1. **Automatically detect** sandbox domains
2. **Use correct authentication** (`domain='test'`)
3. **Work identically** to production
4. **Keep your production data safe**

**Perfect setup for testing the Metrus Account Enrichment System!** 🎯
