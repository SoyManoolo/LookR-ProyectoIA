
from fastapi import File, HTTPException, UploadFile, APIRouter, Depends
from pathlib import Path
import mimetypes

from .models import RespuestaArmario, ItemArmario, RespuestaRecomendaciones
from image_utils import describir_imagen_bytes
import armario as armario_mod
from .utils import _formatear
from .dependencies import get_agent

router = APIRouter()

@router.get("/armario/{user_id}", response_model=RespuestaArmario)
async def listar_armario(user_id: str):
    """Lista todas las prendas del armario personal del usuario."""
    items = armario_mod.listar(user_id)
    return RespuestaArmario(items=[ItemArmario(**i) for i in items])


@router.post("/armario/{user_id}", response_model=ItemArmario)
async def agregar_armario(user_id: str, imagen: UploadFile = File(...), agent = Depends(get_agent)):
    """Analiza una imagen y la guarda en el armario personal del usuario."""

    contenido = await imagen.read()
    media_type, _ = mimetypes.guess_type(imagen.filename or "img.jpg")
    suffix = Path(imagen.filename).suffix if imagen.filename else ".jpg"

    try:
        datos = await describir_imagen_bytes(agent, contenido, media_type or "image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al analizar: {e}")

    try:
        item = armario_mod.agregar(user_id, datos, contenido, suffix)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar en armario: {e}")

    return ItemArmario(**item)


@router.delete("/armario/{user_id}/{item_id}")
async def eliminar_armario(user_id: str, item_id: str):
    """Elimina una prenda del armario personal."""
    if not armario_mod.eliminar(user_id, item_id):
        raise HTTPException(status_code=404, detail="Prenda no encontrada.")
    return {"ok": True}


@router.get("/armario/{user_id}/{item_id}/similares", response_model=RespuestaRecomendaciones)
async def similares_armario(user_id: str, item_id: str, top_k: int = 6):
    """Busca en el catálogo prendas similares a una del armario personal."""
    resultados = armario_mod.similares_en_catalogo(item_id, user_id, top_k)
    return _formatear(resultados)
