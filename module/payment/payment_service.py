from typing import List, Optional
from datetime import datetime
from fastapi import Depends

from common.exceptions.base import BadRequestException, ConflictException, NotFoundException
from common.util.logger import get_logger
from common.util.common_util import generate_payment_num
from module.payment.payment_schema import PaymentCreateRequest, PaymentStatus, WebhookCallbackRequest
from module.payment.payment_repository import PaymentRepository
from module.payment.payment_parser import to_payment_dict
from common.models.payment import Payment, PaymentEvent

log = get_logger(__name__)

class PaymentService:
    def __init__(self, payment_repo: PaymentRepository = Depends()):
        self.payment_repo = payment_repo

    async def create_payment(self, data: PaymentCreateRequest) -> Payment:
        # Check idempotency
        existing_payment = await self.payment_repo.get_by_idempotency_key(data.idempotency_key)
        if existing_payment:
            log.info(f"Idempotency hit for key {data.idempotency_key}, returning existing payment.")
            existing_payment.already_processed = True
            await self.payment_repo.create_event(
                payment_id=existing_payment.id,
                event_type="IDEMPOTENCY_HIT",
                notes=f"Duplicate request for idempotency key {data.idempotency_key}"
            )
            return existing_payment

        payment_num = generate_payment_num()
        payment_dict = to_payment_dict(data, payment_num)
        
        payment = await self.payment_repo.bo.create(payment_dict)
        
        await self.payment_repo.create_event(
            payment_id=payment.id,
            event_type="INITIATED",
            to_status=PaymentStatus.PENDING,
            notes="Payment created"
        )
        
        # Enqueue task
        from common.tasks.payment_tasks import process_payment_task
        process_payment_task.delay(payment.id)
        
        return payment

    async def get_payment(self, payment_id: int) -> Payment:
        return await self.payment_repo.bo.faf_one_by_id(payment_id)

    async def get_payment_by_num(self, payment_num: str) -> Payment:
        payment = await self.payment_repo.bo.get_by_field("payment_num", payment_num)
        if not payment:
            raise NotFoundException(f"Payment with num {payment_num} not found")
        return payment

    async def get_events(self, payment_id: int) -> List[PaymentEvent]:
        # Validate existence
        await self.get_payment(payment_id)
        return await self.payment_repo.get_events(payment_id)

    async def search_payments(self, status: Optional[str] = None, payment_num: Optional[str] = None, 
                              payer_email: Optional[str] = None, currency: Optional[str] = None) -> List[Payment]:
        return await self.payment_repo.search(status, payment_num, payer_email, currency)

    async def retry_payment(self, payment_id: int) -> Payment:
        payment = await self.get_payment(payment_id)
        if payment.status == PaymentStatus.SUCCESS:
            raise BadRequestException("Cannot retry a successful payment")
            
        await self.payment_repo.create_event(
            payment_id=payment.id,
            event_type="RETRY_REQUESTED",
            notes="Manual retry requested"
        )
        
        from common.tasks.payment_tasks import process_payment_task
        process_payment_task.delay(payment.id)
        
        return payment

    async def handle_webhook(self, data: WebhookCallbackRequest) -> Payment:
        payment = await self.payment_repo.bo.get_by_field("gateway_ref", data.gateway_ref)
        if not payment:
            raise NotFoundException(f"Payment with gateway_ref {data.gateway_ref} not found")

        # Duplicate check
        if payment.status == data.status and payment.status in [PaymentStatus.SUCCESS, PaymentStatus.FAILED]:
            log.info(f"Duplicate webhook for {data.gateway_ref} with status {data.status}")
            return payment
            
        # Conflict check
        if payment.status in [PaymentStatus.SUCCESS, PaymentStatus.FAILED] and payment.status != data.status:
            log.warning(f"Conflicting webhook for {data.gateway_ref}. Stored: {payment.status}, Webhook: {data.status}")
            await self.payment_repo.create_event(
                payment_id=payment.id,
                event_type="WEBHOOK_CONFLICT",
                notes=f"Conflicting webhook received. Expected {payment.status}, got {data.status}"
            )
            return payment

        # Early or valid update
        old_status = payment.status
        update_data = {
            "status": data.status,
            "webhook_received_at": datetime.utcnow(),
            "gateway_status": data.status,
            "processed_at": datetime.utcnow() if data.status in [PaymentStatus.SUCCESS, PaymentStatus.FAILED] else payment.processed_at
        }
        payment = await self.payment_repo.bo.update(payment, update_data)
        
        await self.payment_repo.create_event(
            payment_id=payment.id,
            event_type="STATUS_CHANGED",
            from_status=old_status,
            to_status=data.status,
            gateway_ref=data.gateway_ref,
            notes=f"Webhook received: {data.message}"
        )
        
        return payment
