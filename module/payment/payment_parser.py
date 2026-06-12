from typing import Dict, Any
from module.payment.payment_schema import PaymentCreateRequest, PaymentStatus

def to_payment_dict(data: PaymentCreateRequest, payment_num: str) -> Dict[str, Any]:
    return {
        "payment_num": payment_num,
        "idempotency_key": data.idempotency_key,
        "amount": data.amount,
        "currency": data.currency,
        "status": PaymentStatus.PENDING,
        "payer_name": data.payer_name,
        "payer_email": data.payer_email,
        "payer_phone": data.payer_phone,
        "description": data.description,
        "metadata_json": data.metadata_json,
        "retry_count": 0,
    }
