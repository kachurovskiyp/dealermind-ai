from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.automation import ImportRunStatus


class ImportSourceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    provider_type: Literal["json_http", "otomoto_search"] = "json_http"
    endpoint_url: HttpUrl
    interval_minutes: int = Field(default=60, ge=1, le=10_080)
    enabled: bool = True
    configuration: dict[str, object] = Field(default_factory=dict)


class ImportSourceUpdate(BaseModel):
    endpoint_url: HttpUrl | None = None
    interval_minutes: int | None = Field(default=None, ge=1, le=10_080)
    enabled: bool | None = None


class ImportSourceRead(BaseModel):
    id: UUID
    name: str
    provider_type: str
    endpoint_url: str
    interval_minutes: int
    enabled: bool
    next_run_at: datetime | None
    last_run_at: datetime | None
    configuration: dict[str, object]
    model_config = ConfigDict(from_attributes=True)


class ImportRunRead(BaseModel):
    id: UUID
    source_id: UUID
    status: ImportRunStatus
    trigger: str
    received: int
    created: int
    updated: int
    unchanged: int
    error_count: int
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None
    model_config = ConfigDict(from_attributes=True)
