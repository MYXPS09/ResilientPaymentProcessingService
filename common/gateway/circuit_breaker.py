import asyncio
import time
from enum import StrEnum
from common.config import settings
from common.util.logger import get_logger

log = get_logger(__name__)

class CircuitState(StrEnum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitBreaker:
    def __init__(self):
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self._lock = asyncio.Lock()

    async def record_failure(self):
        async with self._lock:
            self.failure_count += 1
            if self.state == CircuitState.CLOSED and self.failure_count >= settings.CB_FAILURE_THRESHOLD:
                self.state = CircuitState.OPEN
                self.last_failure_time = time.time()
                log.warning("Circuit breaker transitioned from CLOSED to OPEN")
            elif self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                self.last_failure_time = time.time()
                log.warning("Circuit breaker transitioned from HALF_OPEN to OPEN")

    async def record_success(self):
        async with self._lock:
            if self.state in (CircuitState.OPEN, CircuitState.HALF_OPEN):
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                log.info("Circuit breaker transitioned to CLOSED")
            else:
                self.failure_count = 0

    async def check_state(self) -> CircuitState:
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if time.time() - self.last_failure_time >= settings.CB_RECOVERY_TIMEOUT:
                    self.state = CircuitState.HALF_OPEN
                    log.info("Circuit breaker transitioned from OPEN to HALF_OPEN")
            return self.state

gateway_circuit_breaker = CircuitBreaker()
