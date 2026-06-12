from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from common.config import settings

# Pool size formula: POOL_SIZE = max(5, (100 - 5) // WORKER_COUNT)
# Assuming 4 workers as per setup instructions
POOL_SIZE = max(5, (100 - 5) // 4)

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=POOL_SIZE,
    max_overflow=10,
    echo=settings.DEBUG,
)

async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
