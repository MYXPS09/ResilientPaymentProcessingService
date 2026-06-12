import pytest
from unittest.mock import patch, AsyncMock
from module.payment.payment_schema import PaymentStatus
from common.gateway.simulator import GatewayOutcome, GatewayResponse
from common.models.payment import Payment
from common.gateway.circuit_breaker import gateway_circuit_breaker, CircuitState

@pytest.mark.asyncio
@patch("common.tasks.payment_tasks.process_payment_task.delay")
async def test_create_happy_path(mock_delay, async_client, api_headers, db_session):
    data = {"idempotency_key": "test_idem_1", "amount": 100.0}
    response = await async_client.post("/api/v1/payments/", json=data, headers=api_headers)
    assert response.status_code == 202
    assert response.json()["status"] == PaymentStatus.PENDING
    payment_id = response.json()["id"]
    
    # Simulate processing
    with patch("common.tasks.payment_tasks.call_external_gateway", new_callable=AsyncMock) as mock_gw:
        mock_gw.return_value = GatewayResponse(outcome=GatewayOutcome.SUCCESS, gateway_ref="GW-REF", message="Success")
        from common.tasks.payment_tasks import process_payment_async
        await process_payment_async(payment_id)
        
    response2 = await async_client.get(f"/api/v1/payments/{payment_id}", headers=api_headers)
    assert response2.json()["status"] == PaymentStatus.SUCCESS

@pytest.mark.asyncio
@patch("common.tasks.payment_tasks.process_payment_task.delay")
async def test_gateway_failure_exhausts_retries(mock_delay, async_client, api_headers, db_session):
    data = {"idempotency_key": "test_idem_2", "amount": 50.0}
    res = await async_client.post("/api/v1/payments/", json=data, headers=api_headers)
    payment_id = res.json()["id"]
    
    with patch("common.tasks.payment_tasks.call_external_gateway", new_callable=AsyncMock) as mock_gw:
        mock_gw.return_value = GatewayResponse(outcome=GatewayOutcome.FAILED, gateway_ref=None, message="Failed")
        # To avoid actual sleep, we can mock asyncio.sleep as well
        with patch("asyncio.sleep", new_callable=AsyncMock):
            from common.tasks.payment_tasks import process_payment_async
            await process_payment_async(payment_id)
            
    res2 = await async_client.get(f"/api/v1/payments/{payment_id}", headers=api_headers)
    assert res2.json()["status"] == PaymentStatus.FAILED

@pytest.mark.asyncio
@patch("common.tasks.payment_tasks.process_payment_task.delay")
async def test_idempotency(mock_delay, async_client, api_headers):
    data = {"idempotency_key": "idem_3", "amount": 20.0}
    r1 = await async_client.post("/api/v1/payments/", json=data, headers=api_headers)
    r2 = await async_client.post("/api/v1/payments/", json=data, headers=api_headers)
    
    assert r1.status_code == 202
    assert r2.status_code == 202
    assert r1.json()["id"] == r2.json()["id"]
    assert r2.json()["already_processed"] == True

@pytest.mark.asyncio
@patch("common.tasks.payment_tasks.process_payment_task.delay")
async def test_retry_endpoint(mock_delay, async_client, api_headers):
    # Setup FAILED payment
    data = {"idempotency_key": "idem_retry_1", "amount": 30.0}
    res = await async_client.post("/api/v1/payments/", json=data, headers=api_headers)
    payment_id = res.json()["id"]
    
    with patch("common.tasks.payment_tasks.call_external_gateway", new_callable=AsyncMock) as mock_gw:
        mock_gw.return_value = GatewayResponse(outcome=GatewayOutcome.FAILED, gateway_ref=None, message="Failed")
        with patch("asyncio.sleep", new_callable=AsyncMock):
            from common.tasks.payment_tasks import process_payment_async
            await process_payment_async(payment_id)
            
    r_retry = await async_client.post(f"/api/v1/payments/{payment_id}/retry", headers=api_headers)
    assert r_retry.status_code == 200
    assert mock_delay.called

@pytest.mark.asyncio
async def test_retry_blocked(async_client, api_headers):
    # Fast path: Insert SUCCESS payment via API
    data = {"idempotency_key": "idem_blocked", "amount": 30.0}
    res = await async_client.post("/api/v1/payments/", json=data, headers=api_headers)
    payment_id = res.json()["id"]
    
    with patch("common.tasks.payment_tasks.call_external_gateway", new_callable=AsyncMock) as mock_gw:
        mock_gw.return_value = GatewayResponse(outcome=GatewayOutcome.SUCCESS, gateway_ref="GW-REF", message="Success")
        from common.tasks.payment_tasks import process_payment_async
        await process_payment_async(payment_id)
        
    r_retry = await async_client.post(f"/api/v1/payments/{payment_id}/retry", headers=api_headers)
    assert r_retry.status_code == 400

