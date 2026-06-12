from fastapi import HTTPException, status, Security, Request
from fastapi.security import APIKeyHeader
from common.config import settings

api_key_header = APIKeyHeader(name="X-Client-Key", auto_error=False)

async def get_api_client(request: Request, api_key: str = Security(api_key_header)) -> str:
    # Fallback to direct header extraction if Security() fails
    actual_key = api_key or request.headers.get("x-client-key") or request.headers.get("X-Client-Key")
    
    # Strip any spaces, newlines, or literal quotes from both sides
    clean_incoming = actual_key.strip().strip('"').strip("'") if actual_key else None
    clean_settings = settings.API_CLIENT_KEY.strip().strip('"').strip("'")
    
    print(f"DEBUG AUTH - Incoming: '{clean_incoming}' | Expected: '{clean_settings}'")
    
    if not clean_incoming or clean_incoming != clean_settings:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or missing X-Client-Key header"
        )
    return clean_incoming
