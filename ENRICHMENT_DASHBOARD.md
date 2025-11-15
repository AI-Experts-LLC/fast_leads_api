# Enrichment Dashboard

## Overview
The Enrichment Dashboard is a web-based UI for manually enriching Salesforce Accounts and Contacts with external data. It provides a simple interface for operations team members to paste Salesforce URLs and trigger enrichment operations.

## Access

**Local:**
```
http://localhost:8000/enrich
```

**Production:**
```
https://fast-leads-api.up.railway.app/enrich
```

## Features

### 📊 Account Enrichment
Enrich Salesforce Accounts with:
- Company information
- Financial data (revenue, employee count)
- Credit ratings and probability of default (EDF-X)
- Industry and location data

### 👤 Contact Enrichment
Enrich Salesforce Contacts with:
- LinkedIn profile data
- Professional information
- Employment history
- Contact information validation

### 🎯 Key Features
- **Automatic ID Extraction** - Just paste the full Salesforce URL
- **Real-time Status Updates** - See enrichment progress in the browser
- **Configurable Options** - Choose what data to include
- **Error Handling** - Clear error messages if something goes wrong
- **Metrus Branding** - Consistent dark theme with Metrus logo

## How to Use

### Enriching an Account

1. **Navigate to the dashboard:**
   ```
   http://localhost:8000/enrich
   ```

2. **Copy the Salesforce Account URL:**
   - Go to Salesforce
   - Open an Account record
   - Copy the URL from your browser
   - Example: `https://your-org.lightning.force.com/lightning/r/Account/001VR00000UhY5JYAV/view`

3. **Paste into the form:**
   - Paste the full URL into the "Salesforce Account URL" field
   - The Account ID will be automatically extracted

4. **Configure options:**
   - ✓ Overwrite existing data (checked by default)
   - ✓ Include financial data (checked by default)
   - □ Credit data only (unchecked by default)

5. **Click "Enrich Account":**
   - Wait 30-60 seconds for enrichment to complete
   - Results will show in green (success) or red (error)

### Enriching a Contact

1. **Copy the Salesforce Contact URL:**
   - Example: `https://your-org.lightning.force.com/lightning/r/Contact/003VR000001234567/view`

2. **Paste into the Contact form:**
   - Scroll down to the "Enrich Contact" section
   - Paste the URL

3. **Configure options:**
   - ✓ Overwrite existing data (checked by default)
   - ✓ Include LinkedIn data (checked by default)

4. **Click "Enrich Contact":**
   - Wait 15-30 seconds for enrichment to complete
   - Results will show with detailed JSON response

## URL Format

The dashboard automatically extracts IDs from Salesforce URLs:

### Account URLs
```
Pattern: /Account/{15-18 character ID}/view
Example: https://your-org.lightning.force.com/lightning/r/Account/001VR00000UhY5JYAV/view
Extracted ID: 001VR00000UhY5JYAV
```

### Contact URLs
```
Pattern: /Contact/{15-18 character ID}/view
Example: https://your-org.lightning.force.com/lightning/r/Contact/003VR000001234567/view
Extracted ID: 003VR000001234567
```

## Enrichment Options

### Account Options

**Overwrite existing data:**
- ✓ Enabled: Replace all existing Salesforce data with new enriched data
- ✗ Disabled: Only fill in empty fields, preserve existing data

**Include financial data:**
- ✓ Enabled: Fetch revenue, employee count, and other financial metrics
- ✗ Disabled: Skip financial data enrichment

**Credit data only:**
- ✓ Enabled: ONLY enrich with EDF-X credit ratings, skip other enrichment
- ✗ Disabled: Full enrichment including credit data

### Contact Options

**Overwrite existing data:**
- ✓ Enabled: Replace existing contact data with enriched data
- ✗ Disabled: Only fill in empty fields

**Include LinkedIn data:**
- ✓ Enabled: Scrape and enrich from LinkedIn profile
- ✗ Disabled: Skip LinkedIn enrichment

## Response Format

### Success Response
```json
{
  "status": "success",
  "record_id": "001VR00000UhY5JYAV",
  "fields_updated": 15,
  "enrichment_sources": ["OpenAI", "EDF-X"],
  "timestamp": "2025-11-15T18:00:00Z"
}
```

