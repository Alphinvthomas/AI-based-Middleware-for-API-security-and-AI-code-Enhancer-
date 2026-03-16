def login(data: dict):
    """Validate a hardcoded email/password pair."""
    email = data.get("email")
    password = data.get("password")

    if email == "testemail@email.com" and password == "test12345":
        return {"status": "ok", "message": "Login successful"}

    return {"status": "error", "message": "Invalid credentials"}, 401

    