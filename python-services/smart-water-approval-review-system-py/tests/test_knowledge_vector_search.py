"""Tests for vector-search path in SmartWaterKnowledgeTools."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from src.services.knowledge_tools import SmartWaterKnowledgeTools, _cosine_similarity

_SAMPLE_KNOWLEDGE_PACK: dict[str, Any] = {
    "version": "test-vector-1.0",
    "materialChecklist": [
        {
            "id": "MAT_APP",
            "materialType": "APPLICATION_FORM",
            "displayName": "取水许可申请书",
            "requiredForCompleteReview": True,
            "sourceRefs": ["SRC_FORM"],
            "basisRefs": ["BASIS_CHECKLIST"],
            "missingFinding": {
                "code": "MISSING_MATERIAL",
                "severity": "BLOCKER",
                "messageForApplicant": "缺少申请书",
                "messageForReviewer": "缺少申请书，无法审核",
            },
        },
    ],
    "applicationFieldRules": [
        {
            "id": "FIELD_PROJECT_NAME",
            "fieldPath": "projectProfile.projectName",
            "displayName": "项目名称",
            "materialType": "APPLICATION_FORM",
            "required": True,
            "ruleType": "COMPLETENESS",
            "instruction": "填写建设项目名称。",
            "sourceRefs": ["SRC_FIELD_INSTR"],
            "basisRefs": ["BASIS_PROJECT_NAME"],
        },
    ],
    "reviewBasis": [
        {
            "id": "BASIS_CHECKLIST",
            "category": "MATERIAL_CHECKLIST",
            "sourceId": "SRC_PROCESS",
            "sourceTitle": "材料清单",
            "summary": "申请材料应包括申请书、营业执照和身份证。",
        },
        {
            "id": "BASIS_PROJECT_NAME",
            "category": "FIELD_RULE",
            "sourceId": "SRC_FIELD_INSTR",
            "sourceTitle": "项目名称填表说明",
            "summary": "新建改建扩建项目应填写建设项目名称。",
        },
    ],
    "promptSnippets": [
        {
            "id": "PROMPT_SYSTEM_ROLE",
            "kind": "system",
            "text": "你是取水许可审核助手。",
        },
    ],
    "manualReviewRules": [
        {
            "id": "MR_NO_PERMIT",
            "findingCode": "PERMIT_REQUIREMENT_REVIEW_REQUIRED",
            "trigger": "可能无需办理取水许可。",
            "basisRefs": ["BASIS_CHECKLIST"],
            "reason": "需人工判断。",
        },
    ],
}


class TestCosineSimilarity:
    def test_identical_vectors(self):
        v = [1.0, 2.0, 3.0]
        assert _cosine_similarity(v, v) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        assert _cosine_similarity([1.0, 0.0, 0.0], [0.0, 1.0, 0.0]) == pytest.approx(0.0)

    def test_zero_vector(self):
        assert _cosine_similarity([0.0, 0.0], [1.0, 2.0]) == pytest.approx(0.0)


class TestVectorSearchKeywordFallback:
    def test_falls_back_when_chroma_store_is_none(self):
        tools = SmartWaterKnowledgeTools(knowledge_pack=_SAMPLE_KNOWLEDGE_PACK)
        result = tools.knowledge_search("取水许可", top_k=3)
        assert result["results"]
        # Keyword search uses integer scores
        for item in result["results"]:
            assert isinstance(item["score"], int)

    def test_falls_back_when_chroma_empty(self):
        mock_store = MagicMock()
        mock_store.count.return_value = 0
        tools = SmartWaterKnowledgeTools(
            knowledge_pack=_SAMPLE_KNOWLEDGE_PACK,
            chroma_store=mock_store,
        )
        result = tools.knowledge_search("取水许可")
        assert result["results"]

    def test_falls_back_when_embedding_client_is_none(self):
        mock_store = MagicMock()
        mock_store.count.return_value = 5
        tools = SmartWaterKnowledgeTools(
            knowledge_pack=_SAMPLE_KNOWLEDGE_PACK,
            chroma_store=mock_store,
            embedding_client=None,
        )
        result = tools.knowledge_search("取水许可")
        assert result["results"]


class TestVectorSearchHappyPath:
    def test_uses_vector_search_when_chroma_populated(self):
        mock_store = MagicMock()
        mock_store.count.return_value = 10
        mock_store.query.return_value = [
            {
                "id": "取水许可办理需资料及流程.docx_3_0",
                "document": "取水许可申请书是办理取水许可的必备材料，需填写单位名称、"
                "统一社会信用代码、法定代表人、取水地点、取水量等信息。",
                "metadata": {
                    "source_file": "取水许可办理需资料及流程.docx",
                    "source_title": "取水许可办理需资料及流程",
                    "doc_type": "docx",
                },
                "distance": 0.15,
            },
        ]

        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = [[0.1] * 256]  # query embedding
        # JSON item embeddings — called on init
        # We need to provide N embeddings for N JSON items
        # There are 5 items in _SAMPLE_KNOWLEDGE_PACK (1+1+2+1+1=6, actually let me count):
        # materialChecklist: 1, applicationFieldRules: 1, reviewBasis: 2,
        # promptSnippets: 1, manualReviewRules: 1 = 6 items
        # But _precompute_json_embeddings uses _build_search_text for each
        # We need to return 6 + 1 (for query) embeddings
        # Actually the query embed is called separately in _vector_search
        # The precompute calls embed() once with all 6 texts concatenated
        mock_embedder.embed.side_effect = lambda texts: [[0.1] * 256 for _ in texts]

        tools = SmartWaterKnowledgeTools(
            knowledge_pack=_SAMPLE_KNOWLEDGE_PACK,
            chroma_store=mock_store,
            embedding_client=mock_embedder,
        )

        result = tools.knowledge_search("取水许可申请书", top_k=10)
        assert result["results"]

        # Should have called ChromaDB query
        mock_store.query.assert_called_once()

        # Check that ChromaDB document chunk is in results
        doc_results = [r for r in result["results"] if r["section"] == "document_chunk"]
        assert len(doc_results) > 0
        assert doc_results[0]["score"] > 0

    def test_vector_search_result_has_expected_fields(self):
        mock_store = MagicMock()
        mock_store.count.return_value = 10
        mock_store.query.return_value = [
            {
                "id": "test.docx_1_0",
                "document": "测试文档内容片段。",
                "metadata": {"source_file": "test.docx", "source_title": "测试文档"},
                "distance": 0.2,
            },
        ]

        mock_embedder = MagicMock()
        mock_embedder.embed.side_effect = lambda texts: [[0.1] * 256 for _ in texts]

        tools = SmartWaterKnowledgeTools(
            knowledge_pack=_SAMPLE_KNOWLEDGE_PACK,
            chroma_store=mock_store,
            embedding_client=mock_embedder,
        )

        result = tools.knowledge_search("测试", top_k=3)

        required_keys = {"query", "requestedTopK", "topK", "total", "results", "knowledgePackVersion"}
        assert required_keys <= set(result.keys())

        for item in result["results"]:
            assert "section" in item
            assert "id" in item
            assert "title" in item
            assert "excerpt" in item
            assert "score" in item
            assert "rank" in item
            assert "sourceIds" in item
            assert "sourceRefs" in item
            assert "basisRefs" in item

    def test_document_chunk_score_is_float(self):
        mock_store = MagicMock()
        mock_store.count.return_value = 10
        mock_store.query.return_value = [
            {
                "id": "test.docx_1_0",
                "document": "测试内容",
                "metadata": {"source_file": "test.docx", "source_title": "测试"},
                "distance": 0.2,
            },
        ]

        mock_embedder = MagicMock()
        mock_embedder.embed.side_effect = lambda texts: [[0.1] * 256 for _ in texts]

        tools = SmartWaterKnowledgeTools(
            knowledge_pack=_SAMPLE_KNOWLEDGE_PACK,
            chroma_store=mock_store,
            embedding_client=mock_embedder,
        )

        result = tools.knowledge_search("测试", top_k=3)

        for item in result["results"]:
            assert isinstance(item["score"], float), f"Expected float score, got {type(item['score'])}"

    def test_json_items_preserve_basis_refs_in_vector_search(self):
        mock_store = MagicMock()
        mock_store.count.return_value = 10
        mock_store.query.return_value = []

        mock_embedder = MagicMock()
        mock_embedder.embed.side_effect = lambda texts: [[0.1] * 256 for _ in texts]

        tools = SmartWaterKnowledgeTools(
            knowledge_pack=_SAMPLE_KNOWLEDGE_PACK,
            chroma_store=mock_store,
            embedding_client=mock_embedder,
        )

        result = tools.knowledge_search("项目名称", top_k=10)
        # BASIS_PROJECT_NAME should appear in results
        basis_ids = {r["id"] for r in result["results"]}
        assert "BASIS_PROJECT_NAME" in basis_ids

    def test_top_k_clamping_in_vector_search(self):
        mock_store = MagicMock()
        mock_store.count.return_value = 10
        mock_store.query.return_value = []

        mock_embedder = MagicMock()
        mock_embedder.embed.side_effect = lambda texts: [[0.1] * 256 for _ in texts]

        tools = SmartWaterKnowledgeTools(
            knowledge_pack=_SAMPLE_KNOWLEDGE_PACK,
            chroma_store=mock_store,
            embedding_client=mock_embedder,
        )

        result = tools.knowledge_search("测试", top_k=1000)
        assert result["total"] <= 50
        assert result["topK"] == 50

    def test_check_completeness_unchanged_with_vector_search(self):
        mock_store = MagicMock()
        mock_store.count.return_value = 10
        mock_store.query.return_value = []

        mock_embedder = MagicMock()
        mock_embedder.embed.side_effect = lambda texts: [[0.1] * 256 for _ in texts]

        tools = SmartWaterKnowledgeTools(
            knowledge_pack=_SAMPLE_KNOWLEDGE_PACK,
            chroma_store=mock_store,
            embedding_client=mock_embedder,
        )

        # Single string input
        result = tools.check_completeness("APPLICATION_FORM")
        assert result["submitted"] == ["APPLICATION_FORM"]
        assert result["missing"] == []
        assert result["complete"] is True

        # List input — sample pack only requires APPLICATION_FORM
        result = tools.check_completeness(["APPLICATION_FORM", "BUSINESS_LICENSE"])
        assert result["complete"] is True  # only APPLICATION_FORM is required in sample pack
        assert result["missing"] == []


class TestVectorSearchFallbackOnError:
    def test_falls_back_when_embedding_fails(self):
        mock_store = MagicMock()
        mock_store.count.return_value = 10

        mock_embedder = MagicMock()
        # Pre-compute succeeds, but query embed fails
        mock_embedder.embed.side_effect = RuntimeError("API down")

        tools = SmartWaterKnowledgeTools(
            knowledge_pack=_SAMPLE_KNOWLEDGE_PACK,
            chroma_store=mock_store,
            embedding_client=mock_embedder,
        )

        result = tools.knowledge_search("取水许可", top_k=3)
        assert result["results"]
        # Should have fallen back to keyword search
        for item in result["results"]:
            assert isinstance(item["score"], int)

    def test_falls_back_when_chroma_query_fails(self):
        mock_store = MagicMock()
        mock_store.count.return_value = 10
        mock_store.query.side_effect = RuntimeError("ChromaDB down")

        mock_embedder = MagicMock()
        # First call: pre-compute in init (all 6 items in one batch)
        # Second call: query embed in _vector_search
        # Third+ call: should not happen if fallback works

        precompute_called = 0

        def side_effect(texts):
            nonlocal precompute_called
            precompute_called += 1
            return [[0.1] * 256 for _ in texts]

        mock_embedder.embed.side_effect = side_effect

        tools = SmartWaterKnowledgeTools(
            knowledge_pack=_SAMPLE_KNOWLEDGE_PACK,
            chroma_store=mock_store,
            embedding_client=mock_embedder,
        )

        # _vector_search should handle ChromaDB error gracefully and still return
        # JSON item results since query embedding succeeded
        result = tools.knowledge_search("取水许可", top_k=5)
        # Vector search should proceed with JSON items only (ChromaDB failed)
        # Results should have float scores from vector matching JSON items
        assert result["results"]
        for item in result["results"]:
            assert isinstance(item["score"], float)
