from __future__ import annotations

import argparse
import json
import logging
import mimetypes
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_ai import Agent, BinaryContent
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.providers.ollama import OllamaProvider


logging.basicConfig(level=logging.INFO)
load_dotenv()

# Categorias utilizadas para que el agente elija una o mas de estas
Categoria = Literal[
    "vestido",
    "chaqueta",
    "pantalón",
    "camisa",
    "camiseta",
    "blusa",
    "falda",
    "abrigo",
    "traje",
    "jersey",
    "sudadera",
    "top",
    "zapatos",
    "bota",
    "deportivas",
    "accesorio",
    "bolso",
    "joyería",
    "gafas",
    "elegante",
    "casual",
    "formal",
    "deportivo",
    "noche",
    "otro",
]

# Cargamos las categorias en una variable para pasarselas todas al agente
categorias_permitidas = Categoria.__args__

# Definimos todas las claves que tendrá la respuesta del agente
class DescripcionRopa(BaseModel):
    descripcion: str
    categoria: list[Categoria]
    estilo: str

# Función para cargar unos ejemplos de descripción para que el agente tenga algunos ejemplos, ya que no se hace fine tuning
def cargar_ejemplos_entrenamiento(path: str | Path | None = None, limite: int = 3) -> str:
    """Carga pocos ejemplos JSONL para guiar al modelo sin fine tuning completo."""
    examples_path = Path(path or os.getenv("TRAINING_EXAMPLES_PATH", "data/examples/training_examples.json"))
    # En caso de que el path no exista devolvemos un string vacio
    if not examples_path.exists():
        return ""

    # Si el path existe vamos guardando los ejemplos del json en la lista
    ejemplos: list[str] = []
    for line in examples_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        output = data.get("output", data)
        ejemplos.append(json.dumps(output, ensure_ascii=False))
        if len(ejemplos) >= limite:
            break

    # Si la lista queda vacia se le pasa un string vacio
    if not ejemplos:
        return ""

    # En el caso de tener ejemplos en la lista se lo devolvemos junto a un pequeño texto con contexto
    return (
        "Ejemplos de estilo de respuesta para mantener consistencia:\n"
        + "\n".join(f"- {ejemplo}" for ejemplo in ejemplos)
    )

# Función para crear el agente de pydantic
def crear_agente() -> Agent:
    # Cargamos una de las posibles url que deben estar configuradas en el .env, en caso contrario se utiliza la url local por defecto de ollama
    url = (
        os.getenv("OLLAMA_BASE_URL")
        or os.getenv("OLLAMA_LOCAL")
        or "http://localhost:11434/v1"
    )

    # Guardamos el nombre del modelo del .env, en caso contrario 
    model_name = os.getenv("OLLAMA_MODEL", "gemma4:e4b")
    contexto_ejemplos = cargar_ejemplos_entrenamiento()

    # Instanciamos el modelo
    model = OllamaModel(
        model_name,
        provider=OllamaProvider(base_url=url),
    )

    # Creamos el system_prompt que le vamos a pasar al agente, tratando de ser lo más específicos posibles, pasandole los ejemplos cargados y las categorias permitidas
    system_prompt = "\n".join(
        [
            "Eres un experto en moda.",
            "Analiza prendas de ropa en imágenes y devuelve descripciones estructuradas y atractivas para el cliente.",
            "Devuelve SOLO JSON, sin markdown ni texto extra.",
            'El JSON SOLO puede contener estas llaves: "descripcion", "categoria" y "estilo".',
            "La descripción debe ser atractiva pero breve, máximo 30 palabras.",
            "Incluye todas las categorías que apliquen, pero elige solo un tipo de prenda principal.",
            'Puedes añadir etiquetas de uso como "elegante", "casual", "formal", "deportivo", "noche" o "accesorio" si aplican.',
            f'En "categoria" SOLO puedes usar estos valores: {categorias_permitidas}.',
            "No inventes categorías nuevas.",
            contexto_ejemplos,
        ]
    )

    # Devolvemos la instancia del agente
    return Agent(model, output_type=DescripcionRopa, system_prompt=system_prompt)

# Llamamos a la función para crear el agente
agent = crear_agente()

# Función para detectar el tipo de archivo de la imagen (mimetype)
def detectar_media_type(image_path: str | Path) -> str:
    media_type, _ = mimetypes.guess_type(str(image_path))
    return media_type or "application/octet-stream"

# Función para enviar los bytes de la imagen al agente y obtener la descripción estructurada
def describir_imagen_bytes(image_bytes: bytes, media_type: str = "image/png") -> DescripcionRopa:
    result = agent.run_sync([BinaryContent(data=image_bytes, media_type=media_type)])
    return result.output

# Función principal que recibe una ruta de imagen, lee sus bytes y llama al análisis del agente
def describir_imagen(image_path: str | Path) -> DescripcionRopa:
    path = Path(image_path)
    if not path.exists() and path.parent == Path("data"):
        path = Path("data/images") / path.name
    return describir_imagen_bytes(path.read_bytes(), detectar_media_type(path))

# Función para ejecutar el script desde la línea de comandos permitiendo pasar una imagen como argumento
def main() -> None:
    parser = argparse.ArgumentParser(description="Describe una imagen de ropa y devuelve JSON.")
    parser.add_argument("image", nargs="?", default="data/images/unnamed.png", help="Ruta de la imagen")
    args = parser.parse_args()

    datos = describir_imagen(args.image)
    print(datos.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
