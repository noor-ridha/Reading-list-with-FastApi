import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

ExportFormat = Literal["csv", "json"]
ExportStatus = Literal["pending", "processing", "completed", "failed"]


class ExportJobCreate(BaseModel):
    format: ExportFormat = "json"


class ExportJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    list_id: uuid.UUID
    status: ExportStatus
    format: ExportFormat
    error: str | None
    created_at: datetime
    completed_at: datetime | None