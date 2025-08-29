# 🔑 How to Get Your Salesforce Sandbox Security Token

## 🎯 **Quick Answer: Get it from YOUR SANDBOX, not production!**

**Important:** The sandbox security token is **different** from your production token. You must get it from the sandbox environment itself.

---

## 📋 **Step-by-Step Instructions**

### **Step 1: Login to Your Sandbox**
```
🌐 Go to: https://test.salesforce.com
👤 Username: Usually same as production (sometimes with .sandbox suffix)
🔐 Password: Usually same as production (or set separately in sandbox)
```

### **Step 2: Navigate to Security Token Settings**
```
1. Click your profile picture (top right corner)
2. Click "Settings"
3. In the left sidebar, look for "My Personal Information"
4. Click "Reset My Security Token"
```

### **Step 3: Reset Your Security Token**
```
1. Click the "Reset Security Token" button
2. Salesforce will email you the NEW token
3. Check your email inbox for the token
```

### **Step 4: Copy the Token**
```
📧 Check your email for subject: "Your new Salesforce security token"
📋 Copy the token from the email
⚠️  This token is ONLY for your sandbox environment
```

---

## 🖼️ **Visual Guide**

### **Login Screen:**
```
https://test.salesforce.com
┌─────────────────────────────┐
│ Username: [your@email.com]  │
│ Password: [yourpassword]    │
│ [ Login ]                   │
└─────────────────────────────┘
```

### **Settings Navigation:**
```
Profile Picture → Settings
└── My Personal Information
    └── Reset My Security Token
        └── [ Reset Security Token ]
```

### **Email Example:**
```
From: Salesforce <noreply@salesforce.com>
Subject: Your new Salesforce security token

Your new security token is: AbCdEfGhIjKlMnOpQrStUv

This token is for: your@email.com (Sandbox)
```

---

## ⚠️ **Important Notes**

### **Sandbox vs Production Tokens:**
- ✅ **Sandbox token:** Get from https://test.salesforce.com
- ❌ **Production token:** Get from https://login.salesforce.com
- 🚫 **Never mix them up!** They're environment-specific

### **Token Security:**
- 🔒 **Unique per environment:** Each sandbox has its own token
- 🔄 **Expires when reset:** Old token stops working when you reset
- 📧 **Sent via email:** Always delivered to your registered email
- 🚫 **Never share:** Keep your tokens private

### **Common Issues:**
1. **"Token not working"** → Make sure you're using the SANDBOX token, not production
2. **"No email received"** → Check spam folder, verify email address in sandbox
3. **"Invalid login"** → Verify you're logging into the correct sandbox environment

---

## 🧪 **Sandbox-Specific Considerations**

### **Username Formats:**
```bash
# Most common: Same as production
SALESFORCE_USERNAME=john.doe@company.com

# Sometimes with suffix:
SALESFORCE_USERNAME=john.doe@company.com.sandbox

# Named sandbox:
SALESFORCE_USERNAME=john.doe@company.com.mysandbox
```

### **Password:**
```bash
# Usually same as production
SALESFORCE_PASSWORD=yourproductionpassword

# Sometimes different if set separately in sandbox
SALESFORCE_PASSWORD=yoursandboxpassword
```

### **Security Token:**
```bash
# ALWAYS different from production!
SALESFORCE_SECURITY_TOKEN=YourSandboxSpecificToken123
```

---

## 🔧 **Complete Sandbox Configuration**

### **Your .env.sandbox file should look like:**
```bash
# Salesforce SANDBOX Configuration
SALESFORCE_DOMAIN=https://test.salesforce.com
SALESFORCE_USERNAME=your.email@company.com
SALESFORCE_PASSWORD=yourpassword
SALESFORCE_SECURITY_TOKEN=AbCdEfGhIjKlMnOpQrStUv
```

---

## 🧪 **Testing Your Token**

### **Quick Test Script:**
```bash
# Test your sandbox token
python3 -c "
import os
from simple_salesforce import Salesforce

# Set your sandbox credentials
username = 'your.email@company.com'
password = 'yourpassword'
token = 'YourSandboxToken123'

try:
    sf = Salesforce(
        username=username,
        password=password, 
        security_token=token,
        domain='test'  # Important: 'test' for sandbox!
    )
    print('✅ Sandbox connection successful!')
    print(f'Instance: {sf.sf_instance}')
    
    # Test query
    result = sf.query('SELECT Id, Name FROM Account LIMIT 1')
    print(f'✅ Query test: Found {result[\"totalSize\"]} accounts')
    
except Exception as e:
    print(f'❌ Connection failed: {e}')
    print('Double-check your sandbox credentials!')
"
```

---

## 🔍 **Troubleshooting**

### **If Token Reset Doesn't Work:**

1. **Check Email Settings:**
   - Login to sandbox
   - Go to Settings → Email → My Email Settings
   - Verify your email address is correct

2. **Try Different Browser:**
   - Clear cookies/cache
   - Try incognito/private mode
   - Use different browser

3. **Contact Sandbox Admin:**
   - If you're not the admin, ask them to reset it
   - They can reset tokens for any user

### **If Connection Still Fails:**

1. **Verify Environment:**
   ```bash
   # Make sure you're connecting to sandbox, not production
   domain='test'  # For sandbox
   # NOT domain='login' (that's production)
   ```

2. **Check Username Format:**
   ```bash
   # Try with/without .sandbox suffix
   your@email.com
   your@email.com.sandbox
   ```

3. **Verify Sandbox URL:**
   ```bash
   # Standard sandbox
   https://test.salesforce.com
   
   # Named sandbox (if you have one)
   https://mycompany--sandbox.my.salesforce.com
   ```

---

## 🎯 **Summary**

### **Quick Checklist:**
- [ ] Login to **https://test.salesforce.com** (not login.salesforce.com)
- [ ] Go to Settings → My Personal Information → Reset Security Token
- [ ] Check email for new token
- [ ] Use token in sandbox configuration
- [ ] Set `SALESFORCE_DOMAIN=https://test.salesforce.com`
- [ ] Test connection with our scripts

### **Remember:**
🧪 **Sandbox tokens are DIFFERENT from production tokens**
🔒 **Always get the token from the same environment you're connecting to**
✅ **This keeps your production environment safe while testing**

**Your sandbox security token will come from the sandbox environment - never from production!** 🎉
