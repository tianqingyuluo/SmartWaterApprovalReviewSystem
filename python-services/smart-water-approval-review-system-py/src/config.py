import os
import shlex
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _env_list(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name, "").strip()
    if not value:
        return list(default)
    return shlex.split(value)


def _env_dict(name: str, default: dict[str, str] | None = None) -> dict[str, str] | None:
    value = os.getenv(name, "").strip()
    if not value:
        return default

    result: dict[str, str] = {}
    for item in value.split(","):
        key, separator, raw = item.partition("=")
        if not separator:
            continue
        key = key.strip()
        if not key:
            continue
        result[key] = raw.strip()
    return result or default


class Config:
    PROJECT_ROOT: str = os.getenv("PROJECT_ROOT", str(_PROJECT_ROOT))
    BACKEND_API_BASE: str = os.getenv("BACKEND_API_BASE", "http://localhost:8080/api")
    WORKER_TOKEN: str = os.getenv("WORKER_TOKEN", "")
    INTERNAL_API_TOKEN: str = os.getenv("INTERNAL_API_TOKEN", "")

    OCR_PROVIDER: str = os.getenv("OCR_PROVIDER", "glm")
    OCR_GLM_API_KEY: str = os.getenv("OCR_GLM_API_KEY", "")
    OCR_GLM_BASE_URL: str = os.getenv("OCR_GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")

    REVIEW_LLM_PROVIDER: str = os.getenv("REVIEW_LLM_PROVIDER", "dashscope")
    REVIEW_LLM_MODEL: str = os.getenv("REVIEW_LLM_MODEL", "qwen-max")
    REVIEW_LLM_BASE_URL: str = os.getenv("REVIEW_LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    REVIEW_LLM_API_KEY: str = os.getenv("REVIEW_LLM_API_KEY", "")

    WORKER_POLL_INTERVAL: int = int(os.getenv("WORKER_POLL_INTERVAL", "5"))
    WORKER_MAX_RETRIES: int = int(os.getenv("WORKER_MAX_RETRIES", "3"))

    KNOWLEDGE_PACK_DIR: str = os.getenv("KNOWLEDGE_PACK_DIR", "./knowledge_pack")

    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "dashscope")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-v3")
    EMBEDDING_BASE_URL: str = os.getenv("EMBEDDING_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    EMBEDDING_API_KEY: str = os.getenv("EMBEDDING_API_KEY", "")

    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
    CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "knowledge_base")

    KNOWLEDGE_SOURCE_DIR: str = os.getenv("KNOWLEDGE_SOURCE_DIR", "")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    MCP_SERVER_COMMAND: str = os.getenv("MCP_SERVER_COMMAND", sys.executable)
    MCP_SERVER_ARGS: list[str] = _env_list("MCP_SERVER_ARGS", ["-m", "src.mcp_server.app", "--transport", "stdio"])
    MCP_SERVER_CWD: str = os.getenv("MCP_SERVER_CWD", PROJECT_ROOT)
    MCP_SERVER_ENV: dict[str, str] | None = _env_dict(
        "MCP_SERVER_ENV",
        {
            "KNOWLEDGE_PACK_DIR": KNOWLEDGE_PACK_DIR,
            "LOG_LEVEL": LOG_LEVEL,
        },
    )

    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "512"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "64"))


config = Config()
