from pathlib import Path

from PIL import Image
from sentence_transformers import SentenceTransformer

_model = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("clip-ViT-B-32")
    return _model

def embed_texto(texto: str) -> list[float]:
    return get_model().encode(texto).tolist()

def embed_imagen(imagen_path: str | Path) -> list[float]:
    img = Image.open(str(imagen_path)).convert("RGB")
    return get_model().encode(img).tolist()
