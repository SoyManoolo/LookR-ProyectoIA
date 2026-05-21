import mimetypes
from fastapi import HTTPException, UploadFile, File, APIRouter, Depends
from image_utils import describir_imagen_bytes
from pathlib import Path
import os

from .models import ResultadoAnalisis
from pinec.upload_data import subir_prenda
from .utils import _slugify, _IMAGES
from .dependencies import get_agent 


router = APIRouter()

@router.post("/analizar", response_model=ResultadoAnalisis)
async def analizar_imagen(imagen: UploadFile = File(...), agent = Depends(get_agent)):
    """Analiza una imagen con el agente, la sube a Pinecone y devuelve la descripción."""

    contenido = await imagen.read()
    suffix = Path(imagen.filename).suffix if imagen.filename else ".jpg"
    media_type, _ = mimetypes.guess_type(imagen.filename or "img.jpg")

    try:
        datos = await describir_imagen_bytes(agent, contenido, media_type or "image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al analizar la imagen: {e}")

    # Nombre basado en la descripción generada por el agente
    slug = _slugify(datos.descripcion)
    nombre_archivo = f"{slug}_{os.urandom(3).hex()}{suffix}"
    destino = _IMAGES / nombre_archivo
    destino.write_bytes(contenido)

    try:
        record_id = subir_prenda(datos, str(destino))
    except Exception as e:
        destino.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Error al subir a Pinecone: {e}")

    return ResultadoAnalisis(
        record_id=record_id,
        descripcion=datos.descripcion,
        categoria=datos.categoria,
        estilo=datos.estilo,
        imagen_url=f"/imagen/images/{nombre_archivo}",
    )
