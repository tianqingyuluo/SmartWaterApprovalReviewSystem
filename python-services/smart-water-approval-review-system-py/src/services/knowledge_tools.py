from __future__ import annotations

import logging
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from knowledge_pack import load_knowledge_pack

logger = logging.getLogger(__name__)

MVP_REQUIRED_MATERIAL_TYPES = ("APPLICATION_FORM", "BUSINESS_LICENSE", "ID_CARD")

_MIN_VECTOR_SIMILARITY = 0.3


@dataclass(frozen=True)
class ChecklistItem:
    item_id: str
    material_type: str
    display_name: str
    required: bool
    source_refs: list[str]
    basis_refs: list[str]
    missing_finding_code: str
    missing_finding_severity: str
    missing_finding_message_for_applicant: str
    missing_finding_message_for_reviewer: str


def _tokenize(text: str) -> list[str]:
    normalized = text.strip().lower()
    if not normalized:
        return []
    return [part for part in normalized.replace("_", " ").replace("-", " ").split() if part]


def _as_str_list(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    result: list[str] = []
    for item in value:
        if item is None:
            continue
        text = str(item).strip()
        if text:
            result.append(text)
    return result


def _normalize_material_token(value: str) -> str:
    return value.strip().upper()


def _extract_material_type(item: Any) -> str | None:
    if isinstance(item, str):
        normalized = _normalize_material_token(item)
        return normalized if normalized in MVP_REQUIRED_MATERIAL_TYPES else None
    if isinstance(item, Mapping):
        for key in ("materialType", "material_type", "type", "name"):
            if key in item:
                normalized = _normalize_material_token(str(item[key]))
                if normalized and normalized in MVP_REQUIRED_MATERIAL_TYPES:
                    return normalized
    return None


def _review_basis_by_id(pack: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    review_basis = pack.get("reviewBasis", [])
    if not isinstance(review_basis, list):
        return result
    for item in review_basis:
        if isinstance(item, dict):
            item_id = str(item.get("id") or "").strip()
            if item_id:
                result[item_id] = item
    return result


def _source_ids_for_item(item: Mapping[str, Any], basis_lookup: Mapping[str, dict[str, Any]]) -> list[str]:
    source_ids = _as_str_list(item.get("sourceRefs", []))

    direct_source_id = str(item.get("sourceId") or "").strip()
    if direct_source_id:
        source_ids.append(direct_source_id)

    for ref in _as_str_list(item.get("basisRefs", [])):
        basis = basis_lookup.get(ref)
        if not basis:
            continue
        basis_source_id = str(basis.get("sourceId") or "").strip()
        if basis_source_id:
            source_ids.append(basis_source_id)

    deduplicated: list[str] = []
    seen: set[str] = set()
    for source_id in source_ids:
        if source_id in seen:
            continue
        seen.add(source_id)
        deduplicated.append(source_id)
    return deduplicated


def _build_excerpt(item: Mapping[str, Any], basis_lookup: Mapping[str, dict[str, Any]]) -> str:
    summary = str(item.get("summary") or "").strip()
    if summary:
        return summary
    instruction = str(item.get("instruction") or "").strip()
    if instruction:
        return instruction
    text = str(item.get("text") or "").strip()
    if text:
        return text

    refs = _as_str_list(item.get("basisRefs", []))
    for ref in refs:
        basis = basis_lookup.get(ref)
        if basis:
            basis_summary = str(basis.get("summary") or "").strip()
            if basis_summary:
                return basis_summary
    return ""


def _build_search_text(item: Mapping[str, Any], basis_lookup: Mapping[str, dict[str, Any]]) -> str:
    values: list[str] = []
    candidate_keys = (
        "id",
        "materialType",
        "displayName",
        "fieldPath",
        "sourceTitle",
        "category",
        "kind",
        "trigger",
        "reason",
        "findingCode",
        "summary",
        "instruction",
        "text",
        "messageForApplicant",
        "messageForReviewer",
    )
    for key in candidate_keys:
        raw = item.get(key)
        if raw is None:
            continue
        values.append(str(raw))

    for ref in _as_str_list(item.get("basisRefs", [])):
        basis = basis_lookup.get(ref)
        if not basis:
            continue
        values.append(str(basis.get("sourceTitle") or ""))
        values.append(str(basis.get("summary") or ""))

    return " ".join(values).lower()


def _score_match(query_tokens: Sequence[str], searchable_text: str) -> int:
    if not query_tokens or not searchable_text:
        return 0
    score = 0
    for token in query_tokens:
        if token in searchable_text:
            score += 1
    return score


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class SmartWaterKnowledgeTools:
    def __init__(
        self,
        knowledge_pack: dict[str, Any] | None = None,
        chroma_store: Any | None = None,
        embedding_client: Any | None = None,
        precompute_json_embeddings: bool = True,
    ) -> None:
        self._pack = knowledge_pack if knowledge_pack is not None else load_knowledge_pack()
        self._version = str(self._pack.get("version") or "")
        self._basis_lookup = _review_basis_by_id(self._pack)
        self._checklist = self._build_checklist()

        self._chroma_store = chroma_store
        self._embedding_client = embedding_client
        self._json_item_embeddings: list[tuple[list[float], dict[str, Any], str]] = []

        if self._embedding_client is not None and precompute_json_embeddings:
            self._precompute_json_embeddings()

    @property
    def knowledge_pack_version(self) -> str:
        return self._version

    def _build_checklist(self) -> list[ChecklistItem]:
        items: list[ChecklistItem] = []
        for raw in self._pack.get("materialChecklist", []):
            if not isinstance(raw, dict):
                continue

            missing_finding = raw.get("missingFinding", {})
            if not isinstance(missing_finding, dict):
                missing_finding = {}

            items.append(
                ChecklistItem(
                    item_id=str(raw.get("id") or "").strip(),
                    material_type=str(raw.get("materialType") or "").strip(),
                    display_name=str(raw.get("displayName") or "").strip(),
                    required=bool(raw.get("requiredForCompleteReview", False)),
                    source_refs=_as_str_list(raw.get("sourceRefs", [])),
                    basis_refs=_as_str_list(raw.get("basisRefs", [])),
                    missing_finding_code=str(missing_finding.get("code") or "MISSING_MATERIAL"),
                    missing_finding_severity=str(missing_finding.get("severity") or "WARNING"),
                    missing_finding_message_for_applicant=str(
                        missing_finding.get("messageForApplicant") or "缺少必需材料。"
                    ),
                    missing_finding_message_for_reviewer=str(
                        missing_finding.get("messageForReviewer") or "缺少必需材料，需人工补充核对。"
                    ),
                )
            )

        return items

    def _precompute_json_embeddings(self) -> None:
        sections = (
            "materialChecklist",
            "applicationFieldRules",
            "reviewBasis",
            "promptSnippets",
            "manualReviewRules",
        )
        items_text: list[str] = []
        items_meta: list[tuple[dict[str, Any], str]] = []

        for section in sections:
            section_items = self._pack.get(section, [])
            if not isinstance(section_items, list):
                continue
            for raw_item in section_items:
                if not isinstance(raw_item, dict):
                    continue
                text = _build_search_text(raw_item, self._basis_lookup)
                items_text.append(text)
                items_meta.append((raw_item, section))

        if not items_text:
            return

        try:
            all_embeddings = self._embedding_client.embed(items_text)
            for emb, (raw_item, section) in zip(all_embeddings, items_meta, strict=False):
                self._json_item_embeddings.append((emb, raw_item, section))
            logger.info(
                "Pre-computed embeddings for %d JSON knowledge pack items",
                len(self._json_item_embeddings),
            )
        except Exception as e:
            logger.warning(
                "Failed to pre-compute JSON item embeddings: %s. "
                "Vector search will only return document chunks.",
                e,
            )
            self._json_item_embeddings = []

    def _chroma_populated(self) -> bool:
        if self._chroma_store is None:
            return False
        try:
            return self._chroma_store.count() > 0
        except Exception:
            return False

    def _keyword_search(self, normalized_query: str, safe_top_k: int) -> list[dict[str, Any]]:
        query_tokens = _tokenize(normalized_query)
        candidates: list[dict[str, Any]] = []
        sections = (
            "materialChecklist",
            "applicationFieldRules",
            "reviewBasis",
            "promptSnippets",
            "manualReviewRules",
        )

        for section in sections:
            section_items = self._pack.get(section, [])
            if not isinstance(section_items, list):
                continue

            for raw_item in section_items:
                if not isinstance(raw_item, dict):
                    continue

                searchable_text = _build_search_text(raw_item, self._basis_lookup)
                score = _score_match(query_tokens, searchable_text)

                if normalized_query and score == 0:
                    continue

                item_id = str(raw_item.get("id") or "").strip()
                title = (
                    str(raw_item.get("displayName") or "").strip()
                    or str(raw_item.get("sourceTitle") or "").strip()
                    or str(raw_item.get("kind") or "").strip()
                    or item_id
                )

                source_refs = _as_str_list(raw_item.get("sourceRefs", []))
                source_ids = _source_ids_for_item(raw_item, self._basis_lookup)
                basis_refs = _as_str_list(raw_item.get("basisRefs", []))
                excerpt = _build_excerpt(raw_item, self._basis_lookup)

                candidates.append(
                    {
                        "section": section,
                        "id": item_id,
                        "title": title,
                        "materialType": str(raw_item.get("materialType") or "").strip() or None,
                        "fieldPath": str(raw_item.get("fieldPath") or "").strip() or None,
                        "excerpt": excerpt,
                        "score": score,
                        "sourceIds": source_ids,
                        "sourceRefs": source_refs,
                        "basisRefs": basis_refs,
                    }
                )

        candidates.sort(
            key=lambda item: (
                -int(item.get("score") or 0),
                str(item.get("section") or ""),
                str(item.get("id") or ""),
            )
        )

        results = []
        for rank, item in enumerate(candidates[:safe_top_k], start=1):
            result = dict(item)
            result["rank"] = rank
            results.append(result)
        return results

    def _vector_search(self, normalized_query: str, safe_top_k: int) -> list[dict[str, Any]]:
        try:
            query_embeddings = self._embedding_client.embed([normalized_query or " "])
            query_emb = query_embeddings[0]
        except Exception as e:
            logger.warning("Failed to embed query, falling back: %s", e)
            raise

        candidates: list[dict[str, Any]] = []

        if self._chroma_store is not None:
            try:
                chroma_hits = self._chroma_store.query(query_emb, top_k=safe_top_k)
                for hit in chroma_hits:
                    metadata = hit.get("metadata", {})
                    distance = float(hit.get("distance", 0.0))
                    similarity = 1.0 - distance
                    doc_text = str(hit.get("document", "")).strip()
                    excerpt = doc_text[:200] + "..." if len(doc_text) > 200 else doc_text
                    chunk_id = str(hit.get("id", ""))
                    source_file = str(metadata.get("source_file", ""))
                    source_title = str(metadata.get("source_title") or source_file)

                    candidates.append(
                        {
                            "section": "document_chunk",
                            "id": chunk_id,
                            "title": source_title,
                            "materialType": None,
                            "fieldPath": None,
                            "excerpt": excerpt,
                            "score": round(similarity, 4),
                            "sourceIds": [source_file] if source_file else [],
                            "sourceRefs": [],
                            "basisRefs": [],
                        }
                    )
            except Exception as e:
                logger.warning("ChromaDB query failed, continuing with JSON items only: %s", e)

        for emb, raw_item, section in self._json_item_embeddings:
            similarity = _cosine_similarity(query_emb, emb)
            if normalized_query and similarity < _MIN_VECTOR_SIMILARITY:
                continue

            item_id = str(raw_item.get("id") or "").strip()
            title = (
                str(raw_item.get("displayName") or "").strip()
                or str(raw_item.get("sourceTitle") or "").strip()
                or str(raw_item.get("kind") or "").strip()
                or item_id
            )
            source_ids = _source_ids_for_item(raw_item, self._basis_lookup)
            source_refs = _as_str_list(raw_item.get("sourceRefs", []))
            basis_refs = _as_str_list(raw_item.get("basisRefs", []))
            excerpt = _build_excerpt(raw_item, self._basis_lookup)

            candidates.append(
                {
                    "section": section,
                    "id": item_id,
                    "title": title,
                    "materialType": str(raw_item.get("materialType") or "").strip() or None,
                    "fieldPath": str(raw_item.get("fieldPath") or "").strip() or None,
                    "excerpt": excerpt,
                    "score": round(similarity, 4),
                    "sourceIds": source_ids,
                    "sourceRefs": source_refs,
                    "basisRefs": basis_refs,
                }
            )

        candidates.sort(
            key=lambda item: (
                -float(item.get("score") or 0),
                str(item.get("section") or ""),
                str(item.get("id") or ""),
            )
        )

        results = []
        for rank, item in enumerate(candidates[:safe_top_k], start=1):
            result = dict(item)
            result["rank"] = rank
            results.append(result)
        return results

    def knowledge_search(self, query: str, top_k: int | str = 5) -> dict[str, Any]:
        normalized_query = query.strip()
        requested_top_k = top_k
        try:
            top_k_int = int(top_k)
        except (TypeError, ValueError):
            top_k_int = 5
        safe_top_k = max(1, min(50, top_k_int))

        use_vector = self._chroma_populated() and self._embedding_client is not None

        if use_vector:
            try:
                results = self._vector_search(normalized_query, safe_top_k)
            except Exception as e:
                logger.warning("Vector search failed, falling back to keyword: %s", e)
                results = self._keyword_search(normalized_query, safe_top_k)
        else:
            results = self._keyword_search(normalized_query, safe_top_k)

        return {
            "query": normalized_query,
            "requestedTopK": requested_top_k,
            "topK": safe_top_k,
            "total": len(results),
            "results": results,
            "knowledgePackVersion": self._version,
        }

    def check_completeness(self, materials: Any) -> dict[str, Any]:
        submitted = self._normalize_submitted(materials)
        required = [item.material_type for item in self._checklist if item.required]

        submitted_set = set(submitted)
        missing_items = [item for item in self._checklist if item.required and item.material_type not in submitted_set]
        missing = [item.material_type for item in missing_items]

        findings: list[dict[str, Any]] = []
        for item in missing_items:
            findings.append(
                {
                    "code": item.missing_finding_code,
                    "severity": item.missing_finding_severity,
                    "materialType": item.material_type,
                    "materialId": item.item_id,
                    "materialDisplayName": item.display_name,
                    "message": item.missing_finding_message_for_reviewer,
                    "applicantMessage": item.missing_finding_message_for_applicant,
                    "basisRefs": item.basis_refs,
                    "sourceRefs": item.source_refs,
                }
            )

        return {
            "submitted": submitted,
            "required": required,
            "missing": missing,
            "complete": len(missing) == 0,
            "findings": findings,
            "knowledgePackVersion": self._version,
        }

    def _normalize_submitted(self, materials: Any) -> list[str]:
        material_items: list[Any]

        if materials is None:
            material_items = []
        elif isinstance(materials, Mapping):
            if "materials" in materials:
                inner = materials["materials"]
                if isinstance(inner, list):
                    material_items = list(inner)
                elif isinstance(inner, Mapping) and all(isinstance(v, bool) for v in inner.values()):
                    material_items = [k for k, v in inner.items() if v]
                else:
                    material_items = [inner] if not isinstance(inner, Mapping) else []
            elif all(isinstance(v, bool) for v in materials.values()):
                material_items = [k for k, v in materials.items() if v]
            else:
                material_items = list(materials.values())
        elif isinstance(materials, Sequence) and not isinstance(materials, (str, bytes, bytearray)):
            material_items = list(materials)
        else:
            material_items = [materials]

        submitted: list[str] = []
        seen: set[str] = set()
        for item in material_items:
            material_type = _extract_material_type(item)
            if not material_type:
                continue
            if material_type in seen:
                continue
            seen.add(material_type)
            submitted.append(material_type)

        return submitted
