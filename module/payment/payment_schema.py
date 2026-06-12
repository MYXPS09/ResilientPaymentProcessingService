from enum import StrEnum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import Field, confloat
from decimal import Decimal
from common.schemas.common import BaseRequestModel, BaseResponseModel

class PaymentStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class PaymentEventRequest(BaseRequestModel):
    event_type: str
    from_status: Optional[str] = None
    to_status: Optional[str] = None
    gateway_ref: Optional[str] = None
    notes: Optional[str] = None

class PaymentEventResponse(BaseResponseModel):
    id: int
    payment_id: int
    event_type: str
    from_status: Optional[str] = None
    to_status: Optional[str] = None
    gateway_ref: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

class PaymentCreateRequest(BaseRequestModel):
    idempotency_key: str
    amount: Decimal = Field(gt=0, description="Amount must be positive")
    currency: str = "INR"
    payer_name: Optional[str] = None
    payer_email: Optional[str] = None
    payer_phone: Optional[str] = None
    description: Optional[str] = None
    metadata_json: Optional[str] = None

class PaymentResponse(BaseResponseModel):
    id: int
    payment_num: str
    idempotency_key: str
    amount: Decimal
    currency: str
    status: PaymentStatus
    gateway_ref: Optional[str] = None
    gateway_status: Optional[str] = None
    failure_reason: Optional[str] = None
    retry_count: int
    max_retries: int
    payer_name: Optional[str] = None
    payer_email: Optional[str] = None
    payer_phone: Optional[str] = None
    description: Optional[str] = None
    metadata_json: Optional[str] = None
    webhook_received_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    already_processed: Optional[bool] = False

class WebhookCallbackRequest(BaseRequestModel):
    gateway_ref: str
    status: str
    message: Optional[str] = None
    signature: Optional[str] = None # Comment: For future HMAC verification
