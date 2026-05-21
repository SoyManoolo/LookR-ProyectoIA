from fastapi.responses import FileResponse
from fastapi import HTTPException, APIRouter
from .utils import _DATA

router = APIRouter()

@router.get("/imagen/{filepath:path}")
async def servir_imagen(filepath: str):
    """Sirve imágenes desde cualquier subdirectorio de data/."""
    path = (_DATA / filepath).resolve()
    if not path.is_relative_to(_DATA) or not path.exists():
        raise HTTPException(status_code=404, detail="Imagen no encontrada.")
    return FileResponse(path)
