# API Logging System

## Overview
The Fast Leads API now includes a comprehensive logging system that captures all API requests and responses in a PostgreSQL database with a beautiful web interface for viewing logs.

## Features

### 📊 Web Dashboard
- **Real-time monitoring** with auto-refresh capability
- **Expandable rows** to view full request/response JSON
- **Statistics panel** showing:
  - Total request count
  - Average response time
  - Success rate percentage
- **Dark theme** GitHub-inspired UI
- **Responsive design** works on all screen sizes

### 🗄️ Database Storage
- **PostgreSQL backend** using Railway's managed database
- **Automatic table creation** on first startup
- **Indexed fields** for fast queries:
  - Timestamp (for sorting by recency)
  - Endpoint (for filtering)
- **Captured data**:
  - HTTP method (GET, POST, PUT, DELETE, etc.)
  - Full endpoint path
  - Request body (JSON)
  - Response body (JSON)
  - Status code
  - Response time (milliseconds)
  - Client IP address
  - User agent

### 🔄 Automatic Logging
- **Middleware-based** - logs all requests automatically
- **Non-blocking** - doesn't slow down API responses
- **Error handling** - failed logs don't break requests
- **Smart exclusions** - skips logging for:
  - `/logs/*` endpoints (to avoid infinite loops)
  - `/health` endpoint (too noisy)
  - `/docs` and `/openapi.json` (documentation)

## Usage

### Viewing Logs

**Local Development:**
```
http://localhost:8000/logs/view
```

**Production (Railway):**
```
https://fast-leads-api.up.railway.app/logs/view
```

### API Endpoints

**Get Logs Data (JSON):**
```bash
curl http://localhost:8000/logs/data?limit=50
```

**Parameters:**
- `limit` - Maximum number of logs to return (default: 100)

**Response:**
```json
{
  "logs": [
    {
      "id": 1,
      "timestamp": "2025-11-15T17:37:43.241237+00:00",
      "method": "GET",
      "endpoint": "/test-services",
      "request_body": null,
      "response_body": "{...}",
      "status_code": 200,
      "duration_ms": 1234.56,
      "client_ip": "127.0.0.1",
      "user_agent": "curl/7.79.1"
    }
  ],
  "stats": {
    "total_count": 100,
    "avg_duration": 523.45,
    "success_rate": 95.5,
    "displayed_count": 50
  }
}
```

## Database Configuration

### Environment Variables

**Local Development (.env file):**
```bash
# Public network URL for local testing (can access from outside Railway)
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@your-host.proxy.rlwy.net:YOUR_PORT/railway
```

**Railway Production (set in Railway dashboard):**
```bash
# Use Railway's reference variable - it automatically resolves to private network URL
DATABASE_URL=${{ Postgres.DATABASE_URL }}

# This resolves to (faster, more secure, only works inside Railway):
# postgresql://postgres:YOUR_PASSWORD@postgres.railway.internal:5432/railway
```

