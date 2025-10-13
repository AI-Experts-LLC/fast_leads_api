# 🚀 Quick Start - Enrichment API

## 📍 API Endpoints

```
Base URL: https://fast-leads-api.up.railway.app
```

### 1️⃣ Enrich Account
```bash
POST /enrich/account
```

**Body:**
```json
{
  "account_id": "001VR00000UhY3oYAF",
  "overwrite": false,
  "include_financial": true
}
```

### 2️⃣ Enrich Contact
```bash
POST /enrich/contact
```

**Body:**
```json
{
  "contact_id": "003VR00000YLIzRYAX",
  "overwrite": false,
  "include_linkedin": true
}
```

---

## 🧪 Test Commands

```bash
# Health check
curl https://fast-leads-api.up.railway.app/health

# Test account enrichment
python3 test_enrichment_api.py --account 001VR00000UhY3oYAF

# Test account with financial data
python3 test_enrichment_api.py --account 001VR00000UhY3oYAF --financial

# Test contact enrichment
python3 test_enrichment_api.py --contact 003VR00000YLIzRYAX

# Test contact with LinkedIn
python3 test_enrichment_api.py --contact 003VR00000YLIzRYAX --linkedin
```

---

## 📦 Deploy to Railway

```bash
cd /Users/lucaserb/Documents/MetrusEnergy/fast_leads_api

git add .
git commit -m "Add enrichment API endpoints"
git push origin main
```

Railway will automatically deploy! ✅

---

## ⏱️ Expected Times

| Operation | Time | Fields |
|-----------|------|--------|
| Account (basic) | 30-60s | 10 fields |
| Account (financial) | 90-180s | 22 fields |
| Contact (basic) | 20-40s | 15 fields |
| Contact (LinkedIn) | 60-90s | 21 fields |

---

## 📚 Full Documentation

See `ENRICHMENT_API.md` for complete documentation.

