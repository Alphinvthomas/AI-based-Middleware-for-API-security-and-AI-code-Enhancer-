import requests
import os
import re
from typing import Optional
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

load_dotenv()

# 🔐 Use environment variable instead of hardcoding
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

SERVER_A_URL = "http://localhost:8000"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME = "llama-3.1-8b-instant"

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication


# ==================================================
# Fetch API Source from Test Server
# ==================================================
def fetch_api_source(api_name):
    try:
        response = requests.get(f"{SERVER_A_URL}/source/{api_name}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


# ==================================================
# Fetch API List from Test Server
# ==================================================
def fetch_api_list():
    try:
        response = requests.get(f"{SERVER_A_URL}/api/list")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e), "apis": []}


# ==================================================
# Extract numeric score safely
# ==================================================
def extract_score(text):
    match = re.search(r'\d+', text)
    if match:
        return int(match.group())
    return 0


# ==================================================
# Get Security Score from LLM
# ==================================================
def get_security_score(source_code: str):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
    You are a cybersecurity expert.
    Analyze the following API source code and give a security score from 1 to 100.
    Only return a number.

    Code:
    {source_code}
    """

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0
    }

    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            score_text = result["choices"][0]["message"]["content"]
            return extract_score(score_text)
        else:
            print("Score API Error:", response.status_code)
            return None
    except Exception as e:
        print(f"Error getting security score: {e}")
        return None


# ==================================================
# Generate Secure Code Suggestion
# ==================================================
PROJECT_CONTEXT = """
PROJECT STRUCTURE:
- Main server file (main.py) uses FastAPI with a registry pattern
- APIs are registered in API_REGISTRY dictionary
- Each API is a function in apis/ folder
- Functions return simple dictionaries (not FastAPI responses)
- The main.py inspect.getsource() retrieves function source code

EXISTING main.py PATTERN:
```python
from fastapi import FastAPI, HTTPException
import inspect
from apis import user_api, payment_api, login_api, order_api
from pydantic import BaseModel

app = FastAPI(title="API Source Registry Server")

API_REGISTRY = {
    "api_name": {"func": module.function, "method": "GET/POST/PUT/DELETE"},
}

@app.get("/source/{api_name}")
def get_api_source(api_name: str):
    if api_name not in API_REGISTRY:
        raise HTTPException(status_code=404, detail="API not found")
    source_code = inspect.getsource(API_REGISTRY[api_name]["func"])
    return {"api_name": api_name, "source_code": source_code}
```

REQUIREMENTS:
1. Output ONLY valid Python code - a single function that can replace the original
2. The function should return a simple dict (not FastAPI response objects)
3. Include necessary imports at the top of the function
4. Implement: input validation, error handling, authentication placeholder
5. Do NOT use hardcoded credentials - use environment variables
6. Do NOT create FastAPI app or routes - just the function
7. If external dependencies needed, add: ###EXTERNAL_DEPENDENCIES### and list pip packages
8. Do NOT add explanations - ONLY code

Example output format:
```python
def api_function():
    # imports
    # validation
    # logic
    return {"result": "value"}
```
"""

def get_secure_code_suggestion(source_code: str, api_name: Optional[str] = None):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""You are a senior backend security engineer.

Analyze the following API function and rewrite it to be secure.

{PROJECT_CONTEXT}

API NAME: {api_name if api_name else "Unknown"}

Original Code to Secure:
{source_code}

Generate the SECURE version of this function:"""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            if "###EXTERNAL_DEPENDENCIES###" in content:
                parts = content.split("###EXTERNAL_DEPENDENCIES###")
                code = parts[0].strip()
                dependencies_raw = parts[1].strip() if len(parts) > 1 else ""
                
                dependencies = []
                if dependencies_raw:
                    for line in dependencies_raw.split('\n'):
                        line = line.strip()
                        if line.startswith('- ') or line.startswith('* '):
                            dependencies.append(line[2:].strip())
                        elif line.startswith('pip ') or line.startswith('pip install '):
                            dependencies.append(line.replace('pip install ', '').replace('pip ', '').strip())
                        elif line and not line.startswith('#'):
                            dependencies.append(line.strip())
                
                return {"code": code, "dependencies": dependencies}
            else:
                return {"code": content, "dependencies": []}
        else:
            print("Secure Code API Error:", response.status_code)
            return {"code": "Secure code generation failed.", "dependencies": []}
    except Exception as e:
        print(f"Error generating secure code: {e}")
        return {"code": f"Error: {str(e)}", "dependencies": []}


