import os
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
from obsidian2vector import config


class Embedder:
    def __init__(self, model_name: str = None):
        self.model_name = model_name or config.EMBEDDING_MODEL
        self.load_mode = config.MODEL_LOAD_MODE
        print(f"\nLoading embedding model: {self.model_name}")
        mode = "offline" if self.load_mode == "offline" else "online"
        print(f"   mode: {mode}")

        if self.load_mode == "offline":
            self.model = self._load_offline()
        else:
            self.model = self._load_online()

        self.dim = config.EMBEDDING_DIM
        print(f"   dim: {self.dim}")

    def _load_offline(self) -> SentenceTransformer:
        local_path = config.MODEL_LOCAL_PATH
        if local_path:
            model_dir = Path(local_path)
            if model_dir.is_dir():
                print(f"   local path: {model_dir}")
                return SentenceTransformer(str(model_dir))
            raise FileNotFoundError(
                f"MODEL_LOCAL_PATH not found: {local_path}"
            )

        if self._model_in_cache(self.model_name):
            print("   loading from HuggingFace cache")
            return SentenceTransformer(self.model_name)

        raise FileNotFoundError(
            f"Model '{self.model_name}' not found in offline mode.\n"
            f"   1. Set MODEL_LOCAL_PATH to local model directory\n"
            f"   2. Run online mode first to cache model to ~/.cache/huggingface/hub/"
        )

    def _load_online(self) -> SentenceTransformer:
        if config.HF_ENDPOINT:
            os.environ["HF_ENDPOINT"] = config.HF_ENDPOINT
            print(f"   HF mirror: {config.HF_ENDPOINT}")
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
