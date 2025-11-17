# Salesforce Update Approval Workflow

## Overview

The enrichment system now includes an approval workflow for Salesforce updates. Instead of directly updating Salesforce records during enrichment, updates are queued to PostgreSQL for manual review and approval through the dashboard.

## Architecture

### Database Model

**Table**: `pending_updates`

```sql
- id: Integer (Primary Key)
- created_at: DateTime
- updated_at: DateTime
- status: Enum (pending, approved, rejected)
- record_type: Enum (Account, Contact)
- record_id: String (Salesforce ID)
- record_name: String (Display name)
- field_updates: JSON (Field: Value pairs)
- enrichment_type: String (e.g., "web_search_account")
- approved_by: String (User who approved)
- approved_at: DateTime
```

### Components

1. **Database Models** (`app/models.py`)
   - `PendingUpdate`: Model for pending Salesforce updates
   - `UpdateStatus`: Enum for update statuses
   - `RecordType`: Enum for Salesforce record types

2. **Pending Updates Service** (`app/services/pending_updates.py`)
   - `queue_update()`: Queue a Salesforce update for approval
   - `get_pending_updates()`: Retrieve pending updates with filters
   - `approve_update()`: Approve and execute a single update
   - `approve_all_pending()`: Bulk approve all pending updates
   - `reject_update()`: Reject an update (no Salesforce write)

3. **Enrichers** (Modified)
   - `WebSearchContactEnricher`: Updated to support queue mode
   - `WebSearchAccountEnricher`: Updated to support queue mode
   - Both accept `queue_mode=True` parameter and `pending_updates_service` instance

4. **API Endpoints** (`main.py`)
   - `GET /pending-updates`: List pending updates
   - `POST /pending-updates/{id}/approve`: Approve single update
   - `POST /pending-updates/approve-all`: Approve all pending
   - `POST /pending-updates/{id}/reject`: Reject update

5. **Dashboard UI** (`app/templates/dashboard.html`)
   - Real-time pending updates display
   - Per-field view with approve/reject buttons
   - Bulk "Approve All" button
   - Auto-refresh every 10 seconds

## Usage

### For Developers

#### Enabling Queue Mode

When calling enrichers, pass `queue_mode=True` and provide the pending updates service:

```python
from app.enrichers.web_search_contact_enricher import WebSearchContactEnricher
from app.services.pending_updates import PendingUpdatesService
from app.database import get_db

# Get database session
async with get_db() as db:
    # Create pending updates service
    pending_service = PendingUpdatesService(db, sf_connection)

    # Initialize enricher with queue mode
    enricher = WebSearchContactEnricher(
        db_session=db,
        pending_updates_service=pending_service
    )

    # Process enrichment in queue mode
    await enricher.process_contact_enrichment(
        record_id="003...",
        overwrite=False
    )

    # Updates are now queued instead of directly applied
    # Call update_contact_fields with queue_mode=True
    await enricher.update_contact_fields(
        contact_id="003...",
        field_data={...},
        queue_mode=True  # This queues instead of updating
    )
```

#### Direct Update Mode (Legacy)

To bypass the approval workflow and directly update Salesforce:

```python
# Don't pass db_session or pending_updates_service
enricher = WebSearchContactEnricher()

# Or explicitly set queue_mode=False
await enricher.update_contact_fields(
    contact_id="003...",
    field_data={...},
    queue_mode=False  # Direct Salesforce update
)
```

### For End Users

#### Dashboard Access

1. Navigate to `/dashboard` (requires password)
2. Scroll to "Pending Salesforce Updates" section
3. View all queued updates with field details

#### Approving Updates

**Single Update:**
1. Review the record name and fields to be updated
2. Click "✓ Approve" button
3. Confirm the action
4. Update is immediately applied to Salesforce

**Bulk Approval:**
1. Review all pending updates
2. Click "✓ Approve All" button at the top
3. Confirm the bulk action
4. All updates are processed sequentially

