"""
Carga masiva de imágenes al catálogo.

Uso:
    python upload_batch.py --carpeta ./fotos_tienda
    python upload_batch.py --carpeta ./fotos_tienda --reanudar
    python upload_batch.py --carpeta ./fotos_tienda --reanudar --limite 50
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Forzar CPU — el batch no necesita GPU y no debe competir con el servidor
os.environ["CUDA_VISIBLE_DEVICES"] = ""

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

from agent import crear_agente
from image_utils import describir_imagen_bytes, detectar_media_type
from pinec.upload_data import subir_prenda

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

EXTENSIONES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
_LOG_NOMBRE = ".upload_log.json"


def _cargar_log(carpeta: Path) -> dict[str, str]:
    """Devuelve {nombre_archivo: record_id} de las imágenes ya procesadas."""
    ruta = carpeta / _LOG_NOMBRE
    if ruta.exists():
        return json.loads(ruta.read_text(encoding="utf-8"))
    return {}


def _guardar_log(carpeta: Path, procesados: dict[str, str]) -> None:
    ruta = carpeta / _LOG_NOMBRE
    ruta.write_text(json.dumps(procesados, indent=2, ensure_ascii=False), encoding="utf-8")


async def procesar_carpeta(carpeta: Path, reanudar: bool, limite: int | None, aleatorio: bool = False) -> None:
    agente = crear_agente()

    # El log siempre se carga para evitar repeticiones entre ejecuciones.
    # --reanudar=False solo significa "empezar desde cero": borra el log previo.
    if not reanudar:
        log_path = carpeta / _LOG_NOMBRE
        if log_path.exists():
            log_path.unlink()
    procesados = _cargar_log(carpeta)

    imagenes = sorted(f for f in carpeta.iterdir() if f.suffix.lower() in EXTENSIONES)
    pendientes = [f for f in imagenes if f.name not in procesados]

    if aleatorio:
        import random
        random.shuffle(pendientes)

    if limite:
        pendientes = pendientes[:limite]

    total = len(pendientes)
    ya_hechas = len(procesados)
    logger.info("Imágenes totales: %d | Ya procesadas: %d | Pendientes: %d",
                len(imagenes), ya_hechas, total)

    if not total:
        logger.info("Nada que procesar.")
        return

    errores: list[tuple[str, str]] = []

    for i, img_path in enumerate(pendientes, 1):
        logger.info("[%d/%d] %s", i, total, img_path.name)
        try:
            imagen_bytes = img_path.read_bytes()
            media_type = detectar_media_type(img_path)
            datos = await describir_imagen_bytes(agente, imagen_bytes, media_type)
            record_id = subir_prenda(datos, str(img_path.resolve()))
            procesados[img_path.name] = record_id
            _guardar_log(carpeta, procesados)
            logger.info("  OK  %s  [id=%s]", datos.descripcion[:60], record_id)
        except Exception as e:
            logger.error("  ERR %s: %s", img_path.name, e)
            errores.append((img_path.name, str(e)))

    ok = total - len(errores)
    logger.info("\n=== Resumen: %d OK | %d errores ===", ok, len(errores))
    for nombre, err in errores:
        logger.error("  - %s: %s", nombre, err)


def main() -> None:
    parser = argparse.ArgumentParser(description="Carga masiva de imágenes al catálogo")
    parser.add_argument("--carpeta", required=True, help="Ruta a la carpeta con imágenes")
    parser.add_argument("--reanudar", action="store_true",
                        help="Saltar imágenes ya procesadas (lee .upload_log.json)")
    parser.add_argument("--limite", type=int, default=None,
                        help="Número máximo de imágenes a procesar en esta ejecución")
    parser.add_argument("--aleatorio", action="store_true",
                        help="Seleccionar imágenes en orden aleatorio para mayor variedad")
    args = parser.parse_args()

    carpeta = Path(args.carpeta)
    if not carpeta.is_dir():
        logger.error("La carpeta '%s' no existe o no es un directorio.", carpeta)
        sys.exit(1)

    asyncio.run(procesar_carpeta(carpeta, args.reanudar, args.limite, args.aleatorio))


if __name__ == "__main__":
    main()
