# Password Protection for Logs Dashboard

## Overview
The logs dashboard is now fully protected with password authentication. No data is visible or accessible without entering the correct password.

## How It Works

### 1. **Login Page**
- Visiting `/logs/view` without authentication shows a beautiful login page
- User enters password
- Session cookie is created upon successful authentication
- Cookie expires after 24 hours

### 2. **Session-Based Authentication**
- Uses secure, random session tokens
- Tokens stored in-memory (active_sessions dict)
- HTTPOnly cookies for security
- SameSite=strict to prevent CSRF

### 3. **Protected Endpoints**
- `/logs/view` - Shows login page if not authenticated, dashboard if authenticated
- `/logs/data` - Returns 401 Unauthorized without valid session cookie

## Configuration

### Set Password in Environment Variable

**Local (.env file):**
```bash
LOGS_PASSWORD=metrus2025
```

**Railway (Environment Variables):**
```
LOGS_PASSWORD=your-secure-password-here
```

**Default password if not set:** `changeme`

## Usage

### 1. Access the Dashboard
```
http://localhost:8000/logs/view
```
or
```
https://fast-leads-api.up.railway.app/logs/view
```

### 2. Enter Password
- Type the password set in `LOGS_PASSWORD` environment variable
- Click "Access Dashboard"
- If correct, you'll be redirected to the full dashboard
- If incorrect, an error message is shown

### 3. Session Duration
- Sessions last for **24 hours**
- After 24 hours, you'll need to log in again
- Closing browser keeps session active (uses cookies)

## Security Features

✅ **No data leakage** - Login page shows nothing about the logs
✅ **HTTPOnly cookies** - JavaScript cannot access session token
✅ **SameSite strict** - Prevents CSRF attacks
✅ **Secure tokens** - Uses `secrets.token_urlsafe(32)` for session IDs
✅ **Automatic expiry** - Sessions expire after 24 hours
✅ **In-memory storage** - Sessions don't persist across server restarts

## API Endpoints

### POST /logs/auth
Authenticate and receive session cookie.

**Parameters:**
- `password` (query param) - The logs dashboard password

**Response (success):**
```json
{"status": "authenticated"}
```
Sets `logs_session` cookie with 24-hour expiry.

**Response (failure):**
```json
{"detail": "Invalid password"}
```
Status code: 401

### GET /logs/view
View logs dashboard (protected).

**Without auth:** Shows login page
**With auth:** Shows full dashboard

### GET /logs/data
Get logs in JSON format (protected).

**Without auth:**
```json
{"detail": "Unauthorized. Please authenticate at /logs/view"}
```
Status code: 401

**With auth:** Returns logs data and statistics

## Testing

### Test Login Page
```bash
curl http://localhost:8000/logs/view
# Should return HTML login page
```

### Test Authentication
```bash
# Correct password
curl -X POST "http://localhost:8000/logs/auth?password=metrus2025"
# {"status":"authenticated"}

# Wrong password
curl -X POST "http://localhost:8000/logs/auth?password=wrong"
# {"detail":"Invalid password"}
```

### Test Protected Endpoint
```bash
# Without auth
curl http://localhost:8000/logs/data
# {"detail":"Unauthorized. Please authenticate at /logs/view"}

# With auth
curl -X POST "http://localhost:8000/logs/auth?password=metrus2025" -c cookies.txt
curl -b cookies.txt http://localhost:8000/logs/data
# Returns logs data
```

## Changing the Password

### Local Development
1. Edit `.env` file
2. Update `LOGS_PASSWORD=your-new-password`
3. Restart server: `hypercorn main:app --reload`

### Railway Production
1. Go to Railway dashboard
2. Click on `fast-leads-api` service
3. Go to **Variables** tab
4. Update or add `LOGS_PASSWORD` variable
5. Save (Railway will automatically redeploy)

## Important Notes

### Session Storage
- Sessions are stored **in-memory** on the server
- Restarting the server **clears all active sessions**
- Users will need to log in again after server restart
- For production with multiple servers, consider Redis for session storage

### Security Recommendations
1. **Use a strong password** - Minimum 12 characters with mix of letters, numbers, symbols
2. **Change default password** - Don't use `metrus2025` in production
3. **Use HTTPS** - Always access via `https://` in production
4. **Rotate password** - Change periodically for security
5. **Monitor access** - Check logs for failed auth attempts

### Browser Behavior
- Login once per device/browser
- Closing tab keeps session active
- Clearing cookies requires re-login
- Private/Incognito mode requires new login

## Troubleshooting

### "Invalid password" error
- Check `LOGS_PASSWORD` environment variable is set correctly
- Verify no trailing spaces in password
- Try in a new incognito window to rule out cookie issues

### Session expired after login
- Check server logs for session creation
- Verify clock on server is correct (affects expiry time)
- Try restarting server to clear old sessions

### Can't access after successful login
- Check browser console for JavaScript errors
- Verify cookies are enabled in browser
- Try clearing cookies and logging in again

## Example: Full Login Flow

```bash
# 1. Try to access dashboard without auth
curl -i http://localhost:8000/logs/view
# Response: HTML login page

# 2. Authenticate with password
curl -i -X POST "http://localhost:8000/logs/auth?password=metrus2025" -c cookies.txt
# Response: {"status":"authenticated"}
# Cookie saved to cookies.txt

# 3. Access dashboard with cookie
curl -b cookies.txt http://localhost:8000/logs/view
# Response: Full dashboard HTML

# 4. Access data API with cookie
curl -b cookies.txt http://localhost:8000/logs/data
# Response: JSON logs data
```

## Implementation Details

### Code Location
- **Authentication logic**: `main.py:1283-1333`
- **Session verification**: `main.py:1295-1305`
- **Protected endpoints**: `main.py:1335-1567`

### Session Structure
```python
active_sessions = {
    "secure_token_here": datetime(2025, 11, 16, 13, 0, 0)  # Expiry time
}
```

### Cookie Configuration
```python
response.set_cookie(
    key="logs_session",
    value=token,
    httponly=True,      # JS can't access
    max_age=86400,      # 24 hours
    samesite="strict"   # CSRF protection
)
```

---

**Security Level:** Medium
**Suitable for:** Internal dashboards, development/staging environments
**Not suitable for:** Highly sensitive data without HTTPS

**Deployment Status:** ✅ Ready for Railway deployment
