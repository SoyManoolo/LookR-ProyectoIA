import mimetypes
from models import ResultadoDescubrir
from utils import _formatear, _validar_top_k
from fastapi import HTTPException, UploadFile, File, Form, APIRouter, Depends
from image_utils import describir_imagen_bytes

from pinec.search import search
from dependencies import get_agent

router = APIRouter()

@router.post("/descubrir", response_model=ResultadoDescubrir)
async def descubrir_por_imagen(imagen: UploadFile = File(...), top_k: int = Form(6), agent = Depends(get_agent)):
    """Analiza una imagen con el agente y devuelve recomendaciones similares sin añadir al catálogo."""

    contenido = await imagen.read()
    media_type, _ = mimetypes.guess_type(imagen.filename or "img.jpg")

    try:
        datos = await describir_imagen_bytes(agent, contenido, media_type or "image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al analizar la imagen: {e}")

    query = f"{datos.descripcion}. Estilo: {datos.estilo}. {' '.join(datos.categoria)}"
    resultados = search(query, por_imagen=False, top_k=_validar_top_k(top_k))

    return ResultadoDescubrir(
        descripcion=datos.descripcion,
        categoria=datos.categoria,
        estilo=datos.estilo,
        recomendaciones=_formatear(resultados).resultados,
    )
