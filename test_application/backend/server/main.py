from fastapi import FastAPI, HTTPException
import inspect
from apis import user_api, payment_api, login_api
from pydantic import BaseModel

app = FastAPI(title="API Source Registry Server")

API_REGISTRY = {
    "get_users": user_api.get_users,
    "process_payment": payment_api.process_payment,
    "login": login_api.login
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
                "method": "GET"
            }
            for name in API_REGISTRY.keys()
        ]
    }

@app.get("/api/{api_name}")
def call_api(api_name: str):
    if api_name not in API_REGISTRY:
        raise HTTPException(status_code=404, detail="API not found")
    return API_REGISTRY[api_name]()

@app.get("/source/{api_name}")
def get_api_source(api_name: str):
    if api_name not in API_REGISTRY:
        raise HTTPException(status_code=404, detail="API not found")

    source_code = inspect.getsource(API_REGISTRY[api_name])
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
    # Run this service with: python main.py
    # (Or use uvicorn directly for auto-reload: uvicorn main:app --reload --port 8000)
    try:
        import uvicorn

        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    except ImportError:
        print("uvicorn is not installed. Install it with `pip install uvicorn` and rerun.")
