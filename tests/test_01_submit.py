#!/usr/bin/env python3
# test_01_submit.py - 测试材料提交接口
# 接口: POST /api/task/submit
# 测试内容:
#   1. 提交全部 3 个材料
#   2. 提交部分材料（2个）
#   3. 空提交（0个材料）
#   4. 提交不支持的文件格式
# 测试文件放在: test_data/ 目录

import os
import requests
from test_config import BASE_URL, TEST_DATA_DIR, TEST_FILES, set_last_result

URL = f"{BASE_URL}/task/submit"


def _get_file(filename):
    """获取测试文件，不存在则返回 None"""
    path = os.path.join(TEST_DATA_DIR, filename)
    if os.path.isfile(path):
        return open(path, "rb")
    return None


def test_submit_all():
    """测试 1: 提交全部 3 个材料"""
    print("=" * 50)
    print("[测试] 提交全部 3 个材料")
    files = {}
    for key, fname in TEST_FILES.items():
        f = _get_file(fname)
        if f:
            files[key] = (fname, f)

    resp = requests.post(URL, files=files if files else None)
    print(f"状态码: {resp.status_code}")
    data = resp.json()
    print(f"响应: {data}")
    if data.get("code") == 200 and data.get("data"):
        set_last_result(data["data"])
        print("[OK] taskId=" + data['data']['taskId'])
    else:
        print("[WARN] submit non-OK (may be normal if test files missing)")
    print()


def test_submit_partial():
    """测试 2: 只提交 1 个材料"""
    print("=" * 50)
    print("[测试] 只提交申请书（1 个材料）")
    f = _get_file(TEST_FILES["applicationForm"])
    if f:
        files = {"applicationForm": (TEST_FILES["applicationForm"], f)}
        resp = requests.post(URL, files=files)
        print(f"状态码: {resp.status_code}")
        data = resp.json()
        print(f"响应: {data}")
        upload_count = sum(1 for m in data.get("data", {}).get("materials", []) if m.get("uploaded"))
        print("[OK] actually uploaded " + str(upload_count) + " material(s)")
    else:
        print("[WARN] skip: test_application.pdf not found")
    print()


def test_submit_empty():
    """测试 3: 空提交"""
    print("=" * 50)
    print("[测试] 空提交（0 个文件）")
    resp = requests.post(URL)
    print(f"状态码: {resp.status_code}")
    data = resp.json()
    print(f"响应: {data}")
    if data.get("code") == 200:
        print("[OK] taskId=" + data['data']['taskId'])
    print()


def test_submit_invalid_format():
    """测试 4: 提交不支持的文件格式"""
    print("=" * 50)
    print("[测试] 提交 .docx 格式（应被拒绝）")
    # 创建一个假的 docx 内容
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
        tf.write(b"fake docx content")
        tf.flush()
        f = open(tf.name, "rb")
        files = {"applicationForm": ("test.docx", f)}
        resp = requests.post(URL, files=files)
        print(f"状态码: {resp.status_code}")
        print(f"响应: {resp.json()}")
        f.close()
    os.unlink(tf.name)
    print()


if __name__ == "__main__":
    test_submit_all()
    test_submit_partial()
    test_submit_empty()
    test_submit_invalid_format()
