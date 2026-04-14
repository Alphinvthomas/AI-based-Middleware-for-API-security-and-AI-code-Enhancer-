"""
AI Security Middleware Server
Fetches APIs from GitHub, analyzes them, and detects input threats
"""
import os
import sys
import re
from typing import Optional, Dict, List
from pathlib import Path

# Load environment variables from root .env file FIRST
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    with open(env_path, 'r', encoding='utf-8-sig') as f:  # utf-8-sig removes BOM
        for line in f:
            line = line.strip()
            if line and '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                key = key.strip().replace('\ufeff', '')  # Remove any BOM characters
                value = value.strip()
                if key:
                    os.environ[key] = value
    print(f"✅ Loaded environment from {env_path}")

from flask import Flask, jsonify, request
from flask_cors import CORS

from github_integration import GitHubIntegration
from api_analyzer import APIAnalyzer, DiscoveredAPI
from threat_detector import ThreatDetector, ThreatLevel, ThreatDetectedError

# ================================================================================
# Configuration
# ================================================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO_OWNER = os.getenv("GITHUB_REPO_OWNER", "default_owner")
GITHUB_REPO_NAME = os.getenv("GITHUB_REPO_NAME", "default_repo")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME = "llama-3.1-8b-instant"

# ================================================================================
# Middleware Configuration
# ================================================================================
# URL of the actual backend API (e.g., RentMate backend)
ACTUAL_BACKEND_URL = os.getenv("ACTUAL_BACKEND_URL", "http://localhost:3000")

print(f"🔗 Actual Backend: {ACTUAL_BACKEND_URL}")

app = Flask(__name__)
CORS(app)

# Global state
github_client = None
api_analyzer = APIAnalyzer()
threat_detector = ThreatDetector(strict_mode=True)
cached_apis: List[DiscoveredAPI] = []
cached_file_contents: Dict[str, str] = {}


# ================================================================================
# GitHub and API Discovery Functions
# ================================================================================

def initialize_github_client(owner: str, repo_name: str) -> Optional[GitHubIntegration]:
    """
    Initialize GitHub integration client
    
    Args:
        owner: Repository owner
        repo_name: Repository name
        
    Returns:
        GitHubIntegration instance or None if failed
    """
    try:
        client = GitHubIntegration(owner, repo_name)
        repo_info = client.get_repository_structure()
        if repo_info:
            print(f"✅ Connected to GitHub repo: {owner}/{repo_name}")
            return client
        else:
            print(f"❌ Failed to access GitHub repo: {owner}/{repo_name}")
            return None
    except Exception as e:
        print(f"❌ GitHub initialization error: {e}")
        return None


def discover_apis_from_github(owner: str, repo_name: str) -> List[DiscoveredAPI]:
    """
    Discover APIs from GitHub repository (all supported languages)
    
    Args:
        owner: Repository owner
        repo_name: Repository name
        
    Returns:
        List of discovered APIs
    """
    global github_client, cached_apis, cached_file_contents
    
    try:
        # Initialize client if not already done
        if github_client is None or github_client.repo_owner != owner or github_client.repo_name != repo_name:
            github_client = initialize_github_client(owner, repo_name)
        
        if github_client is None:
            print("❌ GitHub client not initialized")
            return []
        
        # Get all code files from the repository (all supported languages)
        print("📂 Fetching code files from GitHub...")
        code_files = github_client.get_all_code_files()
        
        if not code_files:
            print("⚠️ No code files found in repository")
            return []
        
        print(f"📄 Found {len(code_files)} code files")
        
        # Fetch file contents
        cached_file_contents = {}
        for file_path in code_files:
            content = github_client.get_file_content(file_path)
            if content:
                cached_file_contents[file_path] = content
        
        print(f"✅ Fetched {len(cached_file_contents)} files with content")
        
        # Analyze files for APIs
        print("🔍 Analyzing files for APIs...")
        cached_apis = api_analyzer.discover_apis_in_project(cached_file_contents)
        
        print(f"✨ Discovered {len(cached_apis)} APIs")
        
        return cached_apis
    
    except Exception as e:
        print(f"❌ Error discovering APIs: {e}")
        return []


