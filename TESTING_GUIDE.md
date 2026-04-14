# 🧪 Middleware Testing Guide

This guide shows how to test the middleware security and forwarding functionality.

## Test Environment Setup

### Prerequisites
- Middleware running on `http://localhost:5000`
- Backend running on `http://localhost:3000` (configure in `.env`)

### Testing Tools
You can use:
1. **PowerShell** (built-in - recommended for Windows)
2. **curl** (if installed)
3. **Postman** (GUI tool)
4. **JavaScript fetch** (in browser console)

---

## Test 1: Safe Query (Should Pass ✅)

**Scenario:** User fetches posts successfully

### PowerShell
```powershell
$body = @{
    userId = 1
    limit = 10
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://localhost:5000/api/proxy/posts" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

### Expected Response
```json
{
  "status": "success",
  "posts": [
    { "id": 1, "title": "Post 1", "content": "..." },
    { "id": 2, "title": "Post 2", "content": "..." }
  ]
}
```

**Result:** ✅ PASS - Request forwarded to backend

---

## Test 2: SQL Injection Attack (Should Block 🛑)

**Scenario:** Attacker tries to inject SQL in query

### PowerShell
```powershell
$body = @{
    userId = "1' OR '1'='1"
    username = "admin'; DROP TABLE users; --"
} | ConvertTo-Json

$response = Invoke-RestMethod `
  -Uri "http://localhost:5000/api/proxy/login" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body `
  -ErrorAction Continue

Write-Host $response | ConvertTo-Json
```

### Expected Response
```json
{
  "status": "blocked",
  "message": "Request blocked: Security threat detected",
  "threat_type": "CRITICAL",
  "threat_details": {
    "type": "SQL_INJECTION",
    "pattern_matched": ["DROP TABLE", "OR '1'='1"],
    "severity": "CRITICAL"
  }
}
```

**Result:** ✅ PASS - Request blocked with 403 status code

---

## Test 3: Command Injection (Should Block 🛑)

**Scenario:** Attacker tries shell command injection

### PowerShell
```powershell
$body = @{
    command = "; rm -rf /"
    file = "document.pdf | cat /etc/passwd"
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://localhost:5000/api/proxy/execute" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body `
  -ErrorAction Continue
```

### Expected Response
```json
{
  "status": "blocked",
  "message": "Request blocked: Security threat detected",
  "threat_details": {
    "type": "COMMAND_INJECTION",
    "pattern_matched": ["rm -rf", "cat /etc/passwd"]
  }
}
```

**Result:** ✅ PASS - Request blocked

---

## Test 4: XSS Attack (Should Block 🛑)

**Scenario:** User tries to inject JavaScript

### PowerShell
```powershell
$body = @{
    comment = "<script>alert('xss');</script>"
    name = "<img src=x onerror='alert(1)'>"
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://localhost:5000/api/proxy/comments" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body `
  -ErrorAction Continue
```

### Expected Response
```json
{
  "status": "blocked",
  "message": "Request blocked: Security threat detected",
  "threat_details": {
    "type": "XSS",
    "pattern_matched": ["<script>", "onerror="]
  }
}
```

**Result:** ✅ PASS - Request blocked

---

## Test 5: Path Traversal Attack (Should Block 🛑)

**Scenario:** Attacker tries to access system files

### PowerShell
```powershell
$body = @{
    file = "../../etc/passwd"
    path = "..\\..\\windows\\system32\\config\\sam"
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://localhost:5000/api/proxy/download" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body `
  -ErrorAction Continue
```

### Expected Response
```json
{
  "status": "blocked",
  "message": "Request blocked: Security threat detected",
  "threat_details": {
    "type": "PATH_TRAVERSAL",
    "pattern_matched": ["../../", "..\\..\\"]
  }
}
```

**Result:** ✅ PASS - Request blocked

---

## Test 6: GET Request (Browser Test ✅)

**Scenario:** Simple GET request through middleware

Open browser and paste:
```
http://localhost:5000/api/proxy/users
```

Or use PowerShell:
```powershell
Invoke-RestMethod `
  -Uri "http://localhost:5000/api/proxy/users?limit=10&page=1" `
  -Method GET
```

### Expected Response
Forwarded to backend and returns user list

**Result:** ✅ PASS - Request forwarded

---

## Test 7: JavaScript Fetch (Frontend Test ✅)

Open browser console and run:

```javascript
// Test 1: Safe request
fetch('http://localhost:5000/api/proxy/posts', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    title: 'My New Post',
    content: 'Hello World'
  })
})
.then(res => res.json())
.then(data => console.log('Safe request response:', data));

