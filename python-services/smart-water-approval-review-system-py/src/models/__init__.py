from pydantic import BaseModel
from typing import Optional, Any


class MaterialSlot(BaseModel):
    material_type: str
    original_file_name: str | None = None
    storage_key: str | None = None
    file_extension: str | None = None
    uploaded: bool = False


class ReviewTask(BaseModel):
    task_id: str
    session_id: str
    status: str
    material_slots: list[MaterialSlot] = []
    knowledge_pack_version: str | None = None


class ExtractedField(BaseModel):
    field_key: str
    field_value: Any | None = None
    confidence: float = 0.0
    source_material: str | None = None
    evidence: str | None = None


class KnowledgeFragment(BaseModel):
    source_id: str
    source_title: str
    content: str


class Issue(BaseModel):
    code: str
    severity: str
    message: str
    material_type: str | None = None
    field_key: str | None = None
    basis_refs: list[str] = []
    applicant_visible: bool = True


class RiskHint(BaseModel):
    risk_level: str
    description: str
    basis_refs: list[str] = []
    requires_manual_review: bool = False


class MaterialCompleteness(BaseModel):
    received: list[str] = []
    missing: list[str] = []
    unrecognized: list[str] = []


class ModelMetadata(BaseModel):
    provider: str
    model: str
    request_id: str | None = None
    finish_reason: str | None = None
    token_usage: dict[str, int] = {}


class ReviewResult(BaseModel):
    summary: str = ""
    issues: list[Issue] = []
    risk_hints: list[RiskHint] = []
    draft_opinion: str = ""
    material_completeness: MaterialCompleteness = MaterialCompleteness()
    basis_refs: list[str] = []
    manual_review_notice: str = ""
    model_metadata: ModelMetadata | None = None


class ProcessingResult(BaseModel):
    task_id: str
    status: str
    result_summary: str = ""
    applicant_result: ReviewResult | None = None
    reviewer_result: ReviewResult | None = None
    error_message: str | None = None
