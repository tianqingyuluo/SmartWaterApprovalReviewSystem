from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, status

from knowledge_pack import KnowledgePackError, load_knowledge_pack, normalize_knowledge_fragments
from src.api.models import (
    CompletenessToolRequest,
    CreateReviewTaskRequest,
    CreateReviewTaskResponse,
    HealthResponse,
    KnowledgeSearchToolRequest,
    TaskStatusResponse,
)
from src.config import config
from src.mcp_server.server import build_mcp_server
from src.services.fastapi_task_store import InMemoryTaskStore
from src.services.mcp_client import SmartWaterMcpClient
from src.services.result_writer import ResultWriter, _result_to_dict
from src.services.review_orchestrator import ReviewTaskOrchestrator

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(UTC)


class FastapiReviewRuntime:
    def __init__(self) -> None:
        self.store = InMemoryTaskStore()
        self.writer = ResultWriter()
        self.knowledge_pack_version: str | None = None
        self._knowledge_fragments: list[dict[str, str]] = []
        self._knowledge_loaded = False

    def ensure_knowledge_loaded(self) -> None:
        if self._knowledge_loaded:
            return
        pack = self._load_knowledge_pack()
        self.knowledge_pack_version = str(pack.get("version") or "") or None
        self._knowledge_fragments = normalize_knowledge_fragments(pack)
        self._knowledge_loaded = True
        logger.info(
            "FastAPI runtime loaded knowledge pack version=%s fragments=%d",
            self.knowledge_pack_version,
            len(self._knowledge_fragments),
        )

    def create_task(self, request: CreateReviewTaskRequest) -> dict[str, Any]:
        task_id = request.task_id
        existing = self.store.get(task_id)
        if existing:
            return existing
        payload = request.model_dump(by_alias=True)
        return self.store.create(task_id, payload)

    def process_task(self, payload: dict[str, Any]) -> None:
        task_id = str(payload.get("taskId") or "").strip()
        if not task_id:
            return

        self.store.mark_processing(task_id)
        status_ok = self.writer.update_status(task_id, "PROCESSING")
        if not status_ok:
            logger.warning("Failed to sync PROCESSING status to Java backend for task %s", task_id)

        try:
            self.ensure_knowledge_loaded()
            orchestrator = ReviewTaskOrchestrator(
                mcp_client=SmartWaterMcpClient(),
                knowledge_fragments=self._knowledge_fragments,
                knowledge_pack_version=self.knowledge_pack_version,
            )
            result = orchestrator.process_task(payload)
        except Exception as exc:
            logger.error("FastAPI background processing failed for task %s: %s", task_id, exc)
            self.store.mark_failed(task_id, f"processing failed: {exc}")
            self.writer.update_status(task_id, "FAILED")
            return

        if not self.writer.write_results(task_id, result):
            message = "result callback failed after retries"
            self.store.mark_failed(task_id, message)
            self.writer.update_status(task_id, "FAILED")
            return

        self.store.mark_result(
            task_id,
            {
                "status": result.status,
                "resultSummary": result.result_summary,
                "knowledgePackVersion": result.knowledge_pack_version,
                "applicantResult": _result_to_dict(result.applicant_result),
                "reviewerResult": _result_to_dict(result.reviewer_result),
            },
        )

    def _load_knowledge_pack(self) -> dict[str, Any]:
        pack_dir = config.KNOWLEDGE_PACK_DIR
        if not os.path.isdir(pack_dir):
            raise KnowledgePackError(f"Knowledge pack directory not found: {pack_dir}")

        preferred_pack = os.path.join(pack_dir, "water_permit_mvp.json")
        if os.path.isfile(preferred_pack):
            return load_knowledge_pack(preferred_pack)

        for filename in os.listdir(pack_dir):
            if not filename.endswith(".json"):
                continue
            return load_knowledge_pack(os.path.join(pack_dir, filename))

        raise KnowledgePackError(f"No JSON knowledge pack found under: {pack_dir}")


runtime = FastapiReviewRuntime()


def _check_internal_token(x_internal_token: str | None = Header(default=None)) -> None:
    required_token = config.INTERNAL_API_TOKEN.strip()
    if not required_token:
        return
    if (x_internal_token or "") != required_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid internal token")


def _mcp_call_result_to_dict(result: Any) -> dict[str, Any]:
    content = getattr(result, "content", result)
    if isinstance(content, list):
        for item in content:
            text = getattr(item, "text", None)
            if text:
                parsed = json.loads(text)
                return parsed if isinstance(parsed, dict) else {"result": parsed}
    return result if isinstance(result, dict) else {"result": result}


async def _call_mcp_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    server = build_mcp_server(
        enable_vector_search=False,
        precompute_json_embeddings=False,
    )
    result = await server.call_tool(name, arguments)
    return _mcp_call_result_to_dict(result)


app = FastAPI(
    title="SmartWater Review FastAPI",
    version="0.1.0",
    description="CP3-B FastAPI review task mainline for SmartWater",
)


@app.get("/health", response_model=HealthResponse, tags=["ops"])
def health() -> HealthResponse:
    try:
        runtime.ensure_knowledge_loaded()
        return HealthResponse(
            status="ok",
            service="smart-water-review-fastapi",
            knowledgePackVersion=runtime.knowledge_pack_version,
        )
    except Exception as exc:
        logger.warning("Health degraded: %s", exc)
        return HealthResponse(
            status="degraded",
            service="smart-water-review-fastapi",
            knowledgePackVersion=runtime.knowledge_pack_version,
        )


@app.post("/api/mcp/tools/knowledge_search", tags=["mcp-tools"])
async def call_knowledge_search_tool(
    request: KnowledgeSearchToolRequest,
    _auth: None = Depends(_check_internal_token),
) -> dict[str, Any]:
    return await _call_mcp_tool(
        "knowledge_search",
        {
            "query": request.query,
            "top_k": request.top_k,
        },
    )


@app.post("/api/mcp/tools/check_completeness", tags=["mcp-tools"])
async def call_check_completeness_tool(
    request: CompletenessToolRequest,
    _auth: None = Depends(_check_internal_token),
) -> dict[str, Any]:
    return await _call_mcp_tool(
        "check_completeness",
        {
            "materials": request.materials,
        },
    )


@app.post(
    "/api/review/tasks",
    response_model=CreateReviewTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["review-task"],
)
def create_review_task(
    request: CreateReviewTaskRequest,
    background_tasks: BackgroundTasks,
    _auth: None = Depends(_check_internal_token),
) -> CreateReviewTaskResponse:
    record = runtime.create_task(request)
    ai_task_id = str(record.get("aiTaskId") or request.task_id)
    if str(record.get("status")) == "QUEUED":
        background_tasks.add_task(runtime.process_task, request.model_dump(by_alias=True))
    return CreateReviewTaskResponse(
        aiTaskId=ai_task_id,
        status=str(record.get("status") or "QUEUED"),
        createdAt=record.get("createdAt") or _utc_now(),
    )


@app.get("/api/review/tasks/{ai_task_id}", response_model=TaskStatusResponse, tags=["review-task"])
def get_review_task_status(
    ai_task_id: str,
    _auth: None = Depends(_check_internal_token),
) -> TaskStatusResponse:
    record = runtime.store.get(ai_task_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskStatusResponse(
        aiTaskId=record["aiTaskId"],
        status=record["status"],
        createdAt=record["createdAt"],
        updatedAt=record["updatedAt"],
        result=record["result"],
        errorMessage=record["errorMessage"],
    )
