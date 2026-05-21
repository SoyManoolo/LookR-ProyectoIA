from pathlib import Path

from PIL import Image
from sentence_transformers import SentenceTransformer

_clip_model = None
_text_model = None


def get_model() -> SentenceTransformer:
    global _clip_model
    if _clip_model is None:
        _clip_model = SentenceTransformer("clip-ViT-B-32", device="cpu")
    return _clip_model


def get_text_model() -> SentenceTransformer:
    """Modelo multilingüe para búsqueda semántica (768d). Corre en CPU para no competir con CLIP en GPU."""
    global _text_model
    if _text_model is None:
        _text_model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2", device="cpu")
    return _text_model


def embed_texto(texto: str) -> list[float]:
    return get_model().encode(texto).tolist()


def embed_imagen(imagen_path: str | Path) -> list[float]:
    img = Image.open(str(imagen_path)).convert("RGB")
    return get_model().encode(img).tolist()


def embed_descripcion(texto: str) -> list[float]:
    """Embede texto en español con modelo multilingüe (768d)."""
    return get_text_model().encode(texto).tolist()


def embed_combinado(imagen_path: str | Path, texto: str, alpha: float = 0.7) -> list[float]:
    """Combina embedding visual y textual en el espacio CLIP (512d).

    alpha controla el peso de la imagen (0.0 = solo texto, 1.0 = solo imagen).
    """
    import numpy as np
    img_vec = np.array(embed_imagen(imagen_path))
    txt_vec = np.array(embed_texto(texto))
    combined = alpha * img_vec + (1.0 - alpha) * txt_vec
    norm = np.linalg.norm(combined)
    if norm > 0:
        combined = combined / norm
    return combined.tolist()
