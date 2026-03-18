"""Common schema helpers."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Base schema with ORM support."""

    model_config = ConfigDict(from_attributes=True)


class TimestampSchema(ORMModel):
    """Timestamp fields."""

    created_at: datetime
    updated_at: datetime
