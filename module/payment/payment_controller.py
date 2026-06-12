from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, status

from module.payment.payment_schema import (PaymentCreateRequest, PaymentResponse, 
                                           WebhookCallbackRequest, PaymentEventResponse)
from module.payment.payment_service import PaymentService
from common.middlewares.client_auth import get_api_client
from common.middlewares.rate_limiter import rate_limit_check
from common.gateway.circuit_breaker import gateway_circuit_breaker

routers = APIRouter(prefix="/payments")

@routers.post("/", response_model=PaymentResponse, status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(get_api_client), Depends(rate_limit_check)])
async def create_payment(
    data: PaymentCreateRequest,
    payment_service: PaymentService = Depends()
):
    return await payment_service.create_payment(data)

@routers.get("/", response_model=List[PaymentResponse], dependencies=[Depends(get_api_client)])
async def get_all(
    status: Optional[str] = None,
    payment_num: Optional[str] = None,
    payer_email: Optional[str] = None,
    currency: Optional[str] = None,
    payment_service: PaymentService = Depends()
):
    return await payment_service.search_payments(status, payment_num, payer_email, currency)

@routers.get("/{id}", response_model=PaymentResponse, dependencies=[Depends(get_api_client)])
async def get_by_id(
    id: int,
    payment_service: PaymentService = Depends()
):
    return await payment_service.get_payment(id)

@routers.get("/num/{payment_num}", response_model=PaymentResponse, dependencies=[Depends(get_api_client)])
async def get_by_payment_num(
    payment_num: str,
    payment_service: PaymentService = Depends()
):
    return await payment_service.get_payment_by_num(payment_num)

@routers.get("/{id}/events", response_model=List[PaymentEventResponse], dependencies=[Depends(get_api_client)])
async def get_events(
    id: int,
    payment_service: PaymentService = Depends()
):
    return await payment_service.get_events(id)

@routers.post("/{id}/retry", response_model=PaymentResponse, dependencies=[Depends(get_api_client), Depends(rate_limit_check)])
async def retry_payment(
    id: int,
    payment_service: PaymentService = Depends()
):
    return await payment_service.retry_payment(id)

# Unauthenticated endpoints
@routers.post("/webhook/callback", response_model=PaymentResponse)
async def webhook_callback(
    data: WebhookCallbackRequest,
    payment_service: PaymentService = Depends()
):
    return await payment_service.handle_webhook(data)

@routers.get("/gateway/circuit-status")
async def get_circuit_status() -> Dict[str, Any]:
    state = await gateway_circuit_breaker.check_state()
    return {"state": state}
