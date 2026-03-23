from fastapi import FastAPI, HTTPException
import inspect
from apis import user_api, payment_api, login_api, order_api
from pydantic import BaseModel

app = FastAPI(title="API Source Registry Server")

API_REGISTRY = {
    "get_users": {"func": user_api.get_users, "method": "GET"},
    "create_user": {"func": user_api.create_user, "method": "POST"},
    "update_user": {"func": user_api.update_user, "method": "PUT"},
    "delete_user": {"func": user_api.delete_user, "method": "DELETE"},
    "process_payment": {"func": payment_api.process_payment, "method": "POST"},
    "refund_payment": {"func": payment_api.refund_payment, "method": "POST"},
    "login": {"func": login_api.login, "method": "POST"},
    "create_order": {"func": order_api.create_order, "method": "POST"},
    "send_email": {"func": order_api.send_email, "method": "POST"},
}

@app.get("/api/list")
def list_apis():
    """Return the list of registered APIs available in this service."""
    return {
        "apis": [
            {
                "apiKey": name,
                "name": name,
                "endpoint": f"/api/{name}",
                "method": info["method"]
            }
            for name, info in API_REGISTRY.items()
        ]
    }

@app.get("/api/{api_name}")
def call_api(api_name: str):
    if api_name not in API_REGISTRY:
        raise HTTPException(status_code=404, detail="API not found")
    return API_REGISTRY[api_name]["func"]()

@app.get("/source/{api_name}")
def get_api_source(api_name: str):
    if api_name not in API_REGISTRY:
        raise HTTPException(status_code=404, detail="API not found")

    source_code = inspect.getsource(API_REGISTRY[api_name]["func"])
    return {
        "api_name": api_name,
        "source_code": source_code
    }

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/login")
def login_endpoint(data: LoginRequest):
    return login_api.login(data.dict())

if __name__ == "__main__":
    try:
        import uvicorn
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    except ImportError:
        print("uvicorn is not installed. Install it with `pip install uvicorn` and rerun.")
