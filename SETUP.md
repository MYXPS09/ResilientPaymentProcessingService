# Payment Gateway Service Setup

## Prerequisites
- Python 3.12+
- PostgreSQL 15+
- Redis 7+

## 1. Setup Environment
Clone the repository and create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
```

## 2. Install Dependencies
```bash
pip install -r requirements.txt
```

## 3. Configuration
Copy `.env.example` to `.env` and configure your settings:
```bash
cp .env.example .env
```
Ensure you set up `DATABASE_URL` and `REDIS_URL` correctly.

## 4. Infrastructure Setup
Start the required PostgreSQL and Redis services using Docker Compose:
```bash
docker-compose up -d
```

Run Alembic migrations to create tables (using the manage script):
```bash
python manage.py migrate-dev
```

## 5. Running the Application
Start the FastAPI server (using the manage script):
```bash
python manage.py run
```

Start the Celery worker (in a separate terminal):
```bash
python manage.py run_worker
```

### Other Database Management Commands
The `manage.py` script provides additional commands for your development workflow:
- `python manage.py makemigrations-dev -m "description"`: Generate a new migration script
- `python manage.py downgrade-dev -r <revision_id>`: Downgrade the database schema
- `python manage.py history`: View migration history
- `python manage.py current`: View current migration revision


## 6. Running Tests
Execute the pytest suite:
```bash
pytest tests/ -v
```

## 7. API Documentation
Visit the Swagger UI at: http://localhost:8000/docs

## 8. cURL Examples

**Create Payment**
```bash
curl -X POST http://localhost:8000/api/v1/payments/ \
  -H "X-Client-Key: your-secret-client-key-here" \
  -H "Content-Type: application/json" \
  -d '{"idempotency_key": "unique-key-123", "amount": 150.50, "currency": "INR"}'
```

**Get Payment by ID**
```bash
curl -X GET http://localhost:8000/api/v1/payments/1 \
  -H "X-Client-Key: your-secret-client-key-here"
```

**Get Audit Trail**
```bash
curl -X GET http://localhost:8000/api/v1/payments/1/events \
  -H "X-Client-Key: your-secret-client-key-here"
```

**Retry Payment**
```bash
curl -X POST http://localhost:8000/api/v1/payments/1/retry \
  -H "X-Client-Key: your-secret-client-key-here"
```

**Webhook Callback**
```bash
curl -X POST http://localhost:8000/api/v1/payments/webhook/callback \
  -H "Content-Type: application/json" \
  -d '{"gateway_ref": "GW-12345", "status": "SUCCESS"}'
```

## 9. UI Simulator
We have included a full **single-file frontend simulator** that perfectly integrates with the FastAPI backend.
- Open `payment-simulator.html` in your web browser.
- By default, it operates in **Mock Mode**, simulating a payment gateway purely with JavaScript.
- Toggle the **Live API Mode** in the navigation bar to connect directly to your local FastAPI backend (`http://localhost:8000`), allowing you to observe real API calls, DB transitions, and queue processing live within the interactive Admin Dashboard.

**Circuit Breaker Status**
```bash
curl -X GET http://localhost:8000/api/v1/payments/gateway/circuit-status
```
