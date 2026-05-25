import os

VAULT_PATH = os.getenv("VAULT_PATH")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")

MODEL_DIM_MAP = {
    "BAAI/bge-small-zh-v1.5": 512,
    "BAAI/bge-base-zh-v1.5": 768,
    "BAAI/bge-large-zh-v1.5": 1024,
    "Qwen/Qwen3-Embedding-0.6B": 1024,
    "Qwen/Qwen3-Embedding-1.8B": 1024,
}

EMBEDDING_DIM = MODEL_DIM_MAP.get(EMBEDDING_MODEL, 1024)

DB_TYPE = os.getenv("DB_TYPE", "milvus").lower()

MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
MILVUS_COLLECTION = os.getenv("MILVUS_COLLECTION", "obsidian_notes")

CHROMA_PATH = os.getenv("CHROMA_PATH", os.path.expanduser("~/.chroma"))
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "obsidian_notes")

# 模型加载模式: "online" (在线下载) 或 "offline" (仅从本地加载)
MODEL_LOAD_MODE = os.getenv("MODEL_LOAD_MODE", "online").lower()

# 离线模式下的本地模型路径 (为空则从 HuggingFace 缓存查找)
MODEL_LOCAL_PATH = os.getenv("MODEL_LOCAL_PATH", "")

# HuggingFace 镜像地址 (在线模式下生效, 如 https://hf-mirror.com)
HF_ENDPOINT = os.getenv("HF_ENDPOINT", "")

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))