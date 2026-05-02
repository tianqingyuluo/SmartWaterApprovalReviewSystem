#!/usr/bin/env python3
# test_03_get_status.py - 测试查询任务状态接口
# 接口: GET /api/task/{taskId}/status
# 测试内容:
#   1. 查询存在的任务
#   2. 查询不存在的任务（应返回 404）
# 需要 taskId，从 test_01_submit.py 运行后的输出或手动指定

import requests
from test_config import BASE_URL, get_last_result, build_session_url

URL_TEMPLATE = f"{BASE_URL}/task/{{task_id}}/status"


def test_status(task_id):
    """测试 1: 查询存在的任务"""
    print("=" * 50)
    print(f"[测试] 查询任务状态: {task_id}")
    url = build_session_url(URL_TEMPLATE, task_id)
    resp = requests.get(url)
    print(f"状态码: {resp.status_code}")
    data = resp.json()
    if data.get("code") == 200:
        d = data["data"]
        print(f"  status: {d.get('status')}")
        print(f"  submittedAt: {d.get('submittedAt')}")
        for m in d.get("materials", []):
            print(f"  {m['materialType']}: uploaded={m['uploaded']}, file={m.get('originalFileName')}")
        print("[OK] 查询成功")
    else:
        print(f"[FAIL] {data}")
    print()


def test_status_not_found():
    """测试 2: 查询不存在的任务"""
    print("=" * 50)
    print("[测试] 查询不存在的任务")
    url = build_session_url(URL_TEMPLATE, "SWXXXXNOTFOUND")
    resp = requests.get(url)
    print(f"状态码: {resp.status_code}")
    data = resp.json()
    print(f"响应: {data}")
    if data.get("code") == 404:
        print("[OK] 正确返回 404")
    else:
        print("[WARN]️ 预期 404")
    print()


if __name__ == "__main__":
    # 从上一个测试获取 taskId，或手动填入
    last = get_last_result()
    task_id = last.get("taskId", "SWMANUALINPUTHERE")

    test_status(task_id)
    test_status_not_found()
