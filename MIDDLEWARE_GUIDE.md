# 🔒 API Security Middleware Architecture

## Overview
This system acts as a **security gateway** between your frontend and backend API. All requests from the frontend pass through the middleware, which validates them for security threats before forwarding to the actual backend.

## Architecture Flow

```
┌─────────────────┐
│    Frontend     │  (apidashboard)
│  (React App)    │
└────────┬────────┘
         │
         │ Sends request to
         │ /api/proxy/...
         ▼
┌──────────────────────────────────────────┐
│   AI Security Middleware (server.py)     │  Port: 5000
│  ┌──────────────────────────────────────┐│
│  │ 1. Receive Request                   ││
│  │ 2. Extract Data                      ││
│  │ 3. Threat Detection (AI-powered)    ││
│  │    ├─ SQL Injection                  ││
│  │    ├─ Command Injection              ││
│  │    ├─ XSS Attacks                    ││
│  │    ├─ Path Traversal                 ││
│  │    └─ More...                        ││
│  │ 4. Decision                          ││
│  └──────────────────────────────────────┘│
│         │                                 │
│    ┌────┴────────┐                       │
│    │             │                       │
│   YES          NO                        │
│ (SAFE)     (THREAT)                      │
│    │             │                       │
│    ▼             ▼                       │
│ FORWARD      BLOCK                       │
│    │             │                       │
└────┼─────────────┼───────────────────────┘
     │             │
     │ Status:    │ Status:
     │ "success"  │ "blocked"
     │ Code: 200  │ Code: 403
     │             │
     ▼             ▼
 Backend API   Frontend Error
   3000        (User informed)
```

## Setup Instructions

### 1. **Configure Backend URL** (`.env` file)

```env
# Points to your actual RentMate backend (or any backend)
ACTUAL_BACKEND_URL=http://localhost:3000
```

Default: `http://localhost:3000` (for RentMate backend)

### 2. **Start the Middleware**

```powershell
python 'd:\path\to\server.py'
```

Server runs on: `http://localhost:5000`

### 3. **Frontend Configuration**

Instead of calling backend directly:
```javascript
// ❌ DON'T: Call backend directly
fetch('http://localhost:3000/api/users', {...})

// ✅ DO: Call through middleware
fetch('http://localhost:5000/api/proxy/users', {...})
```

## API Proxy Endpoint

### Endpoint: `/api/proxy/<path>`

**Supports:** GET, POST, PUT, DELETE, PATCH

**URL:** `http://localhost:5000/api/proxy/<api_path>`

### Example 1: Get Users (GET Request)

**Frontend Request:**
```javascript
fetch('http://localhost:5000/api/proxy/users?id=123', {
  method: 'GET'
})
.then(res => res.json())
.then(data => {
  if (data.status === 'blocked') {
    console.error('Request blocked:', data.reason);
  } else {
    console.log('Response:', data);
  }
});
```

**Middleware Processing:**
1. Extracts query parameters: `{id: 123}`
2. Runs threat detection on input
3. If safe → Forwards to `http://localhost:3000/api/users?id=123`
4. Returns response from backend

### Example 2: Create User (POST with Threat)

**Frontend Request:**
```javascript
fetch('http://localhost:5000/api/proxy/users', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'John',
    email: 'john@example.com',
    query: "'; DROP TABLE users; --"  // ⚠️ SQL Injection attempt
  })
})
.then(res => res.json());
```

**Middleware Response:**
```json
{
  "status": "blocked",
  "message": "Request blocked: Security threat detected",
  "threat_type": "CRITICAL",
  "threat_details": {
    "type": "SQL_INJECTION",
    "pattern_matched": "DROP TABLE",
    "field": "query"
  },
  "reason": "SQL injection pattern detected"
}
```

**Backend Response:** ❌ NEVER REACHED (request blocked)

### Example 3: Login (POST - Safe Request)

**Frontend Request:**
```javascript
fetch('http://localhost:5000/api/proxy/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'SecurePassword123!'
  })
})
.then(res => res.json());
```

**Middleware Processing:**
1. ✅ Threat check: PASSED
2. 📤 Forwards to backend: `POST http://localhost:3000/api/login`
3. 📥 Receives response: `{token: "...", user: {...}}`
4. Returns to frontend

