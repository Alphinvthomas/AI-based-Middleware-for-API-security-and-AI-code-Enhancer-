# GitHub-Integrated API Security Middleware - Setup Guide

## Overview

The AI Security Middleware has been upgraded to:
1. **Fetch APIs directly from GitHub** instead of local servers
2. **Auto-discover APIs** by analyzing entire project code
3. **Detect input threats** for all API parameters
4. **Work with any project** without local configuration needed

## New Architecture

```
┌─────────────────┐
│   GitHub Repo   │
│   (Any Project) │
└────────┬────────┘
         │
         ▼
┌──────────────────────────────────────────────┐
│  GitHub Integration (github_integration.py)   │
│  - Fetch files from GitHub                    │
│  - List all Python files                      │
│  - Get repository metadata                    │
└────────┬─────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────┐
│  API Analyzer (api_analyzer.py)              │
│  - Parse Python AST                          │
│  - Discover APIs automatically               │
│  - Extract parameters                        │
│  - Identify HTTP methods                     │
└────────┬─────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────┐
│  Threat Detector (threat_detector.py)        │
│  - SQL Injection detection                   │
│  - Command Injection detection               │
│  - Path Traversal detection                  │
│  - XSS detection                             │
│  - Code Injection detection                  │
│  - LDAP Injection detection                  │
└────────┬─────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────┐
│  Security Analyzer (server.py)               │
│  - Groq AI Security Scoring                  │
│  - Secure Code Suggestions                   │
│  - Input Validation                          │
└─────────────────────────────────────────────┘
```

## New Modules

### 1. `github_integration.py`
Handles all GitHub interactions.

**Key Classes:**
- `GitHubIntegration`: Main class for GitHub API interactions

**Key Methods:**
- `get_file_content(file_path)`: Get file content from GitHub
- `get_directory_contents(path)`: Get directory listing
- `get_all_python_files(directory)`: Recursively get all Python files
- `get_repository_structure()`: Get repo metadata
- `save_file_locally(file_path, local_path)`: Download and save file

**Example Usage:**
```python
from github_integration import GitHubIntegration

github = GitHubIntegration("facebook", "react")
python_files = github.get_all_python_files()
content = github.get_file_content("src/main.py")
```

### 2. `api_analyzer.py`
Analyzes Python code to discover APIs using AST parsing.

**Key Classes:**
- `APIAnalyzer`: Discovers APIs in code
- `DiscoveredAPI`: Dataclass representing an API
- `APIParameter`: Dataclass representing API parameter

**Key Methods:**
- `analyze_file(file_path, content)`: Analyze a single file
- `discover_apis_in_project(file_contents)`: Analyze entire project
- `get_api_summary()`: Get summary of discovered APIs
- `get_api_by_name(api_name)`: Find API by name

**Discovers:**
- FastAPI routes (@app.get, @app.post, etc.)
- Flask routes (@app.route)
- Function parameters and type hints
- HTTP methods
- Docstrings

**Example Usage:**
```python
from api_analyzer import APIAnalyzer

analyzer = APIAnalyzer()
apis = analyzer.discover_apis_in_project(file_contents)
for api in apis:
    print(f"{api.http_method} {api.endpoint}")
```

### 3. `threat_detector.py`
Detects security threats in input data.

**Key Classes:**
- `ThreatDetector`: Threat analysis engine
- `ThreatLevel`: Enum for threat severity
- `ThreatDetectedError`: Exception for detected threats

**Key Methods:**
- `analyze_input(input_data)`: Scan input for threats
- `check_file_path(file_path)`: Validate file paths

**Detects:**
- SQL Injection (UNION SELECT, OR, DROP, etc.)
- Command Injection (shell metacharacters, pipes, etc.)
- Path Traversal (../, ..\\, %2e%2e, etc.)
- Cross-Site Scripting (XSS) (script tags, event handlers, etc.)
- LDAP Injection (LDAP operators, filters)
- Code Injection (eval, exec, __import__, etc.)
- Suspicious Keywords

**Threat Levels:**
- `CRITICAL`: SQL/Command/Path Traversal/Code Injection
- `HIGH`: XSS/LDAP Injection
- `MEDIUM`: Suspicious Keywords
- `LOW`: Low-risk patterns
- `SAFE`: No threats detected

**Example Usage:**
```python
from threat_detector import ThreatDetector

detector = ThreatDetector(strict_mode=True)
is_safe, threat_level, threats = detector.analyze_input(user_input)

if not is_safe:
    print(f"🚨 Threat detected: {threat_level.value}")
    for threat in threats:
        print(f"  - {threat['type']}: {threat['sample']}")
```

## Environment Configuration

Create a `.env` file in `main_application/backend/`:

```env
# Groq API Key (for security analysis)
GROQ_API_KEY=your_groq_api_key_here

# GitHub Authentication (optional, increases rate limits)
GITHUB_TOKEN=your_github_token_here

# Default GitHub Repository (optional fallback)
GITHUB_REPO_OWNER=username
GITHUB_REPO_NAME=repository_name
```

