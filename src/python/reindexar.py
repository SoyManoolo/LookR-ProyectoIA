"""
Reindexar imágenes en Pinecone con nombres generados por el agente de IA.

Modos:
  python reindexar.py            → procesa solo imágenes con nombre "malo" (Captura*, etc.)
  python reindexar.py --todo     → reindexación completa: limpia Pinecone y procesa TODO
  python reindexar.py "Captura*" → procesa las que coincidan con el patrón
"""
from __future__ import annotations

import asyncio
import fnmatch
import os
import re
import sys
import unicodedata
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / "data" / ".env")

from agent import crear_agente
from image_utils import describir_imagen_bytes
from pinec.embeddings import get_model
from pinec.upload_data import subir_prenda, dense_index

_IMAGES = Path(__file__).parent.parent.parent / "data" / "images"
_NAMESPACE = "mi-espacio"
_EXTENSIONES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

# Patrones de nombres "malos" que siempre se renombran
_PATRONES_MALOS = ["Captura*", "captura*", "Screenshot*", "Untitled*", "image*", "img*", "photo*"]


def _es_nombre_malo(nombre: str) -> bool:
    return any(fnmatch.fnmatch(nombre, p) for p in _PATRONES_MALOS)


def _slugify(texto: str, max_palabras: int = 5) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^\w\s-]", "", texto.lower())
    palabras = texto.split()[:max_palabras]
    return "_".join(palabras) or "prenda"


def _limpiar_namespace():
    """Elimina todos los vectores del namespace."""
    print("  Limpiando namespace en Pinecone...")
    dense_index.delete(delete_all=True, namespace=_NAMESPACE)
    print("  Namespace limpio.")


async def procesar_imagen(agent, imagen: Path, renombrar: bool) -> Path:
    import mimetypes
    media_type, _ = mimetypes.guess_type(str(imagen))
    contenido = imagen.read_bytes()

    datos = await describir_imagen_bytes(agent, contenido, media_type or "image/jpeg")
    print(f"  → {datos.descripcion}")

    destino = imagen
    if renombrar:
        slug = _slugify(datos.descripcion)
        nuevo_nombre = f"{slug}_{os.urandom(3).hex()}{imagen.suffix}"
        destino = _IMAGES / nuevo_nombre
        imagen.rename(destino)
        print(f"  Renombrada: {imagen.name} → {nuevo_nombre}")

    record_id = subir_prenda(datos, str(destino))
    print(f"  Subida con id: {record_id}")
    return destino


async def main():
    modo_todo = "--todo" in sys.argv
    patron = next((a for a in sys.argv[1:] if not a.startswith("--")), None)

    if modo_todo:
        imagenes = [
            p for p in sorted(_IMAGES.iterdir())
            if p.suffix.lower() in _EXTENSIONES
        ]
        print(f"Modo completo: {len(imagenes)} imágenes encontradas.")
        print("Se limpiará Pinecone y se reindexarán todas con el agente.")
        confirmar = input("¿Continuar? (s/N): ").strip().lower()
        if confirmar != "s":
            print("Cancelado.")
            return
        _limpiar_namespace()
        renombrar_todas = True
    elif patron:
        imagenes = sorted(_IMAGES.glob(patron))
        renombrar_todas = True
        print(f"Patrón '{patron}': {len(imagenes)} imágenes encontradas.")
    else:
        imagenes = [
            p for p in sorted(_IMAGES.iterdir())
            if p.suffix.lower() in _EXTENSIONES and _es_nombre_malo(p.name)
        ]
        renombrar_todas = True
        print(f"Imágenes con nombre incorrecto: {len(imagenes)}")

    if not imagenes:
        print("Nada que procesar.")
        return

    print("Cargando modelo CLIP y agente de IA...")
    get_model()
    agent = crear_agente()

    ok, errores = 0, 0
    for i, img in enumerate(imagenes, 1):
        print(f"\n[{i}/{len(imagenes)}] {img.name}")
        try:
            await procesar_imagen(agent, img, renombrar=renombrar_todas or _es_nombre_malo(img.name))
            ok += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            errores += 1

    print(f"\n{'='*40}")
    print(f"Completado: {ok} OK, {errores} errores.")


if __name__ == "__main__":
    asyncio.run(main())
