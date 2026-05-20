from __future__ import annotations

import mimetypes
import os
import re
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

from pinec.search import search, search_combinado
from pinec.embeddings import get_model, get_text_model
from pinec.upload_data import subir_prenda
from image_utils import describir_imagen_bytes
from agent import crear_agente
import armario as armario_mod

_agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _agent
    get_model()
    get_text_model()
    _agent = crear_agente()
    yield


app = FastAPI(title="Recomendador de ropa", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_STATIC = Path(__file__).parent / "static"
_DATA   = Path(__file__).parent.parent.parent / "data"
_IMAGES = _DATA / "images"
app.mount("/static", StaticFiles(directory=_STATIC), name="static")


@app.get("/")
async def index():
    return FileResponse(_STATIC / "index.html")


@app.get("/imagen/{filepath:path}")
async def servir_imagen(filepath: str):
    """Sirve imágenes desde cualquier subdirectorio de data/."""
    path = (_DATA / filepath).resolve()
    if not path.is_relative_to(_DATA) or not path.exists():
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


def _imagen_url(imagen_path: str) -> str | None:
    if not imagen_path:
        return None
    p = Path(imagen_path)
    if not p.is_absolute():
        p = (Path(__file__).parent / p).resolve()
    try:
        rel = p.relative_to(_DATA)
        return f"/imagen/{rel}"
    except ValueError:
        return f"/imagen/images/{p.name}" if p.name else None


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


def _validar_top_k(top_k: int) -> int:
    return max(1, min(top_k, 50))


@app.get("/recomendar/texto", response_model=RespuestaRecomendaciones)
async def recomendar_por_texto_get(query: str, top_k: int = 5):
    """Recomienda prendas por texto (GET). Úsalo desde el navegador o curl."""
    if not query.strip():
        raise HTTPException(status_code=400, detail="El texto no puede estar vacío.")
    return _formatear(search(query, por_imagen=False, top_k=_validar_top_k(top_k)))


@app.post("/recomendar/texto", response_model=RespuestaRecomendaciones)
async def recomendar_por_texto(query: str = Form(...), top_k: int = Form(5)):
    """Recomienda prendas similares a partir de una descripción de texto."""
    if not query.strip():
        raise HTTPException(status_code=400, detail="El texto no puede estar vacío.")
    return _formatear(search(query, por_imagen=False, top_k=_validar_top_k(top_k)))


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
        resultados = search(tmp_path, por_imagen=True, top_k=_validar_top_k(top_k))
    finally:
        os.unlink(tmp_path)

    return _formatear(resultados)


@app.post("/recomendar/combinado", response_model=RespuestaRecomendaciones)
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


class ResultadoAnalisis(BaseModel):
    record_id: str
    descripcion: str
    categoria: list[str]
    estilo: str
    imagen_url: str | None = None


def _slugify(texto: str, max_palabras: int = 5) -> str:
    """Convierte una descripción en un nombre de archivo limpio."""
    import unicodedata
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^\w\s-]", "", texto.lower())
    palabras = texto.split()[:max_palabras]
    return "_".join(palabras) or "prenda"


@app.post("/analizar", response_model=ResultadoAnalisis)
async def analizar_imagen(imagen: UploadFile = File(...)):
    """Analiza una imagen con el agente, la sube a Pinecone y devuelve la descripción."""
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agente no disponible.")

    contenido = await imagen.read()
    suffix = Path(imagen.filename).suffix if imagen.filename else ".jpg"
    media_type, _ = mimetypes.guess_type(imagen.filename or "img.jpg")

    try:
        datos = await describir_imagen_bytes(_agent, contenido, media_type or "image/jpeg")
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
        imagen_url=f"/imagen/{nombre_archivo}",
    )


class ResultadoDescubrir(BaseModel):
    descripcion: str
    categoria: list[str]
    estilo: str
    recomendaciones: list[Recomendacion]


@app.post("/descubrir", response_model=ResultadoDescubrir)
async def descubrir_por_imagen(imagen: UploadFile = File(...), top_k: int = Form(6)):
    """Analiza una imagen con el agente y devuelve recomendaciones similares sin añadir al catálogo."""
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agente no disponible.")

    contenido = await imagen.read()
    media_type, _ = mimetypes.guess_type(imagen.filename or "img.jpg")

    try:
        datos = await describir_imagen_bytes(_agent, contenido, media_type or "image/jpeg")
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


# ── Armario personal ──────────────────────────────────────────────────────────

class ItemArmario(BaseModel):
    id: str
    nombre: str
    descripcion: str
    categoria: list[str]
    estilo: str
    imagen_url: str | None = None


class RespuestaArmario(BaseModel):
    items: list[ItemArmario]


@app.get("/armario/{user_id}", response_model=RespuestaArmario)
async def listar_armario(user_id: str):
    """Lista todas las prendas del armario personal del usuario."""
    items = armario_mod.listar(user_id)
    return RespuestaArmario(items=[ItemArmario(**i) for i in items])


@app.post("/armario/{user_id}", response_model=ItemArmario)
async def agregar_armario(user_id: str, imagen: UploadFile = File(...)):
    """Analiza una imagen y la guarda en el armario personal del usuario."""
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agente no disponible.")

    contenido = await imagen.read()
    media_type, _ = mimetypes.guess_type(imagen.filename or "img.jpg")
    suffix = Path(imagen.filename).suffix if imagen.filename else ".jpg"

    try:
        datos = await describir_imagen_bytes(_agent, contenido, media_type or "image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al analizar: {e}")

    try:
        item = armario_mod.agregar(user_id, datos, contenido, suffix)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar en armario: {e}")

    return ItemArmario(**item)


@app.delete("/armario/{user_id}/{item_id}")
async def eliminar_armario(user_id: str, item_id: str):
    """Elimina una prenda del armario personal."""
    if not armario_mod.eliminar(user_id, item_id):
        raise HTTPException(status_code=404, detail="Prenda no encontrada.")
    return {"ok": True}


@app.get("/armario/{user_id}/{item_id}/similares", response_model=RespuestaRecomendaciones)
async def similares_armario(user_id: str, item_id: str, top_k: int = 6):
    """Busca en el catálogo prendas similares a una del armario personal."""
    resultados = armario_mod.similares_en_catalogo(item_id, user_id, top_k)
    return _formatear(resultados)


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)
