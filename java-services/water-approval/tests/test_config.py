import json
import os

BASE_URL = "http://localhost:8080/api"
TASK_CACHE_FILE = ".task_cache.json"
WORKER_TOKEN = os.getenv("WATER_APPROVAL_WORKER_TOKEN", "")

TEST_DATA_DIR = "test_data"
TEST_FILES = {
    "applicationForm": "test_application.pdf",
    "businessLicense": "test_license.jpg",
    "idCard": "test_idcard.png",
}

WORKER_HEADERS = {"X-Worker-Token": WORKER_TOKEN} if WORKER_TOKEN else {}


def get_last_result():
    if os.path.isfile(TASK_CACHE_FILE):
        with open(TASK_CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def set_last_result(data):
    with open(TASK_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def build_session_url(path, task_id):
    last = get_last_result()
    session_id = last.get("sessionId", "")
    url = path.format(task_id=task_id)
    if session_id:
        url += f"?sessionId={session_id}"
    return url
