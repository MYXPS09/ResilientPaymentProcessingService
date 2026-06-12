from datetime import datetime
import uuid

def generate_payment_num() -> str:
    # PAY-{YYYYMMDDHHMMSS}-{6 uppercase alphanumeric chars}
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_str = uuid.uuid4().hex[:6].upper()
    return f"PAY-{timestamp}-{random_str}"
