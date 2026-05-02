#!/usr/bin/env python3
# test_02_pending.py - 测试拉取待处理任务接口
# 接口: GET /api/task/pending
# 测试内容:
#   1. 查询所有待处理任务
#   2. 验证返回的任务列表结构
# 依赖: 需要先运行 test_01_submit.py 创建一些任务

import requests
from test_config import BASE_URL, WORKER_HEADERS

URL = f"{BASE_URL}/task/pending"


def test_pending():
    print("=" * 50)
    print("[测试] 拉取待处理任务列表")
    resp = requests.get(URL, headers=WORKER_HEADERS)
    print(f"状态码: {resp.status_code}")
    data = resp.json()
    print(f"响应: {data}")

    if data.get("code") == 200:
        tasks = data.get("data", [])
        print(f"[OK] 待处理任务数: {len(tasks)}")
        for i, t in enumerate(tasks):
            print(f"  [{i+1}] taskId={t.get('taskId')}, status={t.get('status')}")
            for m in t.get("materials", []):
                print(f"      {m['materialType']}: uploaded={m['uploaded']}")
    else:
        print("[FAIL] 请求失败")
    print()


if __name__ == "__main__":
    test_pending()
