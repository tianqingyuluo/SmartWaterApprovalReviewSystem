# -*- coding: utf-8 -*-
"""test_07_reviewer_result.py
接口: GET /api/task/{taskId}/result/reviewer
测试: 查询审批人员完整结果（含风险提示、审核意见草稿、模型元数据）
前置: 需要先运行 test_05_write_result.py 写入结果
"""
import requests
from test_config import BASE_URL, get_last_result, build_session_url

TASK_ID_SAMPLE = get_last_result().get("taskId", "SW0000000000000000")

if __name__ == "__main__":
    url_template = f"{BASE_URL}/task/{{task_id}}/result/reviewer"
    url = build_session_url(url_template, TASK_ID_SAMPLE)
    print(f"\n{'='*60}")
    print(f"[TEST] 查询审批人员结果: {TASK_ID_SAMPLE}")
    resp = requests.get(url)
    print(f"Status: {resp.status_code}")
    data = resp.json()
    if data.get("code") == 200:
        d = data["data"]
        print(f"  status: {d.get('status')}")
        print(f"  summary: {d.get('summary')}")
        for issue in d.get("issues", []):
            print(f"  issue=[{issue.get('severity')}] {issue.get('code')}: {issue.get('message')}")
            print(f"        material={issue.get('materialType')}, visible={issue.get('applicantVisible')}")
        for hint in d.get("riskHints", []):
            print(f"  risk=[{hint.get('riskLevel')}] {hint.get('description')}")
        print(f"  draftOpinion: {d.get('draftOpinion')}")
        print(f"  modelMetadata: {d.get('modelMetadata')}")
    else:
        print(f"  ERR: {data}")