def get_api_source_code(api_name: str) -> Optional[str]:
    """
    Get source code of a specific API
    
    Args:
        api_name: API name or endpoint
        
    Returns:
        Source code or None if not found
    """
    api = api_analyzer.get_api_by_name(api_name)
    if api:
        return api.source_code
    return None


# ================================================================================
# Input Validation and Threat Detection
# ================================================================================

def validate_request_input(data: Dict) -> tuple[bool, str, Dict]:
    """
    Validate and check request input for threats
    
    Args:
        data: Request data
        
    Returns:
        Tuple of (is_safe, message, details)
    """
    if not data:
        return True, "No data to validate", {}
    
    try:
        is_safe, threat_level, threats = threat_detector.analyze_input(data)
        
        if not is_safe:
            threat_details = {
                "threat_level": threat_level.value,
                "threats_detected": len(threats),
                "threat_list": threats[:5]  # Return top 5 threats
            }
            
            message = f"🚨 SECURITY THREAT DETECTED ({threat_level.value}): Operation blocked"
            
            return False, message, threat_details
        
        return True, "Input validation passed", {}
    
    except Exception as e:
        return False, f"Validation error: {str(e)}", {}


# ================================================================================
# Security Analysis Functions
# ================================================================================

def extract_score(text: str) -> int:
    """Extract numeric score from text"""
    match = re.search(r'\d+', text)
    if match:
        return int(match.group())
    return 0


def get_security_score(source_code: str) -> Optional[int]:
    """
    Get security score from LLM
    
    Args:
        source_code: Code to analyze
        
    Returns:
        Security score (0-100) or None if failed
    """
    try:
        # If no API key, return default score based on code analysis
        if not GROQ_API_KEY:
            print("⚠️ GROQ_API_KEY not set, using default scoring")
            # Simple heuristic scoring when API key unavailable
            if len(source_code) < 50:
                return 50
            if "password" in source_code.lower() and "input" in source_code.lower():
                return 40
            if "sql" in source_code.lower() and "format" in source_code.lower():
                return 35
            return 60  # Default moderate score
        
        import requests
        
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""You are a cybersecurity expert.
Analyze the following API source code and give a security score from 1 to 100.
Only return a number.

Code:
{source_code}"""
        
        payload = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0
        }
        
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            score_text = result["choices"][0]["message"]["content"]
            return extract_score(score_text)
        else:
            print(f"Score API Error: {response.status_code}")
            return 60  # Return default score on API error
    
    except Exception as e:
        print(f"Error getting security score: {e}")
        return 60  # Return default score on exception


def get_secure_code_suggestion(source_code: str, api_name: Optional[str] = None) -> Dict:
    """
    Generate secure code suggestion
    
    Args:
        source_code: Original code
        api_name: API name for context
        
    Returns:
        Dict with suggested code and dependencies
    """
    try:
        import requests
        
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""You are a senior backend security engineer.
Analyze the following API function and rewrite it to be secure.

API NAME: {api_name if api_name else "Unknown"}

Original Code:
{source_code}

Generate the SECURE version of this function:
- Add input validation
- Add error handling
- Add authentication check
- Implement proper authorization
- Use parameterized queries if using databases
- Add rate limiting
- Use environment variables for secrets
- Output ONLY valid Python code

Code must be production-ready and secure."""
        
        payload = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        }
        
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            return {"code": content, "dependencies": []}
        else:
            print(f"Error generating secure code: {response.status_code}")
            return {"code": "Secure code generation failed.", "dependencies": []}
    
    except Exception as e:
        print(f"Error generating secure code: {e}")
        return {"code": f"Error: {str(e)}", "dependencies": []}


# ================================================================================
# API Endpoints
# ================================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "AI Security Middleware with GitHub Integration",
        "github_connected": github_client is not None,
        "apis_discovered": len(cached_apis)
    }), 200


