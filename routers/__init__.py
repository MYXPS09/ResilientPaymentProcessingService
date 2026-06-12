from fastapi import APIRouter
from module.payment.payment_controller import routers as payment_routers

api_router = APIRouter()
api_router.include_router(payment_routers)
