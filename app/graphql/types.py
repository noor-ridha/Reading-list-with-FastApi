import uuid
from datetime import datetime

import strawberry


@strawberry.type
class ItemType:
    id: uuid.UUID
    title: str
    status: str
    created_at: datetime


@strawberry.type
class ListType:
    id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
    items: list[ItemType]


@strawberry.type
class ExportJobType:
    id: uuid.UUID
    status: str
    format: str
    error: str | None