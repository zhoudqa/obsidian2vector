import os

VAULT_PATH = os.path.expanduser("~/ai-proj/PaperBell")

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

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "obsidian_notes")

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))