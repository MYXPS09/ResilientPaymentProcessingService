from typing import Type, TypeVar, Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from common.exceptions.base import NotFoundException, InternalServerError, BadRequestException

T = TypeVar('T')

class BaseOperations:
    def __init__(self, session: AsyncSession, model_class: Type[T]):
        self.session = session
        self.model_class = model_class
        self.class_name = model_class.__name__

    async def create(self, data: Dict[str, Any]) -> T:
        try:
            model = self.model_class(**data)
            self.session.add(model)
            await self.session.flush()
            await self.session.refresh(model)
            return model
        except Exception as exc:
            await self.session.rollback()
            raise InternalServerError("Failed to create record") from exc

    async def update(self, obj: T, data: Dict[str, Any]) -> T:
        try:
            for key, value in data.items():
                setattr(obj, key, value)
            self.session.add(obj)
            await self.session.flush()
            await self.session.refresh(obj)
            return obj
        except Exception as exc:
            await self.session.rollback()
            raise InternalServerError("Failed to update record") from exc

    async def faf_one_by_id(self, obj_id: int) -> T:
        stmt = select(self.model_class).where(self.model_class.id == obj_id, self.model_class.is_deleted == False)
        result = await self.session.execute(stmt)
        obj = result.scalar_one_or_none()
        if not obj:
            raise NotFoundException(detail=f"{self.class_name} with id {obj_id} not found")
        return obj

    async def get_by_field(self, field_name: str, value: Any) -> Optional[T]:
        if not hasattr(self.model_class, field_name):
            raise BadRequestException(detail=f"Field {field_name} does not exist on {self.class_name}")
        stmt = select(self.model_class).where(getattr(self.model_class, field_name) == value, self.model_class.is_deleted == False)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_by_field(self, field_name: str, value: Any) -> List[T]:
        if not hasattr(self.model_class, field_name):
            raise BadRequestException(detail=f"Field {field_name} does not exist on {self.class_name}")
        stmt = select(self.model_class).where(getattr(self.model_class, field_name) == value, self.model_class.is_deleted == False)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def soft_delete(self, obj: T, updated_by: int = 1) -> T:
        return await self.update(obj, {"is_deleted": True, "updated_by": updated_by})