## API Endpoints

### 1. Health Check
```bash
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "AI Security Middleware with GitHub Integration",
  "github_connected": false,
  "apis_discovered": 0
}
```

### 2. Connect to GitHub Repository
```bash
POST /api/github/connect
Content-Type: application/json

{
  "owner": "torvalds",
  "repo_name": "linux"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Connected to GitHub repository",
  "repository": {
    "name": "linux",
    "description": "Linux kernel source code",
    "url": "https://github.com/torvalds/linux",
    "language": "C",
    "topics": ["kernel", "linux"]
  }
}
```

### 3. Discover APIs from Repository
```bash
POST /api/discover
Content-Type: application/json

{
  "owner": "pallets",
  "repo_name": "flask"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Discovered 45 APIs",
  "repository": "pallets/flask",
  "total_apis": 45,
  "apis_by_method": {
    "GET": ["/hello", "/users"],
    "POST": ["/create", "/login"],
    "PUT": ["/update"],
    "DELETE": ["/remove"]
  },
  "apis": [
    {
      "name": "hello_world",
      "function_name": "hello_world",
      "endpoint": "/hello",
      "http_method": "GET",
      "file_path": "examples/hello.py",
      "parameters": [],
      "security_score": 85,
      "status": "Active"
    }
  ]
}
```

### 4. List Discovered APIs
```bash
GET /api/list?owner=pallets&repo_name=flask
```

### 5. Analyze Specific API
```bash
GET /api/analyze/hello_world
```

or with POST for input validation:

```bash
POST /api/analyze/hello_world
Content-Type: application/json

{
  "test": "data"
}
```

**Response:**
```json
{
  "api_name": "hello_world",
  "function_name": "hello_world",
  "endpoint": "/hello",
  "http_method": "GET",
  "file_path": "examples/hello.py",
  "source_code": "def hello_world():\n    return {'message': 'Hello World'}",
  "parameters": [],
  "security_score": 85,
  "suggested_code": null,
  "suggested_dependencies": [],
  "needs_improvement": false,
  "severity": "Low"
}
```

### 6. Analyze Input for Threats
```bash
POST /api/analyze-input
Content-Type: application/json

{
  "data": "SELECT * FROM users WHERE id = 1 OR '1'='1'"
}
```

**Response:**
```json
{
  "is_safe": false,
  "threat_level": "CRITICAL",
  "threats_count": 2,
  "threats": [
    {
      "type": "SQL_INJECTION",
      "level": "CRITICAL",
      "pattern": "(\\bUNION\\b.*\\bSELECT\\b)",
      "sample": "SELECT * FROM users WHERE id = 1 OR '1'='1'"
    }
  ]
}
```

### 7. Validate Request
```bash
POST /api/validate-request
Content-Type: application/json

{
  "username": "john",
  "query": "SELECT * FROM users"
}
```

**Response - Safe:**
```json
{
  "valid": true,
  "message": "Request is safe to process"
}
```

**Response - Threat Detected:**
```json
{
  "valid": false,
  "message": "🚨 SECURITY THREAT DETECTED (CRITICAL): Operation blocked",
  "details": {
    "threat_level": "CRITICAL",
    "threats_detected": 1,
    "threat_list": [
      {
        "type": "SQL_INJECTION",
        "level": "CRITICAL",
        "sample": "SELECT * FROM users"
      }
    ]
  }
}
```

### 8. Batch Analyze Multiple APIs
```bash
POST /api/batch-analyze
Content-Type: application/json

{
  "api_names": ["get_user", "create_post", "delete_comment"]
}
```

**Response:**
```json
{
  "total_analyzed": 3,
  "analyses": [
    {
      "api_name": "get_user",
      "endpoint": "/users",
      "security_score": 78,
      "needs_improvement": false
    },
    {
      "api_name": "create_post",
      "endpoint": "/posts",
      "security_score": 65,
      "needs_improvement": true
    },
    {
      "api_name": "delete_comment",
      "endpoint": "/comments",
      "security_score": 42,
      "needs_improvement": true
    }
  ]
}
```

## Setup Instructions

### 1. Install Dependencies
```bash
cd main_application/backend
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Create .env file
echo "GROQ_API_KEY=your_key_here" > .env
echo "GITHUB_TOKEN=your_token_here" >> .env
```

### 3. Start the Server
```bash
python server.py
```

**Output:**
```
📦 GitHub Repo: default_owner/default_repo
🚀 Starting AI Security Middleware with GitHub Integration
📍 Server running on: http://localhost:5000
🔍 Endpoints:
   - POST /api/github/connect - Connect to GitHub repo
   - POST /api/discover - Discover APIs from GitHub
   - GET /api/list - List discovered APIs
   - GET/POST /api/analyze/<api_name> - Analyze specific API
   - POST /api/analyze-input - Check input for threats
   - POST /api/validate-request - Validate request
   - GET /api/health - Health check
```