@pytest.mark.asyncio
async def test_webhook_success_updates_failed(async_client, api_headers):
    data = {"idempotency_key": "idem_wh", "amount": 30.0}
    res = await async_client.post("/api/v1/payments/", json=data, headers=api_headers)
    payment_id = res.json()["id"]
    
    # Make it FAILED
    with patch("common.tasks.payment_tasks.call_external_gateway", new_callable=AsyncMock) as mock_gw:
        mock_gw.return_value = GatewayResponse(outcome=GatewayOutcome.FAILED, gateway_ref=None, message="Failed")
        with patch("asyncio.sleep", new_callable=AsyncMock):
            from common.tasks.payment_tasks import process_payment_async
            await process_payment_async(payment_id)
    
    # We need a gateway_ref. Let's patch DB
    # Manually setting gateway_ref for test
    from module.payment.payment_repository import PaymentRepository
    from common.database import async_session_maker
    async with async_session_maker() as session:
        repo = PaymentRepository(session)
        payment = await repo.bo.faf_one_by_id(payment_id)
        await repo.bo.update(payment, {"gateway_ref": "WH_REF"})
    
    wh_data = {"gateway_ref": "WH_REF", "status": PaymentStatus.SUCCESS}
    wh_res = await async_client.post("/api/v1/payments/webhook/callback", json=wh_data)
    assert wh_res.status_code == 200
    assert wh_res.json()["status"] == PaymentStatus.SUCCESS

@pytest.mark.asyncio
async def test_duplicate_webhook(async_client, api_headers):
    data = {"idempotency_key": "idem_wh2", "amount": 30.0}
    res = await async_client.post("/api/v1/payments/", json=data, headers=api_headers)
    payment_id = res.json()["id"]
    
    from module.payment.payment_repository import PaymentRepository
    from common.database import async_session_maker
    async with async_session_maker() as session:
        repo = PaymentRepository(session)
        payment = await repo.bo.faf_one_by_id(payment_id)
        await repo.bo.update(payment, {"gateway_ref": "WH_REF_2", "status": PaymentStatus.SUCCESS})
        
    wh_data = {"gateway_ref": "WH_REF_2", "status": PaymentStatus.SUCCESS}
    r1 = await async_client.post("/api/v1/payments/webhook/callback", json=wh_data)
    r2 = await async_client.post("/api/v1/payments/webhook/callback", json=wh_data)
    
    assert r1.status_code == 200
    assert r2.status_code == 200

@pytest.mark.asyncio
async def test_conflicting_webhook(async_client, api_headers):
    data = {"idempotency_key": "idem_wh3", "amount": 30.0}
    res = await async_client.post("/api/v1/payments/", json=data, headers=api_headers)
    payment_id = res.json()["id"]
    
    from module.payment.payment_repository import PaymentRepository
    from common.database import async_session_maker
    async with async_session_maker() as session:
        repo = PaymentRepository(session)
        payment = await repo.bo.faf_one_by_id(payment_id)
        await repo.bo.update(payment, {"gateway_ref": "WH_REF_3", "status": PaymentStatus.SUCCESS})
        
    wh_data = {"gateway_ref": "WH_REF_3", "status": PaymentStatus.FAILED}
    wh_res = await async_client.post("/api/v1/payments/webhook/callback", json=wh_data)
    
    assert wh_res.status_code == 200
    assert wh_res.json()["status"] == PaymentStatus.SUCCESS # Stored wins

@pytest.mark.asyncio
async def test_audit_trail(async_client, api_headers):
    data = {"idempotency_key": "idem_audit", "amount": 30.0}
    res = await async_client.post("/api/v1/payments/", json=data, headers=api_headers)
    payment_id = res.json()["id"]
    
    events_res = await async_client.get(f"/api/v1/payments/{payment_id}/events", headers=api_headers)
    assert events_res.status_code == 200
    assert len(events_res.json()) >= 1
    assert events_res.json()[0]["event_type"] == "INITIATED"

@pytest.mark.asyncio
async def test_validation(async_client, api_headers):
    data_neg = {"idempotency_key": "idem_v1", "amount": -10.0}
    res_neg = await async_client.post("/api/v1/payments/", json=data_neg, headers=api_headers)
    assert res_neg.status_code == 422
    
    data_zero = {"idempotency_key": "idem_v2", "amount": 0.0}
    res_zero = await async_client.post("/api/v1/payments/", json=data_zero, headers=api_headers)
    assert res_zero.status_code == 422

@pytest.mark.asyncio
async def test_auth(async_client):
    data = {"idempotency_key": "idem_auth", "amount": 10.0}
    res = await async_client.post("/api/v1/payments/", json=data) # no headers
    assert res.status_code == 401

@pytest.mark.asyncio
async def test_rate_limit(async_client, api_headers):
    # Simulate multiple hits to trigger 429
    # RATE_LIMIT_REQUESTS is 10
    from common.config import settings
    # Override limit for testing
    old_limit = settings.RATE_LIMIT_REQUESTS
    settings.RATE_LIMIT_REQUESTS = 2
    
    await async_client.post("/api/v1/payments/", json={"idempotency_key": "rl1", "amount": 10}, headers=api_headers)
    await async_client.post("/api/v1/payments/", json={"idempotency_key": "rl2", "amount": 10}, headers=api_headers)
    
    res = await async_client.post("/api/v1/payments/", json={"idempotency_key": "rl3", "amount": 10}, headers=api_headers)
    assert res.status_code == 429
    
    settings.RATE_LIMIT_REQUESTS = old_limit

@pytest.mark.asyncio
async def test_not_found(async_client, api_headers):
    res = await async_client.get("/api/v1/payments/99999", headers=api_headers)
    assert res.status_code == 404

@pytest.mark.asyncio
async def test_circuit_status(async_client):
    res = await async_client.get("/api/v1/payments/gateway/circuit-status")
    assert res.status_code == 200
    assert "state" in res.json()
