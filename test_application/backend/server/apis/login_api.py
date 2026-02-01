from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

def login(data: LoginRequest):
    if data.username == "admin" and data.password == "password":
        return {"message": "Login successful"}
    return {"message": "Invalid credentials"}