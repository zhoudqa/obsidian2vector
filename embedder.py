import numpy as np
from sentence_transformers import SentenceTransformer
import config

class Embedder:
    def __init__(self, model_name: str = None):
        self.model_name = model_name or config.EMBEDDING_MODEL
        print(f"\n📦 加载嵌入模型: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        self.dim = config.EMBEDDING_DIM
        print(f"   维度: {self.dim}")

    def encode(self, texts: list[str], show_progress: bool = True) -> np.ndarray:
        return self.model.encode(texts, show_progress_bar=show_progress)

    def encode_single(self, text: str) -> list:
        return self.model.encode([text]).tolist()