from fastapi import File, HTTPException, UploadFile
from pathlib import Path
from fastapi import File, Form, APIRouter
import os
import tempfile

from .utils import _formatear, _validar_top_k
from pinec.search import search, search_combinado
from .models import RespuestaRecomendaciones

router = APIRouter()

@router.get("/recomendar/texto", response_model=RespuestaRecomendaciones)
async def recomendar_por_texto_get(query: str, top_k: int = 5):
    """Recomienda prendas por texto (GET). Úsalo desde el navegador o curl."""
    if not query.strip():
        raise HTTPException(status_code=400, detail="El texto no puede estar vacío.")
    return _formatear(search(query, por_imagen=False, top_k=_validar_top_k(top_k)))


@router.post("/recomendar/texto", response_model=RespuestaRecomendaciones)
async def recomendar_por_texto(query: str = Form(...), top_k: int = Form(5)):
    """Recomienda prendas similares a partir de una descripción de texto."""
    if not query.strip():
        raise HTTPException(status_code=400, detail="El texto no puede estar vacío.")
    return _formatear(search(query, por_imagen=False, top_k=_validar_top_k(top_k)))


@router.post("/recomendar/imagen", response_model=RespuestaRecomendaciones)
async def recomendar_por_imagen(
    imagen: UploadFile = File(...),
    top_k: int = Form(5),
):
    """Recomienda prendas similares a partir de una imagen subida."""
    suffix = Path(imagen.filename).suffix if imagen.filename else ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await imagen.read())
        tmp_path = tmp.name

    try:
        resultados = search(tmp_path, por_imagen=True, top_k=_validar_top_k(top_k))
    finally:
        os.unlink(tmp_path)

    return _formatear(resultados)


@router.post("/recomendar/combinado", response_model=RespuestaRecomendaciones)
async def recomendar_combinado(
    imagen: UploadFile = File(...),
    texto: str = Form(""),
    top_k: int = Form(6),
    alpha: float = Form(0.7),
):
    """Búsqueda multimodal: imagen base + modificador de texto.

    alpha controla el peso de la imagen (0.0–1.0). Por defecto 0.7 (70% imagen, 30% texto).
    Si texto está vacío, equivale a búsqueda por imagen normal.
    """
    suffix = Path(imagen.filename).suffix if imagen.filename else ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await imagen.read())
        tmp_path = tmp.name

    try:
        resultados = search_combinado(tmp_path, texto, top_k=_validar_top_k(top_k), alpha=alpha)
    finally:
        os.unlink(tmp_path)

    return _formatear(resultados)
