#!/usr/bin/env python3
# test_05_write_result.py - 测试回写审核结果接口（Worker 用）
# 接口: PUT /api/task/{taskId}/result
# 测试内容:
#   1. 回写完整的审核结果（含申请人视图和审批人员视图）
#   2. 回写部分成功的结果
# 需要 taskId，从 test_01_submit.py 运行后的输出获取

import requests
import json
from test_config import BASE_URL, get_last_result, WORKER_HEADERS

URL_TEMPLATE = f"{BASE_URL}/task/{{task_id}}/result"

SAMPLE_RESULT = {
    "status": "COMPLETED",
    "resultSummary": "申请材料审核完成，发现1个问题，1个风险提示",
    "applicantResult": {
        "summary": "申请材料基本完整，建议补充身份证扫描件",
        "issues": [
            {
                "code": "MISSING_MATERIAL",
                "severity": "WARNING",
                "message": "缺少身份证材料"
            }
        ],
        "materialCompleteness": {
            "received": ["APPLICATION_FORM", "BUSINESS_LICENSE"],
            "missing": ["ID_CARD"],
            "unrecognized": []
        },
        "manualReviewNotice": "AI审核结果为辅助建议"
    },
    "reviewerResult": {
        "summary": "申请材料审核完成，发现1个问题，1个风险提示",
        "issues": [
            {
                "code": "MISSING_MATERIAL",
                "severity": "WARNING",
                "message": "缺少身份证材料",
                "materialType": "ID_CARD",
                "fieldKey": None,
                "basisRefs": ["REG-2024-001"],
                "applicantVisible": True
            }
        ],
        "riskHints": [
            {
                "riskLevel": "MEDIUM",
                "description": "申请材料不完整，可能影响审批进度",
                "basisRefs": ["REG-2024-001"],
                "requiresManualReview": True
            }
        ],
        "draftOpinion": "建议补充身份证扫描件后重新提交",
        "materialCompleteness": {
            "received": ["APPLICATION_FORM", "BUSINESS_LICENSE"],
            "missing": ["ID_CARD"],
            "unrecognized": []
        },
        "basisRefs": ["REG-2024-001"],
        "manualReviewNotice": "AI审核结果为辅助建议，不构成最终审批意见。",
        "modelMetadata": {
            "provider": "dashscope",
            "model": "qwen-max",
            "requestId": "req-test-001",
            "finishReason": "stop",
            "tokenUsage": {
                "promptTokens": 500,
                "completionTokens": 200,
                "totalTokens": 700
            }
        }
    }
}


def test_write_completed(task_id):
    """测试 1: 回写完整审核结果"""
    print("=" * 50)
    print(f"[测试] 回写完整审核结果: {task_id}")
    resp = requests.put(
        URL_TEMPLATE.format(task_id=task_id),
        json=SAMPLE_RESULT,
        headers=WORKER_HEADERS,
    )
    print(f"状态码: {resp.status_code}")
    print(f"响应: {resp.json()}")

    if resp.json().get("code") == 200:
        print("[OK] 结果回写成功")
        print(f">>> 现在可以访问 GET {BASE_URL}/task/{task_id}/result/applicant")
        print(f">>> 现在可以访问 GET {BASE_URL}/task/{task_id}/result/reviewer")
    print()


def test_write_partial(task_id):
    """测试 2: 回写部分成功结果"""
    print("=" * 50)
    print(f"[测试] 回写部分成功结果: {task_id}")
    partial = {
        "status": "PARTIAL_SUCCESS",
        "resultSummary": "部分材料处理失败",
        "applicantResult": {
            "summary": "部分材料OCR识别失败",
            "issues": [
                {"code": "OCR_LOW_CONFIDENCE", "severity": "WARNING", "message": "营业执照OCR识别置信度低"}
            ],
            "materialCompleteness": {
                "received": ["APPLICATION_FORM"],
                "missing": ["BUSINESS_LICENSE", "ID_CARD"],
                "unrecognized": []
            }
        },
        "reviewerResult": {
            "summary": "部分材料OCR识别失败",
            "issues": [
                {
                    "code": "OCR_LOW_CONFIDENCE",
                    "severity": "WARNING",
                    "message": "营业执照OCR识别置信度低",
                    "materialType": "BUSINESS_LICENSE",
                    "applicantVisible": True
                }
            ],
            "riskHints": [],
            "draftOpinion": "建议重新上传营业执照",
            "materialCompleteness": {
                "received": ["APPLICATION_FORM"],
                "missing": ["BUSINESS_LICENSE", "ID_CARD"],
                "unrecognized": []
            },
            "basisRefs": [],
            "manualReviewNotice": "AI审核结果为辅助建议"
        }
    }
    resp = requests.put(
        URL_TEMPLATE.format(task_id=task_id),
        json=partial,
        headers=WORKER_HEADERS,
    )
    print(f"状态码: {resp.status_code}")
    print(f"响应: {resp.json()}")
    print()


if __name__ == "__main__":
    last = get_last_result()
    task_id = last.get("taskId", "SWMANUALINPUTHERE")
    test_write_completed(task_id)
