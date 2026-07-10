import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ItemStatus = Literal["want_to_read", "reading", "finished"]


class ItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    status: ItemStatus = "want_to_read"


class ItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    status: ItemStatus | None = None


class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    list_id: uuid.UUID
    title: str
    status: str
    created_at: datetime
    updated_at: datetime


class ItemPage(BaseModel):
    items: list[ItemOut]
    total: int
    limit: int
    offset: int