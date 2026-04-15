"""
Integration Example: Using GitHub Security Middleware in Your Flask App

This example shows how to integrate the GitHub-based API Security Middleware
into your Flask application to validate all incoming requests and detect threats.
"""

from flask import Flask, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

# Configuration
MIDDLEWARE_URL = "http://localhost:5000"
MIDDLEWARE_TIMEOUT = 5  # seconds

# Threat blocking configuration
BLOCK_CRITICAL = True      # Block CRITICAL threats
BLOCK_HIGH = True          # Block HIGH threats
BLOCK_MEDIUM = False       # Allow MEDIUM threats
LOG_ALL_THREATS = True     # Log all threats for monitoring


# ============================================================================
# Middleware Threat Detector
# ============================================================================

def check_request_safety(data):
    """
    Check if request data is safe using the security middleware
    
    Args:
        data: Request data (dict)
        
    Returns:
        Tuple of (is_safe, threat_info)
    """
    try:
        response = requests.post(
            f"{MIDDLEWARE_URL}/api/validate-request",
            json=data,
            timeout=MIDDLEWARE_TIMEOUT
        )
        
        result = response.json()
        
        if response.status_code == 200 and result.get("valid"):
            return True, None
        else:
            threat_info = result.get("details", {})
            return False, threat_info
    
    except requests.exceptions.Timeout:
        print("⚠️ Middleware timeout - allowing request through")
        return True, None
    except Exception as e:
        print(f"⚠️ Middleware error: {e} - allowing request through")
        return True, None


def should_block_threat(threat_level):
    """Determine if threat should block the request"""
    if threat_level == "CRITICAL" and BLOCK_CRITICAL:
        return True
    elif threat_level == "HIGH" and BLOCK_HIGH:
        return True
    elif threat_level == "MEDIUM" and BLOCK_MEDIUM:
        return True
    return False


def log_threat(endpoint, threat_info, user_ip=None):
    """Log detected threats for security monitoring"""
    if not LOG_ALL_THREATS:
        return
    
    timestamp = datetime.now().isoformat()
    threat_level = threat_info.get("threat_level", "UNKNOWN")
    threats_count = threat_info.get("threats_detected", 0)
    
    log_entry = {
        "timestamp": timestamp,
        "endpoint": endpoint,
        "user_ip": user_ip or request.remote_addr,
        "threat_level": threat_level,
        "threats_count": threats_count,
        "threat_list": threat_info.get("threat_list", [])[:3]  # Top 3 threats
    }
    
    print(f"🚨 THREAT DETECTED: {log_entry}")
    # TODO: Save to database or logging service
    # db.security_logs.insert_one(log_entry)


# ============================================================================
# Request Validation Decorator
# ============================================================================

def validate_request_safety(f):
    """
    Decorator to validate request safety before processing
    
    Usage:
        @app.route('/search', methods=['POST'])
        @validate_request_safety
        def search():
            ...
    """
    def wrapper(*args, **kwargs):
        # Get request data
        if request.method == 'POST':
            data = request.get_json() or {}
        else:
            data = request.args.to_dict()
        
        # Check for threats
        is_safe, threat_info = check_request_safety(data)
        
        if not is_safe:
            # Log the threat
            log_threat(request.path, threat_info)
            
            # Check if we should block
            threat_level = threat_info.get("threat_level", "UNKNOWN")
            
            if should_block_threat(threat_level):
                return jsonify({
                    "error": "🚨 Malicious input detected",
                    "threat_level": threat_level,
                    "message": "Your request was blocked due to security concerns"
                }), 403
        
        # Request is safe, proceed
        return f(*args, **kwargs)
    
    wrapper.__name__ = f.__name__
    return wrapper


# ============================================================================
# Example Routes
# ============================================================================

@app.route('/api/search', methods=['POST'])
@validate_request_safety
def search():
    """
    Search endpoint with automatic threat detection
    All input is validated before processing
    """
    query = request.json.get('q', '')
    category = request.json.get('category', '')
    
    return jsonify({
        "status": "success",
        "results": [
            {"id": 1, "title": f"Result for '{query}'"},
            {"id": 2, "title": f"Another result for '{query}'"}
        ],
        "total": 2
    })


@app.route('/api/user/<user_id>', methods=['GET'])
@validate_request_safety
def get_user(user_id):
    """
    Get user by ID with threat detection
    """
    return jsonify({
        "id": user_id,
        "name": "John Doe",
        "email": f"user_{user_id}@example.com"
    })


@app.route('/api/create-post', methods=['POST'])
@validate_request_safety
def create_post():
    """
    Create a new post with threat detection
    """
    title = request.json.get('title', '')
    content = request.json.get('content', '')
    tags = request.json.get('tags', [])
    
    return jsonify({
        "status": "success",
        "post_id": 123,
        "title": title,
        "created_at": datetime.now().isoformat()
    })


