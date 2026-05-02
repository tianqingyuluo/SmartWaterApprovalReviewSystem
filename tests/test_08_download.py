# -*- coding: utf-8 -*-
"""
测试: GET /api/material/download  —  Material 文件下载接口

前置: 需要先运行 test_01_submit.py 提交带文件的任务
      然后从 test_02_pending.py 的输出中获取 storageKey
配置: 修改下方 STORAGE_KEY
"""
import requests
from test_config import BASE_URL, get_last_result, WORKER_HEADERS

TASK_ID_SAMPLE = get_last_result().get("taskId", "SW0000000000000000")
STORAGE_KEY = "SW0000000000000000/APPLICATION_FORM/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.pdf"

if __name__ == "__main__":
    url = f"{BASE_URL}/material/download"
    print(f"\n{'='*60}")
    print(f"[TEST] 下载材料: {STORAGE_KEY}")
    resp = requests.get(url, params={"key": STORAGE_KEY}, headers=WORKER_HEADERS)
    print(f"Status: {resp.status_code}")
    print(f"Content-Type: {resp.headers.get('Content-Type')}")
    print(f"Content-Length: {len(resp.content)} bytes")
    if resp.status_code == 200:
        print(">>> 文件下载成功")
    else:
        print(f"Body: {resp.text}")
