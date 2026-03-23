import secrets
import hashlib
import re
from datetime import datetime, timedelta

USER_DB = {
    "testemail@email.com": {
        "password_hash": hashlib.sha256("test12345".encode()).hexdigest(),
        "salt": "default_salt",
        "locked": False,
        "failed_attempts": 0
    }
}

TOKEN_DB = {}

RATE_LIMIT = {}
RATE_LIMIT_WINDOW = 60
MAX_ATTEMPTS = 5

def hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()

def generate_token() -> str:
    return secrets.token_urlsafe(32)

def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def login(data: dict):
    """Secure login with rate limiting, input validation, and secure password handling."""
    
    client_ip = data.get("client_ip", "unknown")
    current_time = datetime.now()
    
    if client_ip in RATE_LIMIT:
        attempts, first_attempt = RATE_LIMIT[client_ip]
        if current_time - first_attempt < timedelta(seconds=RATE_LIMIT_WINDOW):
            if attempts >= MAX_ATTEMPTS:
                reset_time = (first_attempt + timedelta(seconds=RATE_LIMIT_WINDOW) - current_time).seconds
                return {"error": "Too many login attempts. Try again later.", "retry_after": reset_time}, 429
        else:
            RATE_LIMIT[client_ip] = (0, current_time)
    
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    
    if not email or not password:
        return {"error": "Email and password are required"}, 400
    
    if not validate_email(email):
        return {"error": "Invalid email format"}, 400
    
    if email not in USER_DB:
        return {"error": "Invalid credentials"}, 401
    
    user = USER_DB[email]
    
    if user.get("locked"):
        return {"error": "Account is locked. Contact support."}, 423
    
    password_hash = hash_password(password, user["salt"])
    
    if password_hash != user["password_hash"]:
        user["failed_attempts"] = user.get("failed_attempts", 0) + 1
        
        if user["failed_attempts"] >= 3:
            user["locked"] = True
            return {"error": "Account locked due to multiple failed attempts"}, 423
        
        RATE_LIMIT[client_ip] = (RATE_LIMIT.get(client_ip, (0, current_time))[0] + 1, current_time)
        
        remaining = 3 - user["failed_attempts"]
        return {"error": f"Invalid credentials. {remaining} attempts remaining."}, 401
    
    user["failed_attempts"] = 0
    user["last_login"] = current_time.isoformat()
    
    token = generate_token()
    TOKEN_DB[token] = {
        "email": email,
        "created_at": current_time.isoformat(),
        "expires_at": (current_time + timedelta(hours=24)).isoformat()
    }
    
    return {
        "status": "ok",
        "message": "Login successful",
        "token": token,
        "token_type": "Bearer",
        "expires_in": 86400
    }


def verify_token(token: str) -> dict:
    """Verify if a token is valid and not expired."""
    if token not in TOKEN_DB:
        return None
    
    token_data = TOKEN_DB[token]
    expires_at = datetime.fromisoformat(token_data["expires_at"])
    
    if datetime.now() > expires_at:
        del TOKEN_DB[token]
        return None
    
    return token_data


def logout(token: str) -> dict:
    """Invalidate a token."""
    if token in TOKEN_DB:
        del TOKEN_DB[token]
        return {"message": "Logged out successfully"}
    return {"error": "Invalid token"}, 401
