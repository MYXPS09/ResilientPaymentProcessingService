import asyncio
from celery_app import celery_app
from common.database import async_session_maker
from common.config import settings
from module.payment.payment_schema import PaymentStatus
from common.gateway.simulator import call_external_gateway, GatewayOutcome
from common.gateway.circuit_breaker import gateway_circuit_breaker, CircuitState
from module.payment.payment_repository import PaymentRepository
from common.util.logger import get_logger
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

log = get_logger(__name__)

class PaymentProcessor:
    """Handles the lifecycle of processing a single payment"""
    
    def __init__(self, session: AsyncSession, repo: PaymentRepository):
        self.session = session
        self.repo = repo
        self.payment = None

    async def process(self, payment_id: int):
        self.payment = await self.repo.lock_for_update(payment_id)
        
        if not self._is_processable(payment_id):
            return
            
        await self._transition_to_processing()
        
        if await self._is_circuit_breaker_open():
            return
            
        await self._execute_retries()

    def _is_processable(self, payment_id: int) -> bool:
        if not self.payment:
            log.warning(f"Payment {payment_id} is locked by another worker or not found.")
            return False
            
        if self.payment.status not in [PaymentStatus.PENDING, PaymentStatus.FAILED]:
            log.info(f"Payment {payment_id} is already in state {self.payment.status}. Skipping.")
            return False
            
        return True

    async def _transition_to_processing(self):
        old_status = self.payment.status
        self.payment = await self.repo.bo.update(self.payment, {"status": PaymentStatus.PROCESSING})
        await self.repo.create_event(
            payment_id=self.payment.id,
            event_type="STATUS_CHANGED",
            from_status=old_status,
            to_status=PaymentStatus.PROCESSING,
            notes="Starting processing"
        )

    async def _is_circuit_breaker_open(self) -> bool:
        state = await gateway_circuit_breaker.check_state()
        if state == CircuitState.OPEN:
            await self._mark_as_failed("Circuit breaker OPEN")
            await self.session.commit()
            return True
        return False

    async def _mark_as_failed(self, reason: str):
        await self.repo.bo.update(self.payment, {
            "status": PaymentStatus.FAILED,
            "failure_reason": reason,
            "processed_at": datetime.utcnow()
        })
        await self.repo.create_event(
            payment_id=self.payment.id,
            event_type="STATUS_CHANGED",
            from_status=PaymentStatus.PROCESSING,
            to_status=PaymentStatus.FAILED,
            notes=reason
        )

    async def _execute_retries(self):
        attempt = self.payment.retry_count
        max_retries = self.payment.max_retries
        
        while attempt <= max_retries:
            try:
                response = await call_external_gateway()
                
                if response.outcome == GatewayOutcome.SUCCESS:
                    await gateway_circuit_breaker.record_success()
                    await self._handle_success(response, attempt)
                    await self.session.commit()
                    return
                else:
                    await gateway_circuit_breaker.record_failure()
                    delay = self._calculate_delay(attempt)
                    await self._handle_retry(response.message, attempt, delay)
                    
            except Exception as e:
                await gateway_circuit_breaker.record_failure()
                log.exception(f"Exception during gateway call for payment {self.payment.id}: {e}")
                delay = self._calculate_delay(attempt)
                await self._handle_retry(f"Exception: {e}", attempt, delay)

            if attempt < max_retries:
                await asyncio.sleep(delay)
                attempt += 1
            else:
                break
                
        # Failed after all retries
        await self._mark_as_failed("Max retries exhausted")
        await self.session.commit()

    async def _handle_success(self, response, attempt: int):
        await self.repo.bo.update(self.payment, {
            "status": PaymentStatus.SUCCESS,
            "gateway_ref": response.gateway_ref,
            "gateway_status": response.outcome,
            "processed_at": datetime.utcnow()
        })
        await self.repo.create_event(
            payment_id=self.payment.id,
            event_type="STATUS_CHANGED",
            from_status=PaymentStatus.PROCESSING,
            to_status=PaymentStatus.SUCCESS,
            gateway_ref=response.gateway_ref,
            notes=f"Attempt {attempt}: {response.message}"
        )

    async def _handle_retry(self, reason: str, attempt: int, delay: float):
        await self.repo.bo.update(self.payment, {
            "retry_count": attempt + 1,
            "failure_reason": reason
        })
        await self.repo.create_event(
            payment_id=self.payment.id,
            event_type="RETRY_ATTEMPT",
            notes=f"Attempt {attempt} failed: {reason}. Retrying in {delay}s"
        )

    def _calculate_delay(self, attempt: int) -> float:
        return min(settings.RETRY_BASE_DELAY * (2 ** attempt), settings.RETRY_MAX_DELAY)


async def process_payment_async(payment_id: int):
    async with async_session_maker() as session:
        try:
            repo = PaymentRepository(session)
            processor = PaymentProcessor(session, repo)
            await processor.process(payment_id)
        except Exception as e:
            await session.rollback()
            log.exception(f"Failed to process payment {payment_id}", e)

@celery_app.task(bind=True)
def process_payment_task(self, payment_id: int):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(process_payment_async(payment_id))
