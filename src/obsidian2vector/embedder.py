import os
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
from obsidian2vector import config


class Embedder:
    def __init__(self, model_name: str = None):
        self.model_name = model_name or config.EMBEDDING_MODEL
        self.load_mode = config.MODEL_LOAD_MODE
        print(f"\n📦 加载嵌入模型: {self.model_name}")
        print(f"   模式: {'离线 (offline)' if self.load_mode == 'offline' else '在线 (online)'}")

        if self.load_mode == "offline":
            self.model = self._load_offline()
        else:
            self.model = self._load_online()

        self.dim = config.EMBEDDING_DIM
        print(f"   维度: {self.dim}")

    def _load_offline(self) -> SentenceTransformer:
        local_path = config.MODEL_LOCAL_PATH
        if local_path:
            model_dir = Path(local_path)
            if model_dir.is_dir():
                print(f"   本地路径: {model_dir}")
                return SentenceTransformer(str(model_dir))
            raise FileNotFoundError(
                f"❌ MODEL_LOCAL_PATH 指定的路径不存在: {local_path}"
            )

        if self._model_in_cache(self.model_name):
            print("   从 HuggingFace 缓存加载")
            return SentenceTransformer(self.model_name)

        raise FileNotFoundError(
            f"❌ 离线模式下找不到模型 '{self.model_name}'。\n"
            f"   解决方式:\n"
            f"   1. 设置 MODEL_LOCAL_PATH 环境变量指向本地模型目录\n"
            f"   2. 先用在线模式运行一次, 模型会自动缓存到 ~/.cache/huggingface/hub/"
        )

    def _load_online(self) -> SentenceTransformer:
        if config.HF_ENDPOINT:
            os.environ["HF_ENDPOINT"] = config.HF_ENDPOINT
            print(f"   HF 镜像: {config.HF_ENDPOINT}")
        return SentenceTransformer(self.model_name)

    @staticmethod
    def _model_in_cache(model_name: str) -> bool:
        cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
        model_dir_name = f"models--{model_name.replace('/', '--')}"
        return (cache_dir / model_dir_name).is_dir()

    def encode(self, texts: list[str], show_progress: bool = True) -> np.ndarray:
        return self.model.encode(texts, show_progress_bar=show_progress)

    def encode_single(self, text: str) -> list:
        return self.model.encode([text]).tolist()
