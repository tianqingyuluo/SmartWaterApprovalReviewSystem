from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ApiMaterialSlot(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    material_type: str = Field(alias="materialType")
    original_file_name: str | None = Field(default=None, alias="originalFileName")
    storage_key: str | None = Field(default=None, alias="storageKey")
    file_extension: str | None = Field(default=None, alias="fileExtension")
    uploaded: bool = False


class CreateReviewTaskRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    task_id: str = Field(alias="taskId", min_length=1)
    session_id: str = Field(alias="sessionId", min_length=1)
    materials: list[ApiMaterialSlot] = Field(default_factory=list)
    idempotency_key: str | None = Field(default=None, alias="idempotencyKey")


class CreateReviewTaskResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ai_task_id: str = Field(alias="aiTaskId")
    status: str
    created_at: datetime = Field(alias="createdAt")


class TaskStatusResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ai_task_id: str = Field(alias="aiTaskId")
    status: str
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    result: dict[str, Any] | None = None
    error_message: str | None = Field(default=None, alias="errorMessage")


class HealthResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: str
    service: str
    knowledge_pack_version: str | None = Field(default=None, alias="knowledgePackVersion")
