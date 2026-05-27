from typing import Any

from pydantic import BaseModel, Field


class FindingType:
    MISSING_MATERIAL = "MISSING_MATERIAL"
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    INCONSISTENT_IDENTITY = "INCONSISTENT_IDENTITY"
    INCONSISTENT_CREDENTIAL = "INCONSISTENT_CREDENTIAL"
    WATER_SOURCE_INCOMPLETE = "WATER_SOURCE_INCOMPLETE"
    WATER_AMOUNT_REVIEW_REQUIRED = "WATER_AMOUNT_REVIEW_REQUIRED"
    PERMIT_REQUIREMENT_REVIEW_REQUIRED = "PERMIT_REQUIREMENT_REVIEW_REQUIRED"
    PUBLIC_NOTICE_REVIEW_REQUIRED = "PUBLIC_NOTICE_REVIEW_REQUIRED"
    WATER_RESOURCE_ASSESSMENT_REVIEW_REQUIRED = "WATER_RESOURCE_ASSESSMENT_REVIEW_REQUIRED"
    MULTI_APPLICANT_UNSUPPORTED = "MULTI_APPLICANT_UNSUPPORTED"
    MULTI_WATER_SOURCE_UNSUPPORTED = "MULTI_WATER_SOURCE_UNSUPPORTED"
    OCR_LOW_CONFIDENCE = "OCR_LOW_CONFIDENCE"
    MODEL_UNCERTAIN = "MODEL_UNCERTAIN"
    SYSTEM_ERROR = "SYSTEM_ERROR"

    ALL = frozenset(
        {
            MISSING_MATERIAL,
            MISSING_FIELD,
            INVALID_FORMAT,
            INCONSISTENT_IDENTITY,
            INCONSISTENT_CREDENTIAL,
            WATER_SOURCE_INCOMPLETE,
            WATER_AMOUNT_REVIEW_REQUIRED,
            PERMIT_REQUIREMENT_REVIEW_REQUIRED,
            PUBLIC_NOTICE_REVIEW_REQUIRED,
            WATER_RESOURCE_ASSESSMENT_REVIEW_REQUIRED,
            MULTI_APPLICANT_UNSUPPORTED,
            MULTI_WATER_SOURCE_UNSUPPORTED,
            OCR_LOW_CONFIDENCE,
            MODEL_UNCERTAIN,
            SYSTEM_ERROR,
        }
    )


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
    material_slots: list[MaterialSlot] = Field(default_factory=list)
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
    basis_refs: list[str] = Field(default_factory=list)
    applicant_visible: bool = True


class RiskHint(BaseModel):
    risk_level: str
    description: str
    basis_refs: list[str] = Field(default_factory=list)
    requires_manual_review: bool = False


class MaterialCompleteness(BaseModel):
    received: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    unrecognized: list[str] = Field(default_factory=list)


class ModelMetadata(BaseModel):
    provider: str
    model: str
    request_id: str | None = None
    finish_reason: str | None = None
    token_usage: dict[str, int] = Field(default_factory=dict)


class ToolCallTrace(BaseModel):
    tool_name: str
    input_summary: str = ""
    output_summary: str = ""
    source_refs: list[str] = Field(default_factory=list)
    status: str = "SUCCESS"
    latency_ms: int | None = None
    error: str | None = None


class ReviewResult(BaseModel):
    summary: str = ""
    issues: list[Issue] = Field(default_factory=list)
    risk_hints: list[RiskHint] = Field(default_factory=list)
    draft_opinion: str = ""
    material_completeness: MaterialCompleteness = Field(default_factory=MaterialCompleteness)
    extracted_fields: list[ExtractedField] = Field(default_factory=list)
    basis_refs: list[str] = Field(default_factory=list)
    manual_review_notice: str = ""
    model_metadata: ModelMetadata | None = None
    tool_call_traces: list[ToolCallTrace] = Field(default_factory=list)


class ProcessingResult(BaseModel):
    task_id: str
    status: str
    result_summary: str = ""
    applicant_result: ReviewResult | None = None
    reviewer_result: ReviewResult | None = None
    error_message: str | None = None
    knowledge_pack_version: str | None = None
