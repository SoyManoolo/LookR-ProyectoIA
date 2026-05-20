import mimetypes

from pathlib import Path
from pydantic_ai import Agent, BinaryContent

from categories import DescripcionRopa
from config import project_path


# Función para detectar el tipo de archivo de la imagen (mimetype)
def detectar_media_type(image_path: str | Path) -> str:
    """Detecta el tipo MIME de un archivo de imagen basándose en su extensión."""
    # Usamos mimetypes para adivinar el tipo de archivo
    media_type, _ = mimetypes.guess_type(str(image_path))
    # Si no se detecta el tipo, usamos un tipo genérico por defecto
    return media_type or "application/octet-stream"

# Función para enviar los bytes de la imagen al agente y obtener la descripción estructurada
def describir_imagen_bytes(agent: Agent, image_bytes: bytes, media_type: str = "image/png") -> DescripcionRopa:
    """Envía los bytes de una imagen al agente y obtiene una descripción estructurada de la prenda."""
    # Ejecutamos el agente de forma síncrona, pasando los bytes de la imagen como contenido binario
    result = agent.run_sync([BinaryContent(data=image_bytes, media_type=media_type)])
    # Devolvemos solo la salida estructura con descripción, categoría y estilo
    return result.output

# Función principal que recibe una ruta de imagen, lee sus bytes y llama al análisis del agente
def describir_imagen(agent: Agent, image_path: str | Path) -> DescripcionRopa:
    """Lee una imagen desde una ruta de archivo y obtiene su descripción estructurada."""
    # Convertimos la ruta a un objeto Path para trabajar de forma más segura
    original_path = Path(image_path)
    path = original_path if original_path.is_absolute() else project_path(original_path)
    # Si el archivo no existe y está en la carpeta data, lo buscamos dentro de data/images
    if not path.exists() and original_path.parent == Path("data"):
        path = project_path(Path("data/images") / path.name)
    if not path.exists():
        raise FileNotFoundError(f"No se ha encontrado la imagen: {path}")
    # Leemos los bytes del archivo y detectamos el tipo MIME, luego los pasamos al agente
    return describir_imagen_bytes(agent, path.read_bytes(), detectar_media_type(path))
