#!/usr/bin/env python3
# test_04_update_status.py - 测试更新任务状态接口（Worker 用）
# 接口: PUT /api/task/{taskId}/status
# 测试内容:
#   1. 将任务状态更新为 QUEUED
#   2. 将任务状态更新为 PROCESSING
#   3. 更新不存在的任务
# 需要 taskId，从 test_01_submit.py 运行后的输出获取

import requests
from test_config import BASE_URL, get_last_result, WORKER_HEADERS

URL_TEMPLATE = f"{BASE_URL}/task/{{task_id}}/status"


def test_update(task_id, status):
    print(f"[测试] 更新状态为 {status}")
    resp = requests.put(
        URL_TEMPLATE.format(task_id=task_id),
        json={"status": status},
        headers=WORKER_HEADERS,
    )
    print(f"  状态码: {resp.status_code}")
    print(f"  响应: {resp.json()}")
    if resp.json().get("code") == 200:
        print(f"  [OK] 更新成功")
    print()


def test_update_not_found():
    print("=" * 50)
    print("[测试] 更新不存在的任务")
    resp = requests.put(
        URL_TEMPLATE.format(task_id="SWXXXXNOTFOUND"),
        json={"status": "PROCESSING"},
        headers=WORKER_HEADERS,
    )
    print(f"  状态码: {resp.status_code}")
    print(f"  响应: {resp.json()}")
    if resp.json().get("code") == 404:
        print("  [OK] 正确返回 404")
    print()


if __name__ == "__main__":
    last = get_last_result()
    task_id = last.get("taskId", "SWMANUALINPUTHERE")

    print("=" * 50)
    print(f"[测试] 更新任务状态: {task_id}")
    test_update(task_id, "QUEUED")
    test_update(task_id, "PROCESSING")
    test_update_not_found()
