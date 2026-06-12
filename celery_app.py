from celery import Celery
from common.config import settings

celery_app = Celery(
    "payment_service",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["common.tasks.payment_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)
