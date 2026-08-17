from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.domain import TimestampMixin, utcnow


class ImportRunStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class ImportSource(TimestampMixin, Base):
    __tablename__ = "import_sources"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(150), unique=True)
    provider_type: Mapped[str] = mapped_column(String(50), default="json_http")
    endpoint_url: Mapped[str] = mapped_column(String(1000))
    interval_minutes: Mapped[int] = mapped_column(Integer, default=60)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    configuration: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    runs: Mapped[list["ImportRun"]] = relationship(back_populates="source")


class ImportRun(Base):
    __tablename__ = "import_runs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("import_sources.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[ImportRunStatus] = mapped_column(
        Enum(ImportRunStatus, name="import_run_status"), default=ImportRunStatus.RUNNING
    )
    trigger: Mapped[str] = mapped_column(String(30))
    received: Mapped[int] = mapped_column(Integer, default=0)
    created: Mapped[int] = mapped_column(Integer, default=0)
    updated: Mapped[int] = mapped_column(Integer, default=0)
    unchanged: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source: Mapped[ImportSource] = relationship(back_populates="runs")