@app.route('/api/upload', methods=['POST'])
@validate_request_safety
def upload_file():
    """
    Upload file with threat detection
    """
    filename = request.form.get('filename', '')
    content = request.form.get('content', '')
    
    return jsonify({
        "status": "success",
        "filename": filename,
        "size": len(content)
    })


@app.route('/api/analyze-api/<api_name>', methods=['GET'])
def analyze_api(api_name):
    """
    Analyze API security (no validation needed - internal)
    """
    try:
        response = requests.get(
            f"{MIDDLEWARE_URL}/api/analyze/{api_name}",
            timeout=MIDDLEWARE_TIMEOUT
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": "API not found"}), 404
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/list-apis', methods=['GET'])
def list_apis():
    """
    List all discovered APIs (no validation needed - internal)
    """
    try:
        owner = request.args.get('owner')
        repo_name = request.args.get('repo_name')
        
        url = f"{MIDDLEWARE_URL}/api/list"
        if owner and repo_name:
            url += f"?owner={owner}&repo_name={repo_name}"
        
        response = requests.get(url, timeout=MIDDLEWARE_TIMEOUT)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": "Failed to fetch APIs"}), 500
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/discover', methods=['POST'])
@validate_request_safety
def discover_apis():
    """
    Discover APIs from GitHub (with threat detection)
    """
    try:
        owner = request.json.get('owner')
        repo_name = request.json.get('repo_name')
        
        if not owner or not repo_name:
            return jsonify({"error": "owner and repo_name required"}), 400
        
        response = requests.post(
            f"{MIDDLEWARE_URL}/api/discover",
            json={"owner": owner, "repo_name": repo_name},
            timeout=30
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify(response.json()), response.status_code
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# Health Check & Status
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint (no validation - system endpoint)
    """
    try:
        # Check middleware health
        middleware_response = requests.get(
            f"{MIDDLEWARE_URL}/api/health",
            timeout=MIDDLEWARE_TIMEOUT
        )
        middleware_status = "UP" if middleware_response.status_code == 200 else "DOWN"
        middleware_info = middleware_response.json() if middleware_response.status_code == 200 else {}
    except:
        middleware_status = "DOWN"
        middleware_info = {}
    
    return jsonify({
        "status": "UP",
        "timestamp": datetime.now().isoformat(),
        "middleware": {
            "status": middleware_status,
            "info": middleware_info
        }
    })


@app.route('/security-status', methods=['GET'])
def security_status():
    """
    Get security status and configuration
    """
    return jsonify({
        "middleware_url": MIDDLEWARE_URL,
        "threat_blocking": {
            "critical": BLOCK_CRITICAL,
            "high": BLOCK_HIGH,
            "medium": BLOCK_MEDIUM
        },
        "logging_enabled": LOG_ALL_THREATS,
        "timeout": MIDDLEWARE_TIMEOUT,
        "protected_endpoints": [
            "/api/search",
            "/api/user/<id>",
            "/api/create-post",
            "/api/upload",
            "/api/discover"
        ]
    })


# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(403)
def forbidden(error):
    return jsonify({"error": "Forbidden"}), 403


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# Testing Examples
# ============================================================================

if __name__ == "__main__":
    print("🚀 Starting Flask App with Security Middleware")
    print("📍 App running on: http://localhost:5001")
    print("\n🔒 Protected Endpoints:")
    print("   POST /api/search - With threat detection")
    print("   GET /api/user/<id> - With threat detection")
    print("   POST /api/create-post - With threat detection")
    print("   POST /api/upload - With threat detection")
    print("   POST /api/discover - With threat detection")
    print("\n📊 Status Endpoints:")
    print("   GET /health - Health check")
    print("   GET /security-status - Security configuration")
    print("\n📧 Ensure middleware is running at:", MIDDLEWARE_URL)
    
    app.run(debug=True, host="0.0.0.0", port=5001)


# ============================================================================
# Testing with curl
# ============================================================================

"""
# Test 1: Safe request
curl -X POST http://localhost:5001/api/search \
  -H "Content-Type: application/json" \
  -d '{"q": "python programming"}'

# Test 2: SQL Injection attempt (should be blocked)
curl -X POST http://localhost:5001/api/search \
  -H "Content-Type: application/json" \
  -d '{"q": "SELECT * FROM users WHERE id = 1 OR 1=1"}'

# Test 3: Command injection attempt (should be blocked)
curl -X POST http://localhost:5001/api/search \
  -H "Content-Type: application/json" \
  -d '{"q": "test; rm -rf /"}'

# Test 4: Create post (safe)
curl -X POST http://localhost:5001/api/create-post \
  -H "Content-Type: application/json" \
  -d '{"title": "My Post", "content": "Great content", "tags": ["python"]}'

# Test 5: Discover APIs
curl -X POST http://localhost:5001/api/discover \
  -H "Content-Type: application/json" \
  -d '{"owner": "pallets", "repo_name": "flask"}'

# Test 6: Health check
curl http://localhost:5001/health

# Test 7: Security status
curl http://localhost:5001/security-status
"""
