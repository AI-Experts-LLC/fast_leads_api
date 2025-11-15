# Railway Deployment Checklist - API Logging System

## Pre-Deployment Checklist

- [x] Database connection working locally
- [x] Middleware logging all requests
- [x] Web dashboard working at `/logs/view`
- [x] Dependencies added to `requirements.txt`
- [x] Documentation written

## Railway Environment Variables

**Before deploying, verify this in Railway dashboard:**

### 1. Navigate to Variables
```
Railway Dashboard → fast-leads-api service → Variables tab
```

### 2. Verify DATABASE_URL

**Should be set to:**
```
DATABASE_URL=${{ Postgres.DATABASE_URL }}
```

**This resolves to private network URL:**
```
postgresql://postgres:[password]@postgres.railway.internal:5432/railway
```

**DO NOT use the public URL in Railway:**
```
❌ postgresql://...@your-host.proxy.rlwy.net:YOUR_PORT/railway  (public - slower)
✅ ${{ Postgres.DATABASE_URL }}                          (private - faster)
```

## Deployment Steps

### 1. Commit Changes
```bash
cd /Users/lucaserb/Documents/MetrusEnergy/fast_leads_api
git add .
git commit -m "Add API logging system with PostgreSQL and web dashboard"
```

### 2. Push to GitHub
```bash
git push origin main
```

### 3. Monitor Railway Deployment
Railway will automatically:
- Detect the push
- Install new dependencies (`asyncpg`, `sqlalchemy`, `alembic`)
- Build the application
- Deploy to `fast-leads-api.up.railway.app`

Watch the logs in Railway dashboard to ensure successful deployment.

## Post-Deployment Verification

### 1. Check Logs Dashboard
```
URL: https://fast-leads-api.up.railway.app/logs/view
Expected: Should load dashboard (might be empty initially)
```

### 2. Verify Database Connection
```bash
curl https://fast-leads-api.up.railway.app/health
```
Expected: Status 200, healthy response

### 3. Generate Test Log
```bash
curl https://fast-leads-api.up.railway.app/test-services
```

### 4. Verify Log Captured
```
Refresh: https://fast-leads-api.up.railway.app/logs/view
Expected: Should show the test-services request
```

### 5. Check Logs Data API
```bash
curl https://fast-leads-api.up.railway.app/logs/data | jq
```
Expected: JSON response with logs array and stats

## Troubleshooting

### Issue: "Connection reset by peer" on logs page

**Cause:** DATABASE_URL not configured correctly

**Fix:**
1. Go to Railway dashboard → fast-leads-api → Variables
2. Check `DATABASE_URL` value
3. Should be: `${{ Postgres.DATABASE_URL }}`
4. If different, update it and redeploy

### Issue: Dashboard loads but no logs appearing

**Cause:** Logs might be getting filtered out or database table not created

**Fix:**
1. Check Railway logs for database initialization message
2. Make a test API call to generate a log
3. Check `/logs/data` endpoint directly:
   ```bash
   curl https://fast-leads-api.up.railway.app/logs/data
   ```

### Issue: 500 error on logs endpoints

**Cause:** Database connection failed or table doesn't exist

**Fix:**
1. Check Railway logs for database errors
2. Verify PostgreSQL service is running in Railway
3. Check DATABASE_URL variable is set correctly
4. Redeploy to trigger database initialization

## Railway Build Logs - What to Look For

### ✅ Successful Deployment Should Show:

```
Installing dependencies from requirements.txt
  - asyncpg (0.29.0)
  - sqlalchemy (2.0.x)
  - alembic (1.13.x)
...
✅ Database initialized successfully
Running on http://[::]:PORT
```

### ❌ Failed Deployment Might Show:

```
⚠️ Failed to initialize database: [error message]
```

If you see this, check DATABASE_URL configuration.

## Current Configuration

**Local (.env):**
- Uses public network URL for testing
- `DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@your-host.proxy.rlwy.net:YOUR_PORT/railway`

**Production (Railway):**
- Uses private network via reference variable
- `DATABASE_URL=${{ Postgres.DATABASE_URL }}`
- Resolves to `postgresql://...@postgres.railway.internal:5432/railway`

## Success Criteria

- [ ] Railway deployment shows "✅ Database initialized successfully"
- [ ] `/logs/view` dashboard loads without errors
- [ ] Test API calls appear in the logs dashboard
- [ ] Response times are displayed in milliseconds
- [ ] Full request/response JSON is visible when expanding rows
- [ ] Statistics show: total count, avg duration, success rate

## Notes

- The `.env` file is **NOT** deployed to Railway (it's in `.gitignore`)
- Railway uses its own environment variables from the dashboard
- Private network URL only works inside Railway's infrastructure
- Logs will persist across deployments (stored in PostgreSQL database)
- Old logs are NOT automatically deleted - consider adding a cleanup job later

---

**Last Updated:** 2025-11-15
**Deployment Target:** https://fast-leads-api.up.railway.app