@app.route('/api/github/connect', methods=['POST'])
def connect_github():
    """
    Connect to GitHub repository
    
    Request body:
    {
        "owner": "github_username",
        "repo_name": "repository_name"
    }
    """
    try:
        data = request.get_json()
        
        # Validate input
        is_safe, message, details = validate_request_input(data)
        if not is_safe:
            return jsonify({"error": message, "details": details}), 400
        
        owner = data.get("owner", GITHUB_REPO_OWNER)
        repo_name = data.get("repo_name", GITHUB_REPO_NAME)
        
        # Initialize GitHub client
        global github_client
        github_client = initialize_github_client(owner, repo_name)
        
        if github_client is None:
            return jsonify({
                "error": f"Failed to connect to repository {owner}/{repo_name}"
            }), 400
        
        repo_info = github_client.get_repository_structure()
        
        return jsonify({
            "status": "success",
            "message": "Connected to GitHub repository",
            "repository": repo_info
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/discover', methods=['POST'])
def discover_apis():
    """
    Discover APIs from GitHub repository
    
    Request body:
    {
        "owner": "github_username",
        "repo_name": "repository_name"
    }
    """
    try:
        data = request.get_json() if request.get_json() else {}
        
        # Validate input
        is_safe, message, details = validate_request_input(data)
        if not is_safe:
            return jsonify({"error": message, "details": details}), 400
        
        owner = data.get("owner", GITHUB_REPO_OWNER)
        repo_name = data.get("repo_name", GITHUB_REPO_NAME)
        
        print(f"\n🔄 Discovering APIs from {owner}/{repo_name}...")
        
        # Discover APIs
        apis = discover_apis_from_github(owner, repo_name)
        
        if not apis:
            return jsonify({
                "message": "No APIs found in repository",
                "apis": []
            }), 200
        
        # Analyze each API
        api_list = []
        for api in apis:
            score = get_security_score(api.source_code)
            
            api_list.append({
                "name": api.name,
                "function_name": api.function_name,
                "endpoint": api.endpoint,
                "http_method": api.http_method,
                "language": api.language,
                "framework": api.framework,
                "file_path": api.file_path,
                "parameters": [
                    {
                        "name": p.name,
                        "type": p.type_hint,
                    } for p in api.parameters
                ],
                "security_score": score if score else 0,
                "status": "Active" if score and score >= 60 else "Danger"
            })
        
        summary = api_analyzer.get_api_summary()
        
        return jsonify({
            "status": "success",
            "message": f"Discovered {len(apis)} APIs",
            "repository": f"{owner}/{repo_name}",
            "total_apis": len(apis),
            "apis_by_method": summary.get("apis_by_method"),
            "apis_by_language": summary.get("apis_by_language"),
            "apis_by_framework": summary.get("apis_by_framework"),
            "language_statistics": summary.get("language_statistics"),
            "apis": api_list
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/list', methods=['GET'])
def list_apis():
    """
    List all discovered APIs
    
    Optionally specify an owner and repo_name to discover from GitHub
    Query parameters:
    - owner: Repository owner (optional)
    - repo_name: Repository name (optional)
    """
    try:
        owner = request.args.get("owner")
        repo_name = request.args.get("repo_name")
        
        # If owner and repo specified, discover APIs first
        if owner and repo_name:
            apis = discover_apis_from_github(owner, repo_name)
        else:
            apis = cached_apis
        
        if not apis:
            return jsonify({"apis": []}), 200
        
        api_list = []
        for api in apis:
            score = get_security_score(api.source_code)
            api_list.append({
                "name": api.name,
                "endpoint": api.endpoint,
                "http_method": api.http_method,
                "language": api.language,
                "framework": api.framework,
                "file_path": api.file_path,
                "security_score": score if score else 0,
                "status": "Active" if score and score >= 60 else "Danger",
                "parameters": [
                    {"name": p.name, "type": p.type_hint}
                    for p in api.parameters
                ]
            })
        
        return jsonify({
            "total_apis": len(api_list),
            "apis": api_list
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/analyze/<api_name>', methods=['GET', 'POST'])
def analyze_api(api_name):
    """
    Analyze an API for security vulnerabilities
    
    Returns:
    {
        "api_name": str,
        "endpoint": str,
        "source_code": str,
        "security_score": int (0-100),
        "parameters": list,
        "suggested_code": str (if score < 70),
        "needs_improvement": bool
    }
    """
    try:
        # Validate input
        if request.method == 'POST':
            data = request.get_json() if request.get_json() else {}
            is_safe, message, details = validate_request_input(data)
            if not is_safe:
                return jsonify({"error": message, "details": details}), 400
        
        # Find the API
        api = api_analyzer.get_api_by_name(api_name)
        
        if not api:
            return jsonify({
                "error": f"API '{api_name}' not found. Total APIs: {len(cached_apis)}"
            }), 404
        
        # Get security score
        score = get_security_score(api.source_code)
        if score is None:
            score = 60  # Default fallback score
        
        # Generate suggested code if score is low
        suggested_code = None
        suggested_dependencies = []
        if score < 70:
            result = get_secure_code_suggestion(api.source_code, api_name)
            suggested_code = result.get("code", "")
            suggested_dependencies = result.get("dependencies", [])
        
        return jsonify({
            "api_name": api.name,
            "function_name": api.function_name,
            "endpoint": api.endpoint,
            "http_method": api.http_method,
            "file_path": api.file_path,
            "source_code": api.source_code,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type_hint,
                } for p in api.parameters
            ],
            "security_score": score,
            "suggested_code": suggested_code,
            "suggested_dependencies": suggested_dependencies,
            "needs_improvement": score < 70,
            "severity": (
                "Critical" if score < 50 else
                "High" if score < 70 else
                "Medium" if score < 85 else
                "Low"
            )
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/analyze-input', methods=['POST'])
def analyze_input_data():
    """
    Check input data for security threats
    
    Request body:
    {
        "data": any (string, dict, list, etc)
    }
    """
    try:
        json_data = request.get_json()
        if not json_data:
            return jsonify({"error": "No data provided"}), 400
        
        input_data = json_data.get("data")
        
        is_safe, threat_level, threats = threat_detector.analyze_input(input_data)
        
        return jsonify({
            "is_safe": is_safe,
            "threat_level": threat_level.value,
            "threats_count": len(threats),
            "threats": threats[:10]  # Return top 10 threats
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/validate-request', methods=['POST'])
def validate_request():
    """
    Validate entire request for threats
    
    Request body can be anything - will be scanned for security threats
    """
    try:
        data = request.get_json() if request.get_json() else {}
        
        is_safe, message, details = validate_request_input(data)
        
        if is_safe:
            return jsonify({
                "valid": True,
                "message": "Request is safe to process"
            }), 200
        else:
            return jsonify({
                "valid": False,
                "message": message,
                "details": details
            }), 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/batch-analyze', methods=['POST'])
def batch_analyze():
    """
    Analyze multiple APIs at once
    
    Request body:
    {
        "api_names": ["login", "user", "payment"]
    }
    """
    try:
        data = request.get_json()
        
        # Validate input
        is_safe, message, details = validate_request_input(data)
        if not is_safe:
            return jsonify({"error": message, "details": details}), 400
        
        api_names = data.get("api_names", [])
        
        results = []
        for api_name in api_names:
            api = api_analyzer.get_api_by_name(api_name)
            if api:
                source_code = api.source_code
                score = get_security_score(source_code)
                
                results.append({
                    "api_name": api_name,
                    "endpoint": api.endpoint,
                    "security_score": score,
                    "needs_improvement": score < 70 if score else False
                })
        
        return jsonify({
            "total_analyzed": len(results),
            "analyses": results
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================================================================================
# Error Handlers
# ================================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


# ================================================================================
# API Request Middleware - Intercepts and Validates Requests
# ================================================================================

@app.route('/api/proxy/<path:api_path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def api_proxy(api_path):
    """
    Middleware that intercepts all API requests
    
    1. Validates request data for security threats
    2. Blocks requests with detected threats
    3. Forwards safe requests to actual backend
    4. Returns backend response to frontend
    
    Request body (for POST/PUT):
    {
        "data": {...request data...}
    }
    
    Response:
    {
        "status": "success" or "blocked",
        "message": "description",
        "data": {...response from backend...} (if success)
        "threat_details": {...} (if blocked)
    }
    """
    try:
        # Extract request data
        request_data = {}
        if request.method in ['POST', 'PUT']:
            request_data = request.get_json() if request.get_json() else {}
        elif request.method == 'GET':
            request_data = request.args.to_dict()
        
        print(f"\n🔒 [MIDDLEWARE] {request.method} /api/{api_path}")
        print(f"   Request data: {str(request_data)[:100]}...")
        
        # ========================================================================
        # THREAT DETECTION - Block dangerous requests
        # ========================================================================
        try:
            threat_detector.detect_threats(request_data)
            print(f"   ✅ Threat check passed")
        except ThreatDetectedError as e:
            print(f"   ❌ THREAT DETECTED: {e}")
            return jsonify({
                "status": "blocked",
                "message": "Request blocked: Security threat detected",
                "threat_type": str(e.threat_level),
                "threat_details": e.details,
                "reason": str(e)
            }), 403  # Forbidden
        
        # ========================================================================
        # SAFE REQUEST - Forward to actual backend
        # ========================================================================
        try:
            import requests
            
            # Build the actual backend URL
            backend_url = f"{ACTUAL_BACKEND_URL}/api/{api_path}"
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'AI-Security-Middleware'
            }
            
            print(f"   📤 Forwarding to: {backend_url}")
            
            # Forward request to actual backend
            if request.method == 'GET':
                response = requests.get(backend_url, params=request_data, headers=headers, timeout=30)
            elif request.method == 'POST':
                response = requests.post(backend_url, json=request_data, headers=headers, timeout=30)
            elif request.method == 'PUT':
                response = requests.put(backend_url, json=request_data, headers=headers, timeout=30)
            elif request.method == 'DELETE':
                response = requests.delete(backend_url, json=request_data, headers=headers, timeout=30)
            elif request.method == 'PATCH':
                response = requests.patch(backend_url, json=request_data, headers=headers, timeout=30)
            
            # Forward the response from backend to frontend
            print(f"   ✅ Response: {response.status_code}")
            
            return response.json(), response.status_code
            
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Backend unreachable: {ACTUAL_BACKEND_URL}")
            return jsonify({
                "status": "error",
                "message": "Backend service unavailable",
                "backend_url": ACTUAL_BACKEND_URL
            }), 503
        except requests.exceptions.Timeout:
            print(f"   ❌ Backend timeout")
            return jsonify({
                "status": "error",
                "message": "Backend request timeout"
            }), 504
        except Exception as backend_error:
            print(f"   ❌ Backend error: {backend_error}")
            return jsonify({
                "status": "error",
                "message": f"Backend error: {str(backend_error)}"
            }), 500
    
    except Exception as e:
        print(f"   ❌ Middleware error: {e}")
        return jsonify({
            "status": "error",
            "message": f"Middleware error: {str(e)}"
        }), 500


# ================================================================================
# Main
# ================================================================================

if __name__ == "__main__":
    if not GROQ_API_KEY:
        print("⚠️ GROQ_API_KEY not set. Please configure in .env file")
    
    if not GITHUB_TOKEN:
        print("⚠️ GITHUB_TOKEN not set. Public API rate limits will apply")
    
    print(f"📦 GitHub Repo: {GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}")
    print("🚀 Starting AI Security Middleware with GitHub Integration")
    print("📍 Server running on: http://localhost:5000")
    print("🔍 Endpoints:")
    print("   - POST /api/github/connect - Connect to GitHub repo")
    print("   - POST /api/discover - Discover APIs from GitHub")
    print("   - GET /api/list - List discovered APIs")
    print("   - GET/POST /api/analyze/<api_name> - Analyze specific API")
    print("   - POST /api/analyze-input - Check input for threats")
    print("   - POST /api/validate-request - Validate request")
    print("   - GET /api/health - Health check")
    
    app.run(debug=True, host="0.0.0.0", port=5000)