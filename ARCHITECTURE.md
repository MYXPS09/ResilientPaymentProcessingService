# System Architecture Overview

## 1. Component Responsibilities
- **FastAPI**: HTTP entry point, request validation, idempotency checks, rate limiting.
- **Celery + Redis**: Asynchronous processing queue for handling payment processing to decouple HTTP requests from slow external gateway calls.
- **PostgreSQL**: Durable storage of payments and their exact state transitions (event sourcing audit table).
- **External Gateway Simulator**: Simulates network latency, success rates, and failure timeouts.

## 2. Payment State Machine
```text
          +---------+
          | PENDING |
          +----+----+
               |
               v
         +-----------+
         | PROCESSING|
         +----+---+--+
              |   |
      +-------+   +-------+
      |                   |
      v                   v
+---------+          +--------+
| SUCCESS |          | FAILED |
+---------+          +--------+
```

## 3. Exponential Backoff Formula
Retry attempts follow exponential backoff:
`delay = min(RETRY_BASE_DELAY * 2^attempt, RETRY_MAX_DELAY)`
If `RETRY_BASE_DELAY=1.0` and `RETRY_MAX_DELAY=30.0`:
- Attempt 1: 2s
- Attempt 2: 4s
- Attempt 3: 8s
Retries prevent overwhelming the gateway and allow transient network issues to resolve.

## 4. Idempotency Mechanism
Every request includes an `idempotency_key`. The `payments` table has a unique constraint on this column. Before inserting, the service checks for an existing record with the same key. If found, it returns the existing record immediately (`already_processed=True`), preventing duplicate charges.

## 5. Concurrency Control
Before moving a payment to `PROCESSING`, workers execute:
`SELECT FOR UPDATE SKIP LOCKED`
This locks the specific payment row. If another worker attempts to process the same payment concurrently (e.g., from a duplicate Celery message), it will either be blocked or skip it, preventing double-processing.

## 6. Circuit Breaker
Protects the system from catastrophic cascading failures when the external gateway is completely down.
```text
          [Failure Threshold Exceeded]
  CLOSED -----------------------------> OPEN
    ^                                     |
    |                                     | [Recovery Timeout]
    |      [Probe Success]                |
    +------------------------- HALF_OPEN <+
                                  |
                                  | [Probe Failure]
                                  +--> OPEN
```

## 7. Webhook Handling
Three-path flow:
1. **Duplicate Callback**: Payment is already in the requested terminal state. No update, 200 OK.
2. **Conflicting Callback**: Payment is in a different terminal state. Stored state wins, logs `WEBHOOK_CONFLICT`.
3. **Early Callback**: Payment is `PENDING` or `PROCESSING`. Updates to new state.

## 8. Queue Architecture
`POST /payments/` handles initial validation, creates a `PENDING` record, and enqueues `process_payment_task`. HTTP responds 202 immediately. Celery workers pick up the task and execute the slow gateway simulation and retries asynchronously. To actively process the background queue, the worker must be manually started in a separate terminal using `python manage.py run_worker`.

## 9. Rate Limiting
Uses a sliding-window algorithm backed by a `defaultdict(deque)`. It tracks request timestamps per IP. When a new request comes in, it cleans up timestamps older than the `RATE_LIMIT_WINDOW` and checks if the remaining count exceeds `RATE_LIMIT_REQUESTS`. O(N) complexity for cleanup where N is requests within the window.

## 10. Database Schema
- **payments**: Stores current payment state, amount, idempotency_key, and retry_count.
- **payment_events**: Audit table recording every state transition and retry attempt with a Foreign Key to `payments`.

## 11. Production Upgrade Notes
- **Distributed Rate Limiter**: Replace in-memory deque with Redis Sorted Sets (ZADD timestamp, ZREMRANGEBYSCORE, ZCARD).
- **Distributed Circuit Breaker**: Replace in-memory state with Redis keys to share circuit breaker state across all worker nodes.
- **Webhook Security**: Add HMAC signature verification to validate the origin of incoming webhook requests.
