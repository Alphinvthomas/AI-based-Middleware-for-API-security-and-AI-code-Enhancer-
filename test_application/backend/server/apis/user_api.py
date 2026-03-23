from typing import List, Optional
from datetime import datetime, timedelta
import secrets
import hashlib

USERS_DB = [
    {"id": 1, "name": "Alice", "email": "alice@example.com", "role": "admin", "created_at": "2024-01-15T10:30:00Z"},
    {"id": 2, "name": "Bob", "email": "bob@example.com", "role": "user", "created_at": "2024-02-20T14:45:00Z"},
    {"id": 3, "name": "Charlie", "email": "charlie@example.com", "role": "user", "created_at": "2024-03-10T09:15:00Z"},
]

SESSION_DB = {}

def generate_session_id() -> str:
    return secrets.token_urlsafe(32)

def hash_data(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()

def get_users(headers: Optional[dict] = None) -> dict:
    """Secure user retrieval endpoint with authentication and pagination."""
    
    auth_header = headers.get("Authorization", "") if headers else ""
    
    if not auth_header.startswith("Bearer "):
        return {"error": "Missing or invalid Authorization header. Use: Bearer <token>"}, 401
    
    token = auth_header.replace("Bearer ", "")
    
    session = SESSION_DB.get(token)
    if not session:
        return {"error": "Invalid or expired session"}, 401
    
    if datetime.now() > datetime.fromisoformat(session["expires_at"]):
        del SESSION_DB[token]
        return {"error": "Session expired. Please login again."}, 401
    
    session["last_activity"] = datetime.now().isoformat()
    
    page = 1
    limit = 10
    
    start = (page - 1) * limit
    end = start + limit
    
    total_users = len(USERS_DB)
    paginated_users = USERS_DB[start:end]
    
    safe_users = []
    for user in paginated_users:
        safe_users.append({
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        })
    
    return {
        "users": safe_users,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_users,
            "total_pages": (total_users + limit - 1) // limit
        },
        "meta": {
            "request_id": secrets.token_hex(8),
            "timestamp": datetime.now().isoformat()
        }
    }


def get_user_by_id(user_id: int, headers: Optional[dict] = None) -> dict:
    """Secure single user retrieval with authorization check."""
    
    auth_header = headers.get("Authorization", "") if headers else ""
    
    if not auth_header.startswith("Bearer "):
        return {"error": "Missing or invalid Authorization header"}, 401
    
    token = auth_header.replace("Bearer ", "")
    session = SESSION_DB.get(token)
    
    if not session:
        return {"error": "Invalid session"}, 401
    
    if datetime.now() > datetime.fromisoformat(session["expires_at"]):
        return {"error": "Session expired"}, 401
    
    user = next((u for u in USERS_DB if u["id"] == user_id), None)
    
    if not user:
        return {"error": "User not found"}, 404
    
    if session["role"] != "admin" and session["email"] != user["email"]:
        return {"error": "Access denied. You can only view your own profile."}, 403
    
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "created_at": user["created_at"]
    }


def create_session(email: str, role: str = "user") -> dict:
    """Create a new session token."""
    token = generate_session_id()
    expires_at = datetime.now() + timedelta(hours=24)
    
    SESSION_DB[token] = {
        "email": email,
        "role": role,
        "created_at": datetime.now().isoformat(),
        "expires_at": expires_at.isoformat(),
        "last_activity": datetime.now().isoformat()
    }
    
    return {
        "token": token,
        "expires_at": expires_at.isoformat()
    }


def create_user():
    return {"message": "User creation endpoint", "method": "POST"}


def update_user():
    return {"message": "User update endpoint", "method": "PUT"}


def delete_user():
    return {"message": "User deletion endpoint", "method": "DELETE"}
