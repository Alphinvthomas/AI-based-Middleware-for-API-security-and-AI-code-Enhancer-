from pydantic import BaseModel

class OrderRequest(BaseModel):
    user_id: int
    items: list

def create_order():
    return {"message": "Create order endpoint", "method": "POST"}


class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str

def send_email():
    return {"message": "Send email endpoint", "method": "POST"}
