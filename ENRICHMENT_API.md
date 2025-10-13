# Salesforce Enrichment API

This API provides comprehensive enrichment capabilities for Salesforce accounts and contacts.

## Endpoints

### 1. Account Enrichment

**Endpoint:** `POST /enrich/account`

Enriches a Salesforce account with comprehensive company data including:
- Company description, HQ location, employee count
- Geographic footprint and recent company news
- Capital project history and infrastructure upgrades
- Energy efficiency projects
- Financial data (optional)

**Request Body:**
```json
{
  "account_id": "001VR00000UhY3oYAF",
  "overwrite": false,
  "include_financial": true
}
```

**Parameters:**
- `account_id` (required): Salesforce Account ID
- `overwrite` (optional, default: false): Whether to overwrite existing field data
- `include_financial` (optional, default: false): Include comprehensive financial analysis (WACC, debt, revenue, credit quality, etc.)

**Response:**
```json
{
  "status": "success",
  "message": "Successfully enriched account 001VR00000UhY3oYAF",
  "data": {
    "status": "success",
    "record_id": "001VR00000UhY3oYAF",
    "message": "Successfully enriched account 001VR00000UhY3oYAF",
    "enriched_fields": {
      "account_name": "St. Joseph Regional Medical Center",
      "overwrite_mode": false,
      "financial_included": true
    }
  },
  "timestamp": "2025-10-13T20:30:45.123456"
}
```

**cURL Example:**
```bash
curl -X POST "https://fast-leads-api.up.railway.app/enrich/account" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "001VR00000UhY3oYAF",
    "overwrite": false,
    "include_financial": true
  }'
```

**Python Example:**
```python
import requests

url = "https://fast-leads-api.up.railway.app/enrich/account"
payload = {
    "account_id": "001VR00000UhY3oYAF",
    "overwrite": False,
    "include_financial": True
}

response = requests.post(url, json=payload)
print(response.json())
```

---

### 2. Contact Enrichment

**Endpoint:** `POST /enrich/contact`

Enriches a Salesforce contact with personalized data including:
- Personalized rapport summaries (4 variations for different email campaigns)
- Local sports teams and personal interests
- Role description and work experience analysis
- Energy project history
- Why their role is relevant to Metrus
- Custom email campaign subject lines (4 variations)
- LinkedIn profile data (optional)

**Request Body:**
```json
{
  "contact_id": "003VR00000YLIzRYAX",
  "overwrite": false,
  "include_linkedin": true
}
```

**Parameters:**
- `contact_id` (required): Salesforce Contact ID
- `overwrite` (optional, default: false): Whether to overwrite existing field data
- `include_linkedin` (optional, default: false): Include LinkedIn profile scraping and enrichment

**Response:**
```json
{
  "status": "success",
  "message": "Successfully enriched contact 003VR00000YLIzRYAX",
  "data": {
    "status": "success",
    "record_id": "003VR00000YLIzRYAX",
    "message": "Successfully enriched contact 003VR00000YLIzRYAX",
    "enriched_fields": {
      "contact_name": "John Doe",
      "company": "Cleveland Clinic",
      "overwrite_mode": false,
      "linkedin_included": true
    }
  },
  "timestamp": "2025-10-13T20:30:45.123456"
}
```

**cURL Example:**
```bash
curl -X POST "https://fast-leads-api.up.railway.app/enrich/contact" \
  -H "Content-Type: application/json" \
  -d '{
    "contact_id": "003VR00000YLIzRYAX",
    "overwrite": false,
    "include_linkedin": true
  }'
```

**Python Example:**
```python
import requests

url = "https://fast-leads-api.up.railway.app/enrich/contact"
payload = {
    "contact_id": "003VR00000YLIzRYAX",
    "overwrite": False,
    "include_linkedin": True
}

response = requests.post(url, json=payload)
print(response.json())
```

---

## Enriched Fields

### Account Fields

**Basic Company Information:**
- `General_Company_Description__c`: Professional 100-150 word description
- `HQ_location__c`: Main headquarters address
- `Employee_count__c`: Number of employees
- `Geographic_footprint__c`: Service area description
- `General_Company_News__c`: Recent news and achievements

**Capital & Infrastructure:**
- `Capital_and_project_history__c`: Recent capital outlays (last 5 years)
- `Past_future_capital_uses__c`: Past and planned capital projects
- `Infrastructure_upgrades__c`: Building/infrastructure improvements
- `Energy_efficiency_projects__c`: Energy and emissions reduction projects

**Financial Data (when include_financial=true):**
- `Recent_disclosures__c`: Recent financial disclosures and filings
- `Weighted_average_cost_of_capital__c`: WACC calculation
- `Debt_appetite_constraints__c`: Debt capacity and constraints
- `Debt__c`: Other debt instruments and obligations
- `Long_term_financial_outlook__c`: Capital project history and financial trends
- `Off_balance_sheet_financing__c`: Synthesized off-balance appetite assessment
- `Revenue__c`: Annual revenue (e.g., "$17.8B" or "$450M")
- `Company_Credit_Quality__c`: Simple credit rating format
- `Company_Credit_Quality_Detailed__c`: Detailed credit analysis

### Contact Fields

**Personalized Rapport:**
- `Local_sports_team__c`: Local sports teams (comma-separated)
- `Rapport_summary__c`: Professional recognition/achievement opening
- `Rapport_summary_2__c`: Shared professional interest opening
- `Rapport_summary_3__c`: Company-specific observation opening
- `Rapport_summary_4__c`: Local/regional connection opening
- `Miscellaneous_notes__c`: Additional rapport-building details

