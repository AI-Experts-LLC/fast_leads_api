# API Authentication Guide

## Overview

The Salesforce enrichment endpoints now require API key authentication for security. This prevents unauthorized access to your enrichment services.

---

## 🔐 How It Works

**Authentication Method:** API Key in Header  
**Header Name:** `X-API-Key`  
**Protected Endpoints:**
- `POST /enrich/account`
- `POST /enrich/contact`

**Public Endpoints** (no auth required):
- `GET /health`
- `GET /version`
- `GET /`

---

## 🚀 Setup in Railway

### 1. Set the API Key Environment Variable

Go to your Railway dashboard:
1. Select the `fast-leads-api` project
2. Click on **Variables**
3. Add a new variable:
   - **Name:** `API_KEY`
   - **Value:** Your secret API key (e.g., `metrus-secure-key-2024`)
4. Save and redeploy

**Recommended:** Use a strong, random key:
```bash
# Generate a secure random key (run locally)
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 📝 Usage Examples

### cURL

```bash
curl -X POST "https://fast-leads-api.up.railway.app/enrich/account" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "account_id": "001VR00000UhY3oYAF",
    "overwrite": false,
    "include_financial": true
  }'
```

### Python

```python
import requests

url = "https://fast-leads-api.up.railway.app/enrich/contact"
headers = {
    "Content-Type": "application/json",
    "X-API-Key": "your-api-key-here"
}
payload = {
    "contact_id": "003VR00000YLIzRYAX",
    "overwrite": False,
    "include_linkedin": True
}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
```

### Test Script

```bash
# Option 1: Set environment variable
export API_KEY=your-api-key-here
python3 test_enrichment_api.py --account 001VR00000UhY3oYAF

# Option 2: Pass as argument
python3 test_enrichment_api.py --account 001VR00000UhY3oYAF --api-key your-api-key-here

# Option 3: Set METRUS_API_KEY
export METRUS_API_KEY=your-api-key-here
python3 test_enrichment_api.py --contact 003VR00000YLIzRYAX --linkedin
```

---

## ⚠️ Error Responses

### Missing API Key

**Request:**
```bash
curl -X POST "https://fast-leads-api.up.railway.app/enrich/account" \
  -H "Content-Type: application/json" \
  -d '{"account_id": "001VR00000UhY3oYAF"}'
```

**Response:** `401 Unauthorized`
```json
{
  "detail": "Missing API Key. Please provide X-API-Key header."
}
```

### Invalid API Key

**Request:**
```bash
curl -X POST "https://fast-leads-api.up.railway.app/enrich/account" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: wrong-key" \
  -d '{"account_id": "001VR00000UhY3oYAF"}'
```

**Response:** `403 Forbidden`
```json
{
  "detail": "Invalid API Key"
}
```

---

## 🔒 Security Best Practices

1. **Keep Your API Key Secret**
   - Never commit API keys to git
   - Don't share keys in public channels
   - Use environment variables only

2. **Rotate Keys Periodically**
   - Change the API key every 90 days
   - Update the `API_KEY` variable in Railway

3. **Use Different Keys for Different Environments**
   - Development: One key
   - Production: Different key

4. **Monitor Usage**
   - Check Railway logs for unauthorized access attempts
   - Look for `401` or `403` errors

---

## 🛠️ Testing

### Test Without Authentication (Should Fail)

```bash
curl -X POST "https://fast-leads-api.up.railway.app/enrich/account" \
  -H "Content-Type: application/json" \
  -d '{"account_id": "001VR00000UhY3oYAF"}'
  
# Expected: 401 Unauthorized
```

### Test With Valid Authentication (Should Succeed)

```bash
export API_KEY=your-api-key-here

python3 test_enrichment_api.py --account 001VR00000UhY3oYAF
# Expected: 200 OK with enrichment data
```

---

## 📚 Implementation Details

### Authentication Flow

```
1. Client sends request with X-API-Key header
2. FastAPI dependency injection calls verify_api_key()
3. verify_api_key() checks header against environment variable
4. If valid: Request proceeds
5. If invalid: Returns 401/403 error
```

### Code Location

- **Auth Module:** `app/auth.py`
- **Main API:** `main.py` (imports verify_api_key)
- **Protected Endpoints:** Lines 635-728 in main.py

---

## 🔄 Migration Guide

If you have existing code calling these endpoints:

**Before (without auth):**
```python
response = requests.post(url, json=payload)
```

**After (with auth):**
```python
headers = {"X-API-Key": os.getenv("API_KEY")}
response = requests.post(url, json=payload, headers=headers)
```

---

## ❓ FAQ

**Q: What if I forget my API key?**  
A: Reset it in Railway dashboard under Variables → API_KEY

**Q: Can I use the same key for local testing?**  
A: Yes, set it in your local `.env` file: `API_KEY=your-key`

**Q: Do all endpoints require authentication?**  
A: No, only enrichment endpoints. Health checks don't require auth.

**Q: Can I have multiple API keys?**  
A: Currently no, but you can implement token rotation by changing the key in Railway.

**Q: Is this secure enough?**  
A: For basic protection yes. For enterprise needs, consider OAuth2 or JWT tokens.

---

## 📞 Support

If you encounter authentication issues:
1. Verify API_KEY is set in Railway
2. Check the key matches exactly (no extra spaces)
3. Ensure X-API-Key header is included
4. Check Railway logs for error details

---

**Status:** ✅ Authentication Active  
**Last Updated:** 2025-10-13

