import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

EXPORT_STATUSES = ("pending", "processing", "completed", "failed")
EXPORT_FORMATS = ("csv", "json")


class ExportJob(Base):
    __tablename__ = "export_jobs"
    __table_args__ = (
        CheckConstraint(f"status IN {EXPORT_STATUSES}", name="export_status_valid"),
        CheckConstraint(f"format IN {EXPORT_FORMATS}", name="export_format_valid"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    list_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lists.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(nullable=False, default="pending")
    format: Mapped[str] = mapped_column(nullable=False, default="json")
    file_path: Mapped[str | None] = mapped_column(nullable=True)
    error: Mapped[str | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="export_jobs")
    list: Mapped["List"] = relationship(back_populates="export_jobs")