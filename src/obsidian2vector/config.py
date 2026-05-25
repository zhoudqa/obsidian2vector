import json
import os
from pathlib import Path

# ── 跨平台配置目录 ──────────────────────────────────────────
# macOS/Linux: ~/.obsidian2vector/settings.json
# Windows:     C:\Users\<user>\.obsidian2vector\settings.json
CONFIG_DIR = Path.home() / ".obsidian2vector"
CONFIG_FILE = CONFIG_DIR / "settings.json"

# ── 默认配置 ────────────────────────────────────────────────
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
    """从 settings.json 加载配置，文件不存在则自动创建并返回默认值。"""
    if not CONFIG_FILE.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        _save_settings(_DEFAULTS)
        print(
            f"已生成默认配置文件: {CONFIG_FILE}\n"
            f"请编辑该文件设置 vault_path 等 parameters 后重新运行。"
        )
        return dict(_DEFAULTS)

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            user_settings: dict = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"警告: 读取配置文件失败 ({exc})，使用默认值。")
        return dict(_DEFAULTS)

    # 合并：用户配置覆盖默认值，缺失字段用默认值填充
    merged = dict(_DEFAULTS)
    merged.update(user_settings)
    # 回写一次以补全新增的默认字段
    if set(user_settings.keys()) != set(_DEFAULTS.keys()):
        _save_settings(merged)
    return merged


def _save_settings(settings: dict) -> None:
    """将配置写入 settings.json。"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
        f.write("\n")


def _get(key: str, env_var: str | None = None):
    """
    优先级: 环境变量 > settings.json > 默认值。
    env_var 为 None 时表示该配置不支持环境变量覆盖。
    """
    # 1) 环境变量（向后兼容）
    if env_var and (val := os.getenv(env_var)) is not None:
        return val
    # 2) settings.json 中的值
    return _settings.get(key, _DEFAULTS.get(key))


def _get_int(key: str, env_var: str | None = None) -> int:
    val = _get(key, env_var)
    return int(val)


def _get_expanded_path(key: str, env_var: str | None = None, default_path: str = "") -> str:
    """获取路径配置，自动展开 ~ 和相对路径。"""
    val = _get(key, env_var)
    if not val:
        return str(Path.expanduser(Path(default_path))) if default_path else ""
    return str(Path.expanduser(Path(val)))


# ── 加载配置 ────────────────────────────────────────────────
_settings = _load_settings()

# ── 导出模块级变量（与现有代码 config.XXX 完全兼容）────────
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