# ==================================================
# API Endpoints
# ==================================================

@app.route('/api/list', methods=['GET'])
def list_apis():
    """
    Returns the list of available APIs from the test server with security scores.
    """
    data = fetch_api_list()
    if "error" in data and not data.get("apis"):
        return jsonify({"error": data["error"], "apis": []}), 200
    
    apis = data.get("apis", [])
    
    for api in apis:
        api_name = api.get("apiKey")
        if api_name:
            source_data = fetch_api_source(api_name)
            if "source_code" in source_data:
                score = get_security_score(source_data["source_code"])
                api["score"] = score if score else 0
                api["status"] = "Active" if score and score >= 60 else "Danger"
            else:
                api["score"] = 0
                api["status"] = "Danger"
    
    return jsonify({"apis": apis}), 200


@app.route('/api/analyze/<api_name>', methods=['GET'])
def analyze_api(api_name):
    """
    Analyzes an API for security vulnerabilities.
    
    Returns:
    {
        "api_name": str,
        "endpoint": str,
        "source_code": str,
        "security_score": int (0-100),
        "suggested_code": str (only if score < 70),
        "needs_improvement": bool
    }
    """
    try:
        # Fetch API source from test server
        data = fetch_api_source(api_name)
        
        if "error" in data:
            return jsonify({"error": f"Could not fetch API source: {data['error']}"}), 404
        
        source_code = data.get("source_code", "")
        
        if not source_code:
            return jsonify({"error": "No source code found"}), 404
        
        # Get security score
        score = get_security_score(source_code)
        if score is None:
            return jsonify({"error": "Failed to analyze security score"}), 500
        
        # Generate suggested code if score is low
        suggested_code = None
        suggested_dependencies = []
        if score < 70:
            result = get_secure_code_suggestion(source_code, api_name)
            suggested_code = result.get("code", "")
            suggested_dependencies = result.get("dependencies", [])
        
        return jsonify({
            "api_name": api_name,
            "endpoint": f"/api/v1/{api_name}",
            "source_code": source_code,
            "security_score": score,
            "suggested_code": suggested_code,
            "suggested_dependencies": suggested_dependencies,
            "needs_improvement": score < 70,
            "severity": "Critical" if score < 50 else "High" if score < 70 else "Medium" if score < 85 else "Low"
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/batch-analyze', methods=['POST'])
def batch_analyze():
    """
    Analyzes multiple APIs at once.
    
    Request body:
    {
        "api_names": ["login", "user", "payment"]
    }
    """
    try:
        data = request.get_json()
        api_names = data.get("api_names", [])
        
        results = []
        for api_name in api_names:
            api_data = fetch_api_source(api_name)
            if "error" not in api_data:
                source_code = api_data.get("source_code", "")
                score = get_security_score(source_code)
                
                results.append({
                    "api_name": api_name,
                    "security_score": score,
                    "needs_improvement": score < 70 if score else False
                })
        
        return jsonify({"analyses": results}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "AI Security Middleware"}), 200


# ==================================================
# Error Handlers
# ==================================================
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


# ==================================================
# Main
# ==================================================
if __name__ == "__main__":
    if not GROQ_API_KEY:
        print("⚠️ GROQ_API_KEY not set. Please configure environment variable.")
        exit()
    
    print("🚀 Starting AI Security Middleware Server...")
    print("📡 Backend API running on http://localhost:5000")
    print("🔗 Test Server (source APIs) should be running on http://localhost:8000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)