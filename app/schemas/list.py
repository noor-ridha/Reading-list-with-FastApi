import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ListCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class ListUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class ListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class ListPage(BaseModel):
    items: list[ListOut]
    total: int
    limit: int
    offset: int