#### Rejecting Updates

1. Review the update
2. Click "✗ Reject" button
3. Confirm the action
4. Update is marked as rejected (not applied to Salesforce)

## API Examples

### List Pending Updates

```bash
curl -X GET "http://localhost:8000/pending-updates" \
  --cookie "dashboard_session=your_session_token"
```

Response:
```json
{
  "status": "success",
  "count": 2,
  "updates": [
    {
      "id": 1,
      "created_at": "2025-11-17T17:00:00",
      "record_type": "Contact",
      "record_id": "003VR00000ABC123",
      "record_name": "John Doe",
      "field_updates": {
        "Rapport_summary__c": "I saw the recognition your team got...",
        "Local_sports_team__c": "Boston Red Sox, Boston Celtics"
      },
      "enrichment_type": "web_search_contact",
      "status": "pending"
    }
  ],
  "timestamp": "2025-11-17T17:30:00"
}
```

### Approve Single Update

```bash
curl -X POST "http://localhost:8000/pending-updates/1/approve" \
  --cookie "dashboard_session=your_session_token"
```

### Approve All Updates

```bash
curl -X POST "http://localhost:8000/pending-updates/approve-all" \
  --cookie "dashboard_session=your_session_token"
```

### Reject Update

```bash
curl -X POST "http://localhost:8000/pending-updates/1/reject" \
  --cookie "dashboard_session=your_session_token"
```

## Benefits

1. **Quality Control**: Manual review before data enters Salesforce
2. **Audit Trail**: Full history of what was changed and when
3. **Safety**: Prevent bad AI outputs from polluting CRM data
4. **Flexibility**: Reject invalid enrichments, approve good ones
5. **Visibility**: Dashboard shows exactly what will be updated

## Migration Notes

### Backward Compatibility

- Enrichers still support direct Salesforce updates (default behavior)
- Only enable queue mode when `db_session` and `pending_updates_service` are provided
- Existing code continues to work without modifications

### Database Migration

The `pending_updates` table is automatically created on application startup via:

```python
@app.on_event("startup")
async def startup_event():
    await init_db()  # Creates all tables including pending_updates
```

## Future Enhancements

1. **User Tracking**: Track which dashboard user approved/rejected updates
2. **Field-Level Approval**: Approve individual fields instead of all-or-nothing
3. **Edit Before Approve**: Allow editing field values before applying
4. **Notifications**: Email/Slack notifications for pending updates
5. **Bulk Edit**: Edit multiple updates before approval
6. **Auto-Approval Rules**: Define rules for automatic approval of certain updates

## Troubleshooting

### Updates Not Queuing

**Problem**: Enrichment runs but no pending updates appear

**Solutions**:
1. Verify `queue_mode=True` is passed to `update_contact_fields()` or `update_account_fields()`
2. Check that `pending_updates_service` is provided to enricher constructor
3. Verify database connection is working
4. Check server logs for errors

### Dashboard Not Loading Updates

**Problem**: Dashboard shows spinner or "Error loading pending updates"

**Solutions**:
1. Check browser console for JavaScript errors
2. Verify session authentication is valid
3. Test `/pending-updates` endpoint directly
4. Check database connection

### Approved Updates Not Applying

**Problem**: Clicking approve doesn't update Salesforce

**Solutions**:
1. Verify Salesforce connection is working (`/salesforce/status`)
2. Check server logs for Salesforce API errors
3. Verify record IDs are valid
4. Check field names match Salesforce schema

## Security Considerations

- All endpoints require dashboard session authentication
- Only authenticated users can approve/reject updates
- No API key bypass for pending updates (session-only)
- Field validation still applies before queueing
- Salesforce credentials never exposed to frontend

## Performance

- Minimal overhead: One extra database write per enrichment
- Dashboard auto-refreshes every 10 seconds
- Approval operations are async and non-blocking
- Bulk approval processes updates sequentially to avoid rate limits
