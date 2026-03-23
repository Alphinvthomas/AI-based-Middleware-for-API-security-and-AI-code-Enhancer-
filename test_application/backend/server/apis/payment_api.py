from pydantic import BaseModel

class PaymentRequest(BaseModel):
    user_id: int
    amount: float
    currency: str = "USD"

def process_payment():
    return {"message": "Process payment endpoint", "method": "POST"}


class RefundRequest(BaseModel):
    transaction_id: str
    amount: float

def refund_payment():
    return {"message": "Refund payment endpoint", "method": "POST"}
