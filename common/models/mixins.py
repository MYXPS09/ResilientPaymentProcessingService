from sqlalchemy import DateTime, BigInteger, Boolean, Column, func, String
from sqlalchemy.orm import declared_attr

class CommonFieldMixin:
    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=func.now(), nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    @declared_attr
    def created_by(cls):
        return Column(BigInteger, nullable=False, default=1)

    @declared_attr
    def updated_by(cls):
        return Column(BigInteger, nullable=False, default=1)

    @declared_attr
    def is_deleted(cls):
        return Column(Boolean, nullable=True, default=False)

    @declared_attr
    def modified_by(cls):
        return Column(String(32), nullable=True, default=None)