**Important:** The `.env` file is NOT deployed to Railway (it's in `.gitignore`). Railway uses its own environment variables that you set in the dashboard.

### Database Schema

The `api_logs` table is automatically created with this schema:

```sql
CREATE TABLE api_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    method VARCHAR(10) NOT NULL,
    endpoint VARCHAR(500) NOT NULL,
    request_body TEXT,
    response_body TEXT,
    status_code INTEGER,
    duration_ms DOUBLE PRECISION,
    client_ip VARCHAR(50),
    user_agent VARCHAR(500)
);

CREATE INDEX idx_api_logs_timestamp ON api_logs(timestamp DESC);
CREATE INDEX idx_api_logs_endpoint ON api_logs(endpoint);
```

## Architecture

### Files Created

1. **`app/database.py`** - Database connection and session management
2. **`app/models.py`** - SQLAlchemy model for `api_logs` table
3. **`app/services/logging_middleware.py`** - FastAPI middleware for automatic logging
4. **`app/templates/logs.html`** - Web UI for viewing logs
5. **`main.py`** (updated) - Added logging endpoints and middleware registration

### Dependencies Added

```txt
asyncpg>=0.29.0       # Async PostgreSQL driver
sqlalchemy>=2.0.0     # ORM for database operations
alembic>=1.13.0       # Database migrations (future use)
```

### How It Works

1. **Request arrives** → Middleware captures request details
2. **Request processed** → API endpoint handles request normally
3. **Response generated** → Middleware captures response details
4. **Log saved** → Asynchronously writes to PostgreSQL database
5. **Dashboard updates** → Web UI queries database for latest logs

## Deployment to Railway

### Step 1: Update Requirements
The `requirements.txt` already includes the new database dependencies:
- `asyncpg>=0.29.0`
- `sqlalchemy>=2.0.0`
- `alembic>=1.13.0`

### Step 2: Configure Environment Variables in Railway

**IMPORTANT:** You need to set the database URL in Railway's dashboard to use the private network.

1. Go to Railway dashboard → Your project
2. Click on **fast-leads-api** service
3. Go to **Variables** tab
4. **Check if `DATABASE_URL` already exists:**
   - If it exists and equals `${{ Postgres.DATABASE_URL }}` → ✅ **You're good!**
   - If it doesn't exist → **Add it:**
     ```
     DATABASE_URL=${{ Postgres.DATABASE_URL }}
     ```
   - If it exists but has a different value → **Update it to:**
     ```
     DATABASE_URL=${{ Postgres.DATABASE_URL }}
     ```

**Why this matters:**
- `${{ Postgres.DATABASE_URL }}` is Railway's **reference variable**
- It automatically resolves to the **private network URL**: `postgresql://...@postgres.railway.internal:5432/railway`
- Private network is **faster** (no internet roundtrip) and **more secure** (stays inside Railway)
- The `.env` file uses public network URL for local testing, but that's NOT deployed to Railway

### Step 3: Deploy to Railway
Push your changes to GitHub:
```bash
git add .
git commit -m "Add API logging system with PostgreSQL and web dashboard"
git push
```

Railway will automatically:
1. Detect the changes
2. Build with new dependencies
3. Deploy the updated API
4. Connect to PostgreSQL using private network

### Step 4: Verify Deployment
Once deployed:

1. **Check the logs dashboard:**
   ```
   https://fast-leads-api.up.railway.app/logs/view
   ```

2. **Verify database connection:**
   ```
   https://fast-leads-api.up.railway.app/health
   ```

3. **Make a test request to generate a log:**
   ```bash
   curl https://fast-leads-api.up.railway.app/test-services
   ```

4. **Refresh logs dashboard** - you should see the test request logged!

### Troubleshooting Railway Deployment

**If logs dashboard shows "Connection reset by peer":**
1. Check Railway dashboard → fast-leads-api → Variables
2. Verify `DATABASE_URL=${{ Postgres.DATABASE_URL }}`
3. Check Railway logs for database connection errors
4. Redeploy if needed: Railway dashboard → fast-leads-api → Settings → Redeploy

## Benefits

1. **🔍 Debugging** - See exactly what requests are coming in and what responses are going out
2. **📈 Monitoring** - Track API usage patterns and performance metrics
3. **🐛 Error Tracking** - Quickly identify failed requests and error patterns
4. **📊 Analytics** - Understand which endpoints are most used
5. **🔐 Security** - Monitor for suspicious activity or abuse
6. **💰 Cost Tracking** - See how many API calls are being made for billing purposes

## Performance Considerations

- **Async logging** - Doesn't block request processing
- **Database indexes** - Fast queries even with millions of logs
- **Automatic cleanup** - Consider adding a cleanup job to remove old logs:
  ```sql
  DELETE FROM api_logs WHERE timestamp < NOW() - INTERVAL '30 days';
  ```

## Security Notes

- Logs are stored in a private Railway database
- The `/logs/view` endpoint has no authentication (add if needed)
- Consider filtering sensitive data from request/response bodies
- Use Railway's private network URL in production for better security

## Future Enhancements

- [ ] Add authentication to logs dashboard
- [ ] Filter logs by endpoint, method, status code
- [ ] Export logs to CSV/JSON
- [ ] Real-time log streaming with WebSockets
- [ ] Automatic old log cleanup (retention policy)
- [ ] Search functionality
- [ ] Error rate alerting

## Troubleshooting

### Can't connect to database locally
- Make sure you're using the **public network** DATABASE_URL
- Check firewall settings
- Verify credentials are correct

### Logs not appearing
- Check server logs for database connection errors
- Verify middleware is registered: `app.add_middleware(APILoggingMiddleware)`
- Test database connection: `python test_db_connection.py`

### Dashboard loads but shows empty
- Make some API requests to generate logs
- Check `/logs/data` endpoint directly
- Verify database has data: `SELECT COUNT(*) FROM api_logs;`

## Support

For issues or questions, check:
- Server logs: `hypercorn main:app`
- Database connection: `python test_db_connection.py`
- API docs: http://localhost:8000/docs