### Error Response
```json
{
  "detail": "Account not found in Salesforce",
  "error_code": "RECORD_NOT_FOUND"
}
```

## API Integration

The dashboard uses these API endpoints:

### POST /enrich/account
```bash
curl -X POST "http://localhost:8000/enrich/account" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-change-in-production" \
  -d '{
    "account_id": "001VR00000UhY5JYAV",
    "overwrite": true,
    "include_financial": true,
    "credit_only": false
  }'
```

### POST /enrich/contact
```bash
curl -X POST "http://localhost:8000/enrich/contact" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-change-in-production" \
  -d '{
    "contact_id": "003VR000001234567",
    "overwrite": true,
    "include_linkedin": true
  }'
```

## Authentication

**Note:** The enrichment endpoints require an API key for authentication.

**Default API Key (local):** `dev-key-change-in-production`

This is hardcoded in the dashboard's JavaScript for convenience. In production, you should:
1. Set a secure `API_KEY` environment variable
2. Update the dashboard to use that key
3. Consider adding user authentication to the dashboard itself

## Timing

| Operation | Typical Duration |
|-----------|-----------------|
| Account Enrichment | 30-60 seconds |
| Contact Enrichment | 15-30 seconds |
| Credit Only | 10-20 seconds |

## Error Messages

### "Could not extract Account/Contact ID from URL"
- **Cause:** URL format is incorrect
- **Solution:** Make sure you're copying the full Salesforce URL with `/Account/` or `/Contact/` in it

### "Account/Contact not found"
- **Cause:** The record doesn't exist in Salesforce or you don't have permission
- **Solution:** Verify the record exists and your API credentials have access

### "Unauthorized" or "Invalid API key"
- **Cause:** API key is missing or incorrect
- **Solution:** Check `API_KEY` environment variable is set correctly

### "Connection timeout"
- **Cause:** External enrichment services (LinkedIn, EDF-X) are slow or unavailable
- **Solution:** Try again in a few minutes

## User Interface

### Design
- **Dark theme** - GitHub-inspired with Metrus blue accents
- **Metrus logo** - Displayed in header
- **Responsive** - Works on desktop and tablet devices
- **Real-time feedback** - Loading spinners and status messages

### Colors
- Background: `#0f1419` (dark gray)
- Cards: `#161b22` (medium gray)
- Borders: `#30363d` (light gray)
- Primary: `#58a6ff` (Metrus blue)
- Success: `#238636` (green)
- Error: `#da3633` (red)

## Best Practices

### For Operations Team

1. **Always check the URL before enriching**
   - Make sure it's the correct account/contact
   - Verify the URL format is correct

2. **Use appropriate options**
   - Enable "Overwrite" if you want to refresh stale data
   - Disable "Overwrite" if you want to preserve manual edits

3. **Review results**
   - Check the JSON response for what was updated
   - Verify in Salesforce that the data looks correct

4. **Handle errors gracefully**
   - If enrichment fails, check the error message
   - Some records may not have enrichment data available

### For Developers

1. **Monitor API usage**
   - Check logs at `/logs/view` to see enrichment activity
   - Monitor API costs (OpenAI, LinkedIn, EDF-X)

2. **Update API key**
   - Change `API_KEY` environment variable in production
   - Update dashboard JavaScript if needed

3. **Customize enrichment logic**
   - Edit `app/services/enrichment.py` for business logic
   - See `CLAUDE.md` for architecture details

## Deployment

The enrichment dashboard is automatically deployed with the API:

1. **Commit changes:**
   ```bash
   git add app/templates/enrichment.html
   git commit -m "Add enrichment dashboard"
   git push
   ```

2. **Access on Railway:**
   ```
   https://fast-leads-api.up.railway.app/enrich
   ```

3. **No additional configuration needed** - Uses existing enrichment endpoints

## Future Enhancements

Potential improvements:

- [ ] Batch enrichment (paste multiple URLs)
- [ ] Scheduled enrichment (enrich all accounts nightly)
- [ ] Enrichment history/audit log
- [ ] User authentication (SAML/OAuth)
- [ ] Export enriched data to CSV
- [ ] Data quality scoring
- [ ] Duplicate detection
- [ ] Enrichment preview (show what will change)

---

**Version:** 1.0.0
**Last Updated:** 2025-11-15
**Status:** ✅ Production Ready