## Usage Examples

### Example 1: Analyze a Public GitHub Repository

```bash
# Connect to repository
curl -X POST http://localhost:5000/api/discover \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "pallets",
    "repo_name": "flask"
  }'

# Analyze specific API
curl http://localhost:5000/api/analyze/hello_world

# Check input for threats
curl -X POST http://localhost:5000/api/analyze-input \
  -H "Content-Type: application/json" \
  -d '{
    "data": "admin; DROP TABLE users;--"
  }'
```

### Example 2: Batch Analysis

```bash
curl -X POST http://localhost:5000/api/batch-analyze \
  -H "Content-Type: application/json" \
  -d '{
    "api_names": ["get_user", "create_post", "delete_item"]
  }'
```

### Example 3: Check Before Processing

```python
import requests

# Validate user input before processing
user_input = request.form.get("search_query")

response = requests.post(
    "http://localhost:5000/api/analyze-input",
    json={"data": user_input}
)

data = response.json()
if not data["is_safe"]:
    print(f"🚨 Suspicious input detected: {data['threat_level']}")
    # Block the operation
else:
    print("✅ Input is safe to process")
    # Process the request
```

## Key Features

### 🔐 Security Threat Detection
- SQL Injection
- Command Injection
- Path Traversal
- XSS (Cross-Site Scripting)
- LDAP Injection
- Code Injection
- Suspicious Keywords

### 🔍 API Discovery
- Automatic detection of FastAPI routes
- Flask route discovery
- Parameter extraction
- HTTP method identification
- Docstring capture

### 🤖 AI-Powered Analysis
- Groq AI security scoring (0-100)
- Automated secure code suggestions
- Vulnerability recommendations
- Severity classification

### 🌍 GitHub Integration
- Works with any GitHub repository
- Public and private repo support (with token)
- Recursive directory traversal
- Efficient caching

### ⚡ Input Validation
- Pre-request threat detection
- Operation blocking on threats
- Detailed threat reporting
- Configurable threat levels

## Threat Detection Examples

### SQL Injection Detected
```json
{
  "is_safe": false,
  "threat_level": "CRITICAL",
  "threats": [
    {
      "type": "SQL_INJECTION",
      "pattern": "UNION.*SELECT",
      "sample": "SELECT * FROM users UNION SELECT password FROM admin"
    }
  ]
}
```

### Command Injection Detected
```json
{
  "is_safe": false,
  "threat_level": "CRITICAL",
  "threats": [
    {
      "type": "COMMAND_INJECTION",
      "pattern": "shell metacharacters",
      "sample": "user; rm -rf /"
    }
  ]
}
```

### Path Traversal Detected
```json
{
  "is_safe": false,
  "threat_level": "CRITICAL",
  "threats": [
    {
      "type": "PATH_TRAVERSAL",
      "pattern": "../",
      "sample": "../../../../etc/passwd"
    }
  ]
}
```

## Troubleshooting

### GitHub Authentication Issues
- Ensure `GITHUB_TOKEN` is set in `.env` for private repos
- Check token permissions: `repo`, `read:org`
- Verify owner and repo name are correct

### API Discovery Issues
- Ensure repository contains Python files (.py)
- Check for syntax errors in Python files (will be skipped)
- Verify sufficient rate limits with GitHub

### Threat Detection False Positives
- Disable strict mode if needed: `ThreatDetector(strict_mode=False)`
- Customize patterns in `threat_detector.py` if needed

### Groq API Issues
- Verify `GROQ_API_KEY` is set correctly
- Check Groq API status and rate limits
- Ensure sufficient API credits

## Performance Optimization

### Caching
- APIs are cached after discovery
- File contents are cached to avoid re-downloading
- Use `GET /api/list` for cached APIs

### Rate Limiting
- GitHub: 60 requests/hour (unauthenticated), 5000/hour (authenticated)
- Groq API: Check your plan limits
- Consider caching results for frequently analyzed APIs

## Security Best Practices

1. **Keep tokens secure**: Never commit `.env` to repository
2. **Use environment variables**: Store secrets in environment, not code
3. **Validate before processing**: Always check input with `/api/analyze-input`
4. **Review suggestions**: AI suggestions should be reviewed by humans
5. **Monitor threats**: Log all detected threats for security auditing
6. **Update regularly**: Keep threat patterns up to date

## Future Enhancements

- [ ] Webhook support for real-time analysis
- [ ] Database logging of threats
- [ ] Advanced ML-based threat detection
- [ ] Multi-language support (JavaScript, Go, Rust, etc.)
- [ ] CI/CD pipeline integration
- [ ] Threat pattern customization UI
- [ ] Batch repository analysis
- [ ] Comparative security scoring

## Support

For issues or questions:
1. Check logs for error messages
2. Verify all environment variables are set
3. Test endpoints with curl or Postman
4. Review code comments in each module
5. Check GitHub and Groq API status pages
