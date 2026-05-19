from __future__ import annotations

import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv(Path(__file__).parent.parent.parent / "data" / ".env")

from pinec.search import search
from pinec.embeddings import get_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cargamos el modelo CLIP al arrancar para que la primera petición no tarde
    get_model()
    yield


app = FastAPI(title="Recomendador de ropa", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_STATIC = Path(__file__).parent / "static"
_IMAGES = Path(__file__).parent.parent.parent / "data" / "images"
app.mount("/static", StaticFiles(directory=_STATIC), name="static")


@app.get("/")
async def index():
    return FileResponse(_STATIC / "index.html")


@app.get("/imagen/{filename}")
async def servir_imagen(filename: str):
    """Sirve imágenes del dataset desde data/images/."""
    path = _IMAGES / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Imagen no encontrada.")
    return FileResponse(path)


class Recomendacion(BaseModel):
    id: str
    score: float
    nombre: str
    descripcion: str
    imagen_url: str | None = None
    categoria: list[str] = []
    estilo: str = ""


class RespuestaRecomendaciones(BaseModel):
    resultados: list[Recomendacion]


def _formatear(resultados: list[tuple]) -> RespuestaRecomendaciones:
    items = []
    for r in resultados:
        imagen_path = r[4] if len(r) > 4 else ""
        filename = Path(imagen_path).name if imagen_path else None
        categoria = r[5] if len(r) > 5 else []
        items.append(Recomendacion(
            id=r[0],
            score=r[1],
            nombre=r[2],
            descripcion=r[3],
            imagen_url=f"/imagen/{filename}" if filename else None,
            categoria=categoria if isinstance(categoria, list) else [categoria],
            estilo=r[6] if len(r) > 6 else "",
        ))
    return RespuestaRecomendaciones(resultados=items)


@app.get("/recomendar/texto", response_model=RespuestaRecomendaciones)
async def recomendar_por_texto_get(query: str, top_k: int = 5):
    """Recomienda prendas por texto (GET). Úsalo desde el navegador o curl."""
    if not query.strip():
        raise HTTPException(status_code=400, detail="El texto no puede estar vacío.")
    return _formatear(search(query, por_imagen=False, top_k=top_k))


@app.post("/recomendar/texto", response_model=RespuestaRecomendaciones)
async def recomendar_por_texto(query: str = Form(...), top_k: int = Form(5)):
    """Recomienda prendas similares a partir de una descripción de texto."""
    if not query.strip():
        raise HTTPException(status_code=400, detail="El texto no puede estar vacío.")
    return _formatear(search(query, por_imagen=False, top_k=top_k))


@app.post("/recomendar/imagen", response_model=RespuestaRecomendaciones)
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
        resultados = search(tmp_path, por_imagen=True, top_k=top_k)
    finally:
        os.unlink(tmp_path)

    return _formatear(resultados)


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)
