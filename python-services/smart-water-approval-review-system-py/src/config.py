import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    BACKEND_API_BASE: str = os.getenv("BACKEND_API_BASE", "http://localhost:8080/api")
    WORKER_TOKEN: str = os.getenv("WORKER_TOKEN", "")

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

    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "512"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "64"))

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


config = Config()