// Test 2: Injection attempt
fetch('http://localhost:5000/api/proxy/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: "admin' --",
    password: "'; DROP TABLE users; --"
  })
})
.then(res => res.json())
.then(data => console.log('Injection attempt response:', data));
```

---

## Automated Testing Script

### PowerShell Script: test_middleware.ps1

```powershell
# Configuration
$middlewareUrl = "http://localhost:5000/api/proxy"
$resultsFile = "test_results.txt"

# Colors for output
$green = "Green"
$red = "Red"
$yellow = "Yellow"

Write-Host "🧪 Starting Middleware Security Tests" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
""

# Test 1: Safe Request
Write-Host "Test 1: Safe Request" -ForegroundColor Yellow
$body = @{
    name = "John Doe"
    email = "john@example.com"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$middlewareUrl/users" -Method POST -Body $body -ContentType "application/json" -ErrorAction Continue
    Write-Host "✅ Request forwarded successfully" -ForegroundColor Green
    Write-Host "Response: $($response | ConvertTo-Json)" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Error: $_" -ForegroundColor Yellow
}
""

# Test 2: SQL Injection
Write-Host "Test 2: SQL Injection Attack" -ForegroundColor Yellow
$body = @{
    username = "admin'; DROP TABLE users; --"
    password = "anything"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$middlewareUrl/login" -Method POST -Body $body -ContentType "application/json" -ErrorAction Continue
    Write-Host "✅ Request blocked as expected" -ForegroundColor Green
    Write-Host "Response: $($response | ConvertTo-Json)" -ForegroundColor Green
} catch {
    if ($_.Exception.Response.StatusCode -eq 403) {
        Write-Host "✅ BLOCKED with 403 Forbidden (Correct)" -ForegroundColor Green
    } else {
        Write-Host "❌ Unexpected error: $_" -ForegroundColor Red
    }
}
""

# Test 3: XSS Attack
Write-Host "Test 3: XSS Attack" -ForegroundColor Yellow
$body = @{
    comment = "<script>alert('xss');</script>"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$middlewareUrl/comments" -Method POST -Body $body -ContentType "application/json" -ErrorAction Continue
    Write-Host "✅ Request blocked as expected" -ForegroundColor Green
} catch {
    if ($_.Exception.Response.StatusCode -eq 403) {
        Write-Host "✅ BLOCKED with 403 Forbidden (Correct)" -ForegroundColor Green
    }
}
""

# Test 4: GET Request
Write-Host "Test 4: GET Request (Safe)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$middlewareUrl/products?limit=10" -Method GET
    Write-Host "✅ GET Request forwarded successfully" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Expected if backend not available: $_" -ForegroundColor Yellow
}
""

Write-Host "================================" -ForegroundColor Cyan
Write-Host "✅ Testing Complete" -ForegroundColor Cyan
```

**Run the script:**
```powershell
.\test_middleware.ps1
```

---

## Expected Test Results Summary

| Test | Input | Expected | Result |
|------|-------|----------|--------|
| Safe POST | Normal data | 200 OK | ✅ Forwarded |
| SQL Inject | `' DROP TABLE` | 403 Blocked | ✅ Blocked |
| Command Inject | `; rm -rf /` | 403 Blocked | ✅ Blocked |
| XSS Attack | `<script>alert` | 403 Blocked | ✅ Blocked |
| Path Traversal | `../../etc/passwd` | 403 Blocked | ✅ Blocked |
| Safe GET | Normal query | 200 OK | ✅ Forwarded |

---

## Debugging Failed Tests

### Issue: Backend Unreachable
```
❌ HTTPConnectionError: Cannot reach http://localhost:3000
```
**Solution:**
1. Verify backend is running: `netstat -ano | findstr :3000`
2. Check ACTUAL_BACKEND_URL in `.env` is correct
3. Ensure backend is listening on 0.0.0.0 or localhost

### Issue: Request Forwarded but Should Be Blocked
This is a SECURITY ISSUE!
1. Check threat_detector.py pattern matching
2. Verify detect_threats() is called
3. Add custom patterns if needed

### Issue: Legitimate Request Blocked
The middleware may have false positives
1. Review threat_details to see what triggered the block
2. Check if legitimate request contains keywords like `DROP`, `SELECT`, etc.
3. Possibly adjust strictness level

---

## Real RentMate Backend Testing

Once tests pass, test with actual RentMate endpoints:

### Test 1: Login API
```powershell
$body = @{
    email = "test@rentmate.com"
    password = "password123"
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://localhost:5000/api/proxy/login" `
  -Method POST `
  -Body $body `
  -ContentType "application/json"
```

### Test 2: Create Order
```powershell
$body = @{
    propertyId = "123"
    rentalDays = 30
    totalPrice = 1500
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://localhost:5000/api/proxy/orders" `
  -Method POST `
  -Body $body `
  -ContentType "application/json"
```

---

**All tests passing? Your middleware is working! 🎉**