**Frontend Response:**
```json
{
  "token": "eyJhbGc...",
  "user": {
    "id": "123",
    "email": "user@example.com"
  }
}
```

## Security Threats Detected

The middleware detects and blocks:

| Threat Type | Example | Action |
|------------|---------|--------|
| **SQL Injection** | `'; DROP TABLE users; --` | Block 🛑 |
| **Command Injection** | `; rm -rf /` | Block 🛑 |
| **XSS Attacks** | `<script>alert('xss')</script>` | Block 🛑 |
| **Path Traversal** | `../../etc/passwd` | Block 🛑 |
| **LDAP Injection** | `*)(uid=*))(|(uid=*` | Block 🛑 |
| **Code Injection** | `eval(...)` | Block 🛑 |

## Middleware Console Output

When requests come in, you'll see:

```
🔒 [MIDDLEWARE] POST /api/users
   Request data: {"name":"John","email":"john@example.com"}...
   ✅ Threat check passed
   📤 Forwarding to: http://localhost:3000/api/users
   ✅ Response: 200

🔒 [MIDDLEWARE] POST /api/register
   Request data: {"query":"' OR '1'='1"}...
   ❌ THREAT DETECTED: SQL injection pattern detected
   ❌ Request Blocked (403)
```

## Step-by-Step Setup for RentMate Project

### 1. Start Middleware (Port 5000)
```powershell
cd backend\
python server.py
```

### 2. Update Frontend to Use Middleware
In your React app, change API calls:

```javascript
// Old (directly to backend)
const API_BASE = 'http://localhost:3000/api'

// New (through middleware)
const API_BASE = 'http://localhost:5000/api/proxy'

// Usage stays the same
fetch(`${API_BASE}/users`)
```

### 3. Start Backend (Port 3000)
```powershell
# In RentMate backend directory
npm start  # or node server.js
```

### 4. Start Frontend
```powershell
cd apidashboard\
npm run dev
```

## Complete Request Flow Example

```
User clicks "Create Post" in frontend
           ↓
Frontend calls:
POST http://localhost:5000/api/proxy/posts
{
  "title": "My Post",
  "content": "Hello World"
}
           ↓
Middleware receives request at Port 5000
           ↓
Middleware extracts data:
{
  "title": "My Post",
  "content": "Hello World"
}
           ↓
Threat Detection Analysis:
- Check for injection patterns
- Check for suspicious keywords
- Validate input format
- Result: ✅ SAFE
           ↓
Middleware forwards to backend:
POST http://localhost:3000/api/posts
{
  "title": "My Post",
  "content": "Hello World"
}
           ↓
Backend processes and returns:
{
  "id": "123",
  "title": "My Post",
  "content": "Hello World",
  "createdAt": "2026-04-15T10:00:00Z"
}
           ↓
Middleware forwards response to frontend
           ↓
Frontend displays post
```

## Benefits

✅ **Transparent Security** - Frontend developers don't need to worry about threats
✅ **Centralized Protection** - All requests validated in one place
✅ **AI-Powered** - Groq AI continuously learns attack patterns
✅ **Real-time Blocking** - Threats blocked before reaching backend
✅ **Request Logging** - All requests logged for audit trail
✅ **Easy Integration** - Just change API endpoint URL in frontend

## Troubleshooting

### Backend Service Unavailable
```
❌ Backend unreachable: http://localhost:3000
```
**Solution:** Make sure your actual backend is running on the configured port

### Request Timeout
```
❌ Backend request timeout
```
**Solution:** Backend taking too long. Check if it's healthy.

### Threat False Positive
If legitimate request is blocked:
1. Check the threat_details
2. Possibly adjust input validation
3. Contact admin for whitelist

## Configuration

| Setting | Default | Where | Example |
|---------|---------|-------|---------|
| Middleware Port | 5000 | server.py | N/A |
| Backend URL | `http://localhost:3000` | `.env` | `ACTUAL_BACKEND_URL=http://api.example.com` |
| Threat Mode | Strict | threat_detector.py | Can be relaxed |
| Frontend Port | 5173 | Dev server | `npm run dev` |

---

**This is true middleware behavior: Security-first gateway protecting your APIs!** 🔒
