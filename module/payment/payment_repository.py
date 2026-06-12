from typing import Optional, List
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from common.database import get_async_session
from common.repositories.base_operations import BaseOperations
from common.models.payment import Payment, PaymentEvent

class PaymentRepository:
    def __init__(self, session: AsyncSession = Depends(get_async_session)):
        self.session = session
        self.bo = BaseOperations(session, Payment)
        self.event_bo = BaseOperations(session, PaymentEvent)

    async def get_by_idempotency_key(self, idempotency_key: str) -> Optional[Payment]:
        return await self.bo.get_by_field("idempotency_key", idempotency_key)

    async def lock_for_update(self, payment_id: int) -> Optional[Payment]:
        stmt = select(Payment).where(Payment.id == payment_id, Payment.is_deleted == False).with_for_update(skip_locked=True)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_event(self, payment_id: int, event_type: str, from_status: Optional[str] = None, 
                           to_status: Optional[str] = None, gateway_ref: Optional[str] = None, notes: Optional[str] = None):
        event_data = {
            "payment_id": payment_id,
            "event_type": event_type,
            "from_status": from_status,
            "to_status": to_status,
            "gateway_ref": gateway_ref,
            "notes": notes
        }
        await self.event_bo.create(event_data)

    async def get_events(self, payment_id: int) -> List[PaymentEvent]:
        stmt = select(PaymentEvent).where(PaymentEvent.payment_id == payment_id, PaymentEvent.is_deleted == False).order_by(PaymentEvent.created_at.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search(self, status: Optional[str] = None, payment_num: Optional[str] = None, 
                     payer_email: Optional[str] = None, currency: Optional[str] = None) -> List[Payment]:
        stmt = select(Payment).where(Payment.is_deleted == False)
        if status:
            stmt = stmt.where(Payment.status == status)
        if payment_num:
            stmt = stmt.where(Payment.payment_num == payment_num)
        if payer_email:
            stmt = stmt.where(Payment.payer_email == payer_email)
        if currency:
            stmt = stmt.where(Payment.currency == currency)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
