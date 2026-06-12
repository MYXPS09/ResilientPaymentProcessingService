from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import api_router
from common.config import settings

app = FastAPI(
    title=settings.SERVICE_NAME,
    description=settings.SERVICE_DESCRIPTION,
    version=settings.SERVICE_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*", "x-client-key", "X-Client-Key"],
)

app.include_router(api_router, prefix="/api/v1")
