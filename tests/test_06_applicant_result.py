#!/usr/bin/env python3
# test_06_applicant_result.py - 测试查询申请人结果接口
# 接口: GET /api/task/{taskId}/result/applicant
# 测试内容:
#   1. 查询已有结果的任务
#   2. 查询尚无结果的任务（应提示处理中）
# 依赖: 需要先运行 test_05_write_result.py 写入结果

import requests
from test_config import BASE_URL, get_last_result, build_session_url

URL_TEMPLATE = f"{BASE_URL}/task/{{task_id}}/result/applicant"


def test_applicant_result(task_id):
    print("=" * 50)
    print(f"[测试] 查询申请人结果: {task_id}")
    url = build_session_url(URL_TEMPLATE, task_id)
    resp = requests.get(url)
    print(f"状态码: {resp.status_code}")
    data = resp.json()
    if data.get("code") == 200:
        d = data["data"]
        print(f"  status: {d.get('status')}")
        print(f"  summary: {d.get('summary')}")
        for issue in d.get("issues", []):
            print(f"  问题: [{issue.get('severity')}] {issue.get('code')}: {issue.get('message')}")
        for m in d.get("missingMaterials", []):
            print(f"  缺失: {m}")
        print("[OK] 查询成功")
    else:
        print(f"[FAIL] {data}")
    print()


if __name__ == "__main__":
    last = get_last_result()
    task_id = last.get("taskId", "SWMANUALINPUTHERE")
    test_applicant_result(task_id)
