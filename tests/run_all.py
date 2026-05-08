#!/usr/bin/env python3
"""
run_all.py - 一键执行所有测试脚本

用法:
    python run_all.py                    # 执行所有测试
    python run_all.py -s                 # 只执行提交+状态查询流程

执行顺序:
    1. test_01_submit.py        提交材料
    2. test_02_pending.py       拉取待处理任务
    3. test_03_get_status.py    查询任务状态
    4. test_04_update_status.py 更新任务状态
    5. test_05_write_result.py  回写审核结果
    6. test_06_applicant_result 查询申请人结果
    7. test_07_reviewer_result  查询审批人员结果
    *. test_08_download.py      下载材料 (需手动指定 storageKey)
"""

import subprocess
import sys

SCRIPTS = [
    ("test_01_submit.py",         "提交材料"),
    ("test_02_pending.py",        "拉取待处理任务"),
    ("test_03_get_status.py",     "查询任务状态"),
    ("test_04_update_status.py",  "更新任务状态"),
    ("test_05_write_result.py",   "回写审核结果"),
    ("test_06_applicant_result.py","查询申请人结果"),
    ("test_07_reviewer_result.py","查询审批人员结果"),
]

def run_script(name, desc):
    print(f"\n{'#'*60}")
    print(f"# 运行: {name} ({desc})")
    print(f"{'#'*60}")
    result = subprocess.run(
        ["python", name],
        capture_output=False,
        text=True
    )
    return result.returncode == 0

if __name__ == "__main__":
    print("=" * 60)
    print("SmartWater API 自动化测试")
    print(f"BASE_URL: http://localhost:8080/api")
    print("=" * 60)

    passed = 0
    failed = 0

    for script, desc in SCRIPTS:
        ok = run_script(script, desc)
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"测试完成: 通过 {passed}/{len(SCRIPTS)}, 失败 {failed}/{len(SCRIPTS)}")
    print(f"提示: test_08_download.py 需要手动指定 storageKey 后单独运行")
    print(f"{'='*60}")
