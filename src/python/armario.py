"""
Gestión del armario personal de cada usuario.

Almacenamiento:
  - Metadatos: data/armarios/{user_id}.json
  - Imágenes:  data/images/armario/{user_id}_{item_id}.{ext}
  - Vectores:  Pinecone buscador-semantico, namespace "armario-{user_id}"
"""
from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

from pinec.index import crear_index_semantico
from pinec.embeddings import embed_descripcion

_PROJECT_ROOT = Path(__file__).parent.parent.parent
_ARMARIOS_DIR = _PROJECT_ROOT / "data" / "armarios"
_IMAGES_DIR   = _PROJECT_ROOT / "data" / "images" / "armario"
_ARMARIOS_DIR.mkdir(parents=True, exist_ok=True)
_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

semantic_index = crear_index_semantico()


# ── Persistencia local ─────────────────────────────────────────────────────────

def _ruta_json(user_id: str) -> Path:
    return _ARMARIOS_DIR / f"{user_id}.json"


def _cargar(user_id: str) -> list[dict]:
    ruta = _ruta_json(user_id)
    if not ruta.exists():
        return []
    return json.loads(ruta.read_text(encoding="utf-8"))


def _guardar(user_id: str, items: list[dict]):
    _ruta_json(user_id).write_text(
        json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ── Operaciones ────────────────────────────────────────────────────────────────

def listar(user_id: str) -> list[dict]:
    """Devuelve todas las prendas del armario del usuario."""
    return _cargar(user_id)


def agregar(user_id: str, datos, imagen_bytes: bytes, suffix: str) -> dict:
    """Analiza y guarda una prenda en el armario personal.

    Guarda la imagen en disco, los metadatos en JSON y el vector en Pinecone.
    """
    item_id = str(uuid.uuid4())
    namespace = f"armario-{user_id}"

    # Guardar imagen
    nombre_archivo = f"{user_id[:8]}_{item_id[:8]}{suffix}"
    img_path = _IMAGES_DIR / nombre_archivo
    img_path.write_bytes(imagen_bytes)
    imagen_url = f"/imagen/images/armario/{nombre_archivo}"

    # Metadatos
    nombre = datos.descripcion.split(",")[0].strip()[:60]
    item = {
        "id": item_id,
        "nombre": nombre,
        "descripcion": datos.descripcion,
        "categoria": datos.categoria,
        "estilo": datos.estilo,
        "imagen_url": imagen_url,
        "imagen_path": str(img_path),
    }

    # Persistir en JSON
    items = _cargar(user_id)
    items.append(item)
    _guardar(user_id, items)

    # Subir vector semántico a Pinecone (namespace propio del usuario)
    texto = f"{datos.descripcion}. Categorías: {', '.join(datos.categoria)}. Estilo: {datos.estilo}"
    pinecone_meta = {**item, "imagen": str(img_path)}
    semantic_index.upsert(
        vectors=[{"id": item_id, "values": embed_descripcion(texto), "metadata": pinecone_meta}],
        namespace=namespace,
    )

    return item


def eliminar(user_id: str, item_id: str) -> bool:
    """Elimina una prenda del armario (JSON + Pinecone). Devuelve True si existía."""
    items = _cargar(user_id)
    nuevo = [i for i in items if i["id"] != item_id]
    if len(nuevo) == len(items):
        return False

    # Eliminar imagen del disco
    eliminado = next((i for i in items if i["id"] == item_id), None)
    if eliminado:
        Path(eliminado.get("imagen_path", "")).unlink(missing_ok=True)

    _guardar(user_id, nuevo)

    # Eliminar de Pinecone
    try:
        semantic_index.delete(ids=[item_id], namespace=f"armario-{user_id}")
    except Exception as e:
        logger.error("Error eliminando vector de Pinecone (id=%s, user=%s): %s", item_id, user_id, e)

    return True


def similares_en_catalogo(item_id: str, user_id: str, top_k: int = 6) -> list[tuple]:
    """Busca en el catálogo prendas que combinan con una prenda del armario."""
    from pinec.search import _formatear

    # Recuperar el vector del armario del usuario
    try:
        resp = semantic_index.fetch(ids=[item_id], namespace=f"armario-{user_id}")
    except Exception as e:
        logger.error("Error al recuperar vector del armario (id=%s, user=%s): %s", item_id, user_id, e)
        return []
    if item_id not in resp.vectors:
        return []

    meta = resp.vectors[item_id].metadata
    query = f"{meta.get('descripcion', '')}. {' '.join(meta.get('categoria', []))}. {meta.get('estilo', '')}"

    # Buscar en el catálogo (namespace mi-espacio)
    vector = embed_descripcion(query)
    results = semantic_index.query(
        namespace="mi-espacio", vector=vector,
        top_k=top_k, include_metadata=True,
    )
    return _formatear(results["matches"])
