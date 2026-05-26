import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".obsidian2vector"
CONFIG_FILE = CONFIG_DIR / "settings.json"

_DEFAULTS: dict = {
    "vault_path": "",
    "embedding_model": "BAAI/bge-small-zh-v1.5",
    "db_type": "milvus",
    "milvus_host": "localhost",
    "milvus_port": "19530",
    "milvus_collection": "obsidian_notes",
    "chroma_path": "",
    "chroma_collection": "obsidian_notes",
    "model_load_mode": "online",
    "model_local_path": "",
    "hf_endpoint": "",
    "api_host": "0.0.0.0",
    "api_port": 8000,
}


def _load_settings() -> dict:
    if not CONFIG_FILE.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        _save_settings(_DEFAULTS)
        print(
            f"Generated default config: {CONFIG_FILE}\n"
            f"Edit vault_path and other settings, then re-run."
        )
        return dict(_DEFAULTS)

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            user_settings: dict = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Warning: failed to read config ({exc}), using defaults.")
        return dict(_DEFAULTS)

    merged = dict(_DEFAULTS)
    merged.update(user_settings)
    if set(user_settings.keys()) != set(_DEFAULTS.keys()):
        _save_settings(merged)
    return merged


def _save_settings(settings: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
        f.write("\n")


def _get(key: str, env_var: str | None = None):
    if env_var and (val := os.getenv(env_var)) is not None:
        return val
    return _settings.get(key, _DEFAULTS.get(key))


def _get_int(key: str, env_var: str | None = None) -> int:
    return int(_get(key, env_var))


def _get_expanded_path(key: str, env_var: str | None = None, default_path: str = "") -> str:
    val = _get(key, env_var)
    if not val:
        return str(Path.expanduser(Path(default_path))) if default_path else ""
    return str(Path.expanduser(Path(val)))


_settings = _load_settings()

VAULT_PATH: str = _get_expanded_path("vault_path", "VAULT_PATH")
EMBEDDING_MODEL: str = _get("embedding_model", "EMBEDDING_MODEL")

MODEL_DIM_MAP: dict[str, int] = {
    "BAAI/bge-small-zh-v1.5": 512,
    "BAAI/bge-base-zh-v1.5": 768,
    "BAAI/bge-large-zh-v1.5": 1024,
    "Qwen/Qwen3-Embedding-0.6B": 1024,
    "Qwen/Qwen3-Embedding-1.8B": 1024,
}

EMBEDDING_DIM: int = MODEL_DIM_MAP.get(EMBEDDING_MODEL, 1024)
DB_TYPE: str = _get("db_type", "DB_TYPE").lower()

MILVUS_HOST: str = _get("milvus_host", "MILVUS_HOST")
MILVUS_PORT: str = _get("milvus_port", "MILVUS_PORT")
MILVUS_COLLECTION: str = _get("milvus_collection", "MILVUS_COLLECTION")

CHROMA_PATH: str = _get_expanded_path("chroma_path", "CHROMA_PATH", default_path="~/.chroma")
CHROMA_COLLECTION: str = _get("chroma_collection", "CHROMA_COLLECTION")

MODEL_LOAD_MODE: str = _get("model_load_mode", "MODEL_LOAD_MODE").lower()
MODEL_LOCAL_PATH: str = _get_expanded_path("model_local_path", "MODEL_LOCAL_PATH")
HF_ENDPOINT: str = _get("hf_endpoint", "HF_ENDPOINT")

API_HOST: str = _get("api_host", "API_HOST")
API_PORT: int = _get_int("api_port", "API_PORT")