**Work Experience:**
- `Role_description__c`: Detailed role and responsibilities
- `Energy_Project_History__c`: Energy/sustainability project involvement
- `Why_their_role_is_relevant_to_Metrus__c`: Strategic sales intelligence
- `Summary_Why_should_they_care__c`: Persona-specific pain points
- `General_personal_information_notes__c`: Professional background notes

**Email Customization:**
- `Campaign_1_Subject_Line__c`: Professional recognition subject
- `Campaign_2_Subject_Line__c`: Industry connection subject
- `Campaign_3_Subject_Line__c`: Company-specific observation subject
- `Campaign_4_Subject_Line__c`: Local/regional connection subject

**LinkedIn Data (when include_linkedin=true):**
- `Full_Linkedin_Data__c`: Complete LinkedIn profile JSON
- `Department`: Derived from job title
- `Time_in_role__c`: Duration in current role
- `Total_work_experience__c`: Total years of experience
- `Tenure_at_current_company__c`: Time at current company
- `Time_Zone__c`: Timezone based on location
- `Description`: AI-generated professional summary

---

## Error Handling

All endpoints return standard error responses:

**400 Bad Request:**
```json
{
  "detail": "Account enrichment failed: Account not found"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Error enriching account: Connection timeout"
}
```

---

## Rate Limiting & Performance

- Account enrichment typically takes 30-60 seconds (120+ seconds with financial data)
- Contact enrichment typically takes 20-40 seconds (60+ seconds with LinkedIn)
- LinkedIn scraping adds 15-30 seconds per contact
- Financial analysis adds 60-90 seconds per account

**Recommendations:**
- Run enrichments during off-peak hours for batch operations
- Use `overwrite=false` to only update empty fields (faster)
- Enable financial/LinkedIn only when needed (slower but comprehensive)

---

## Architecture

The enrichment system consists of:

1. **FastAPI Service Layer** (`app/services/enrichment.py`)
   - Manages enrichment requests
   - Handles errors and response formatting
   - Provides clean API interface

2. **Enricher Modules** (`app/enrichers/`)
   - `web_search_account_enricher.py`: Account data enrichment
   - `web_search_contact_enricher.py`: Contact data enrichment
   - `linkedin_contact_enricher.py`: LinkedIn scraping via Apify
   - `financial_enricher.py`: Financial data analysis with GPT-5
   - `salesforce_credit_enricher.py`: Credit quality via Fast Leads API
   - `field_validator.py`: Data validation and quality control
   - `zoominfo_contact_enricher.py`: ZoomInfo integration (optional)

3. **AI Models Used:**
   - GPT-4o-mini-search-preview: Web search and data extraction
   - GPT-5: Financial analysis with reasoning
   - GPT-4o: Text refinement and summarization

---

## Environment Variables Required

```bash
# Salesforce
SALESFORCE_USERNAME=your-username
SALESFORCE_PASSWORD=your-password
SALESFORCE_SECURITY_TOKEN=your-token
SALESFORCE_DOMAIN=login

# OpenAI
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4o-mini-search-preview

# LinkedIn (Apify)
APIFY_API_TOKEN=your-apify-token
SERPER_API_KEY=your-serper-key

# Optional: ZoomInfo
ZOOMINFO_CLIENT_ID=your-client-id
ZOOMINFO_CLIENT_SECRET=your-client-secret
```

---

## Testing

Test the endpoints locally:

```bash
# Start the server
cd fast_leads_api
python -m hypercorn main:app --bind 0.0.0.0:8000

# Test account enrichment
curl -X POST "http://localhost:8000/enrich/account" \
  -H "Content-Type: application/json" \
  -d '{"account_id": "001VR00000UhY3oYAF", "overwrite": false}'

# Test contact enrichment
curl -X POST "http://localhost:8000/enrich/contact" \
  -H "Content-Type: application/json" \
  -d '{"contact_id": "003VR00000YLIzRYAX", "overwrite": false}'
```

---

## Deployment on Railway

The enrichment API is deployed on Railway at:
```
https://fast-leads-api.up.railway.app
```

**Railway Environment Variables:**
- All environment variables listed above must be set in Railway dashboard
- Ensure `PORT` is set to Railway's dynamic port (Railway sets this automatically)

**Deployment Process:**
1. Push changes to GitHub
2. Railway automatically deploys from `main` branch
3. Check deployment logs for any errors
4. Test endpoints using the Railway URL

---

## Troubleshooting

**Import Errors:**
- Ensure all dependencies in `requirements.txt` are installed
- Check that enricher files are in `app/enrichers/` directory

**Connection Timeouts:**
- Increase timeout settings for long-running enrichments
- Consider using background tasks for batch operations

**Validation Errors:**
- Check that field names match Salesforce API names
- Verify Salesforce field types (Text vs Long Text)
- Ensure field length limits are respected (255 chars for Text fields)

**API Key Issues:**
- Verify all required environment variables are set
- Check that API keys are valid and have proper permissions
- For LinkedIn: ensure Apify actor permissions are correct

---

## Support

For issues or questions:
1. Check deployment logs on Railway
2. Review enrichment logs in Salesforce
3. Test individual enricher scripts locally first
4. Contact the development team with error details

