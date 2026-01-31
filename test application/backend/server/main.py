from fastapi import FastAPI, HTTPException
import inspect
from apis import user_api, payment_api

app = FastAPI(title="API Source Registry Server")

API_REGISTRY = {
    "get_users": user_api.get_users,
    "process_payment": payment_api.process_payment
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
