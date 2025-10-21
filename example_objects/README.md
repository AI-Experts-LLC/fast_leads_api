# 📋 Example Salesforce Objects

This folder contains real example Salesforce objects (anonymized) to demonstrate the data structure for Accounts and Contacts.

## 📂 Files

### Accounts (3 examples)
- `account_example_1.json` - West Valley Medical Center (Caldwell, ID)
- `account_example_2.json` - Community Medical Center
- `account_example_3.json` - St. Luke's Magic Valley RMC

### Contacts (3 examples)
- `contact_example_1.json` - Tracy Fialli (Senior Energy Engineer)
- `contact_example_2.json` - Lynn Bernard
- `contact_example_3.json` - Jeff Shoaf

## 🏢 Account Object Structure

Salesforce Account objects contain comprehensive company information:

### Core Fields
- `Id` - Salesforce unique identifier (18 characters)
- `Name` - Company name
- `Type` - Account type (e.g., "Customer", "Prospect")
- `RecordTypeId` - Record type identifier
- `ParentId` - Parent account ID (for subsidiaries)

### Contact Information
- `Phone`, `Fax`, `Website` - Basic contact info
- `BillingAddress` - Primary address (street, city, state, postal code)
- `ShippingAddress` - Secondary address

### Business Details
- `Industry` - Industry classification (e.g., "Healthcare")
- `AnnualRevenue` - Company revenue
- `NumberOfEmployees` - Employee count
- `Description` - Company description

### Custom Fields (Metrus Energy Specific)
- `Building_Automation_Controls__c` - Automation capabilities
- `Lighting__c`, `HVAC_Upgrades__c`, `Pumps_Motors_Drives__c` - Infrastructure flags
- `Compressed_Air__c`, `Utility_Tariff_Rate_Optimization__c` - Energy capabilities
- `Account_Value__c` - Account value score
- `Account_Status__c` - Current status
- `NDA_Status__c`, `PD_Status__c` - Legal/due diligence status
- `Primary_Business_Activity__c` - Primary business focus
- `Program_Participation__c` - Active programs

### Metadata
- `CreatedDate`, `CreatedById` - Creation timestamp
- `LastModifiedDate`, `LastModifiedById` - Last update
- `LastActivityDate` - Last activity
- `SystemModstamp` - System modification timestamp

## 👤 Contact Object Structure

Salesforce Contact objects contain individual prospect information:

### Core Fields
- `Id` - Salesforce unique identifier (18 characters)
- `AccountId` - Related account ID
- `FirstName`, `LastName`, `Name` - Name fields
- `Title` - Job title
- `Department` - Department/division

### Contact Information
- `Email` - Primary email address
- `Phone` - Office phone
- `MobilePhone` - Mobile phone
- `HomePhone`, `OtherPhone` - Additional phones
- `MailingAddress` - Primary address (street, city, state, postal code)
- `OtherAddress` - Secondary address

### Communication Preferences
- `HasOptedOutOfEmail` - Email opt-out flag
- `HasOptedOutOfFax` - Fax opt-out flag
- `DoNotCall` - Do not call flag
- `IsEmailBounced` - Email bounce status
- `EmailBouncedReason`, `EmailBouncedDate` - Bounce details

### Professional Details
- `Description` - Professional biography/summary
- `ReportsToId` - Manager/supervisor contact ID
- `LeadSource` - Original lead source
- `AssistantName`, `AssistantPhone` - Assistant info

### Custom Fields (Metrus Energy Specific)
- `Account_Type__c` - Related account type
- `Include_in_Mailings__c` - Mailing list flag
- `dupcheck__dc3DisableDuplicateCheck__c` - Duplicate check flag
- `SmartvCard__Organization__c` - Organization info

### Metadata
- `CreatedDate`, `CreatedById` - Creation timestamp
- `LastModifiedDate`, `LastModifiedById` - Last update
- `LastActivityDate` - Last activity date
- `SystemModstamp` - System modification timestamp
- `LastViewedDate`, `LastReferencedDate` - View tracking

## 🔍 Field Naming Conventions

Salesforce uses specific naming conventions:

### Standard Fields
- PascalCase: `FirstName`, `LastName`, `CreatedDate`
- No suffix

### Custom Fields
- PascalCase with `__c` suffix: `Account_Value__c`, `Building_Automation_Controls__c`
- Indicates custom field added to Salesforce org

### Relationship Fields
- End with `Id`: `AccountId`, `ParentId`, `ReportsToId`
- Reference other Salesforce objects

### Address Compound Fields
- Prefix with address type: `BillingStreet`, `MailingCity`, `ShippingState`
- Compound into `BillingAddress`, `MailingAddress` objects

## 💡 Usage Examples

### Account Query
```python
# Get account with all fields
account_id = "001VR00000Vh3TrYAJ"
account = sf.Account.get(account_id)

# Access fields
print(account['Name'])  # "West Valley Medical Center"
print(account['Industry'])  # "Healthcare"
print(account['BillingCity'])  # "Caldwell"
print(account['Building_Automation_Controls__c'])  # false
```

### Contact Query
```python
# Get contact with all fields
contact_id = "0030B00001tC3E4QAK"
contact = sf.Contact.get(contact_id)

# Access fields
print(contact['Name'])  # "Tracy Fialli"
print(contact['Title'])  # "Senior Energy Engineer"
print(contact['Email'])  # "tracy_l_fialli@raytheon.com"
print(contact['MobilePhone'])  # "(978) 815-1776"
```

### Enrichment API Usage
```bash
# Enrich account with company data
curl -X POST "http://localhost:8000/enrich/account" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "001VR00000Vh3TrYAJ",
    "overwrite": false,
    "include_financial": true
  }'

# Enrich contact with personalized outreach data
curl -X POST "http://localhost:8000/enrich/contact" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "contact_id": "0030B00001tC3E4QAK",
    "overwrite": false,
    "include_linkedin": true
  }'
```

## 📚 Related Documentation

- **API Endpoints**: See `main.py` for enrichment endpoint documentation
- **Enrichment Service**: See `app/services/enrichment.py` for field mapping
- **Salesforce Integration**: See `app/services/salesforce.py` for connection details
- **CLAUDE.md**: Complete development guide with examples

## 🔒 Privacy & Security

These example objects:
- Are real Salesforce data from Metrus Energy's production org
- Contain healthcare facility and prospect information
- Should NOT be committed to public repositories
- Are intended for internal development reference only

**Note**: The `example_objects/` folder should be added to `.gitignore` if this repo is made public.

---

**Generated**: October 21, 2025
**Source**: Metrus Energy Salesforce Production Org
