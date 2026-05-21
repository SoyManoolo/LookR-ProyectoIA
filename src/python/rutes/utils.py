from .models import RespuestaRecomendaciones, Recomendacion
from pathlib import Path
import re

_PYTHON_SRC = Path(__file__).resolve().parents[1]
_PROJECT_ROOT = Path(__file__).resolve().parents[3]

_STATIC = _PYTHON_SRC / "static"
_DATA   = _PROJECT_ROOT / "data"
_IMAGES = _DATA / "images"

def _formatear(resultados: list[tuple]) -> RespuestaRecomendaciones:
    items = []
    for r in resultados:
        imagen_path = r[4] if len(r) > 4 else ""
        categoria = r[5] if len(r) > 5 else []
        items.append(Recomendacion(
            id=r[0],
            score=r[1],
            nombre=r[2],
            descripcion=r[3],
            imagen_url=_imagen_url(imagen_path),
            categoria=categoria if isinstance(categoria, list) else [categoria],
            estilo=r[6] if len(r) > 6 else "",
        ))
    return RespuestaRecomendaciones(resultados=items)

def _imagen_url(imagen_path: str) -> str | None:
    if not imagen_path:
        return None
    p = Path(imagen_path)
    if not p.is_absolute():
        p = (_PROJECT_ROOT / p).resolve()
    try:
        rel = p.relative_to(_DATA)
        return f"/imagen/{rel}"
    except ValueError:
        return f"/imagen/images/{p.name}" if p.name else None
    
def _validar_top_k(top_k: int) -> int:
    return max(1, min(top_k, 50))

def _slugify(texto: str, max_palabras: int = 5) -> str:
    """Convierte una descripción en un nombre de archivo limpio."""
    import unicodedata
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^\w\s-]", "", texto.lower())
    palabras = texto.split()[:max_palabras]
    return "_".join(palabras) or "prenda"
