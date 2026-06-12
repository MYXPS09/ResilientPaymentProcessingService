import random
import asyncio
import uuid
from dataclasses import dataclass
from enum import StrEnum
from common.config import settings

class GatewayOutcome(StrEnum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"

@dataclass
class GatewayResponse:
    outcome: GatewayOutcome
    gateway_ref: str | None
    message: str

async def call_external_gateway() -> GatewayResponse:
    """Simulates a network call to an external payment gateway."""
    delay = random.uniform(settings.GATEWAY_DELAY_MIN, settings.GATEWAY_DELAY_MAX)
    await asyncio.sleep(delay)

    rand_val = random.random()
    if rand_val < settings.GATEWAY_TIMEOUT_RATE:
        await asyncio.sleep(settings.GATEWAY_TIMEOUT_SECONDS)
        return GatewayResponse(outcome=GatewayOutcome.TIMEOUT, gateway_ref=None, message="Gateway timed out")
    
    if rand_val < settings.GATEWAY_TIMEOUT_RATE + settings.GATEWAY_SUCCESS_RATE:
        ref = f"GW-{uuid.uuid4().hex[:8].upper()}"
        return GatewayResponse(outcome=GatewayOutcome.SUCCESS, gateway_ref=ref, message="Payment succeeded")

    return GatewayResponse(outcome=GatewayOutcome.FAILED, gateway_ref=None, message="Payment declined by gateway")
