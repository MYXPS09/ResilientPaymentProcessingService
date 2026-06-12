from sqlalchemy import Column, BigInteger, String, Numeric, Text, DateTime, ForeignKey, Integer
from common.models.base import Base
from common.models.mixins import CommonFieldMixin

class Payment(Base, CommonFieldMixin):
    __tablename__ = "payments"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    payment_num = Column(String(64), unique=True, nullable=False, index=True)
    idempotency_key = Column(String(128), unique=True, nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(8), default='INR')
    status = Column(String(32), default='PENDING')
    gateway_ref = Column(String(128), nullable=True)
    gateway_status = Column(String(32), nullable=True)
    failure_reason = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    payer_name = Column(String(128), nullable=True)
    payer_email = Column(String(128), nullable=True)
    payer_phone = Column(String(32), nullable=True)
    description = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)
    webhook_received_at = Column(DateTime, nullable=True)
    processed_at = Column(DateTime, nullable=True)


class PaymentEvent(Base, CommonFieldMixin):
    __tablename__ = "payment_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    payment_id = Column(BigInteger, ForeignKey("payments.id"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)
    from_status = Column(String(32), nullable=True)
    to_status = Column(String(32), nullable=True)
    gateway_ref = Column(String(128), nullable=True)
    notes = Column(Text, nullable=True)
