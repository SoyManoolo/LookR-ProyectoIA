import json
import mimetypes
import re
import unicodedata

from pathlib import Path
from pydantic_ai import Agent, BinaryContent

from categories import DescripcionRopa, categorias_permitidas
from config import project_path


_CATEGORIA_ALIASES = {
    "zapato": "zapatos",
    "botas": "bota",
    "sandalias": "sandalia",
    "zapatillas": "deportivas",
    "deportiva": "deportivas",
    "pantalones": "pantalón",
    "pantalon": "pantalón",
    "joyeria": "joyería",
}


def _normalizar_categoria(categoria: str) -> str:
    normalizada = categoria.strip().lower()
    sin_acentos = unicodedata.normalize("NFKD", normalizada).encode("ascii", "ignore").decode()
    return _CATEGORIA_ALIASES.get(sin_acentos, _CATEGORIA_ALIASES.get(normalizada, normalizada))


# Función para detectar el tipo de archivo de la imagen (mimetype)
def detectar_media_type(image_path: str | Path) -> str:
    """Detecta el tipo MIME de un archivo de imagen basándose en su extensión."""
    # Usamos mimetypes para adivinar el tipo de archivo
    media_type, _ = mimetypes.guess_type(str(image_path))
    # Si no se detecta el tipo, usamos un tipo genérico por defecto
    return media_type or "application/octet-stream"

# Función para enviar los bytes de la imagen al agente y obtener la descripción estructurada
async def describir_imagen_bytes(agent: Agent, image_bytes: bytes, media_type: str = "image/png") -> DescripcionRopa:
    """Envía los bytes de una imagen al agente y obtiene una descripción estructurada de la prenda."""
    result = await agent.run([BinaryContent(data=image_bytes, media_type=media_type)])
    texto = result.output.strip()
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', texto, re.DOTALL)
    if match:
        texto = match.group(1)
    data = json.loads(texto)
    if isinstance(data.get("categoria"), str):
        data["categoria"] = [data["categoria"]]
    data["categoria"] = [
        categoria
        for categoria in (_normalizar_categoria(c) for c in data.get("categoria", []))
        if categoria in categorias_permitidas
    ] or ["otro"]
    return DescripcionRopa.model_validate(data)

# Función principal que recibe una ruta de imagen, lee sus bytes y llama al análisis del agente
def describir_imagen(agent: Agent, image_path: str | Path) -> DescripcionRopa:
    """Lee una imagen desde una ruta de archivo y obtiene su descripción estructurada (CLI)."""
    import asyncio
    
    # Resolución de rutas robusta
    original_path = Path(image_path)
    path = original_path if original_path.is_absolute() else project_path(original_path)
    
    # Lógica para buscar en data/images si no existe en la raíz
    if not path.exists() and original_path.parent == Path("data"):
        path = project_path(Path("data/images") / path.name)
        
    if not path.exists():
        raise FileNotFoundError(f"No se ha encontrado la imagen: {path}")
    
    # Ejecución asíncrona para que no falle el script
    return asyncio.run(describir_imagen_bytes(agent, path.read_bytes(), detectar_media_type(path)))
