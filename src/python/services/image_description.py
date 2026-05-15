from __future__ import annotations

import json
import mimetypes
import os
from pathlib import Path

from pydantic_ai import Agent, BinaryContent
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.providers.ollama import OllamaProvider

from core.config import (
    DEFAULT_EXAMPLES_PATH,
    DEFAULT_OLLAMA_BASE_URL,
    DEFAULT_OLLAMA_MODEL,
    IMAGES_DIR,
    PROJECT_ROOT,
)
from models.fashion import DescripcionRopa, categorias_permitidas


def cargar_ejemplos_entrenamiento(path: str | Path | None = None, limite: int = 3) -> str:
    """Carga pocos ejemplos JSONL para guiar al modelo sin fine tuning completo."""
    configured_path = path or os.getenv("TRAINING_EXAMPLES_PATH")
    examples_path = Path(configured_path) if configured_path else DEFAULT_EXAMPLES_PATH
    if not examples_path.is_absolute():
        examples_path = PROJECT_ROOT / examples_path

    if not examples_path.exists():
        return ""

    ejemplos: list[str] = []
    for line in examples_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        output = data.get("output", data)
        ejemplos.append(json.dumps(output, ensure_ascii=False))
        if len(ejemplos) >= limite:
            break

    if not ejemplos:
        return ""

    return (
        "Ejemplos de estilo de respuesta para mantener consistencia:\n"
        + "\n".join(f"- {ejemplo}" for ejemplo in ejemplos)
    )


def crear_agente() -> Agent:
    url = os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL).rstrip("/")
    model_name = os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
    contexto_ejemplos = cargar_ejemplos_entrenamiento()

    model = OllamaModel(
        model_name,
        provider=OllamaProvider(base_url=url),
    )

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

    return Agent(model, output_type=DescripcionRopa, system_prompt=system_prompt)


agent = crear_agente()


def detectar_media_type(image_path: str | Path) -> str:
    media_type, _ = mimetypes.guess_type(str(image_path))
    return media_type or "application/octet-stream"


def describir_imagen_bytes(image_bytes: bytes, media_type: str = "image/png") -> DescripcionRopa:
    result = agent.run_sync([BinaryContent(data=image_bytes, media_type=media_type)])
    return result.output


def describir_imagen(image_path: str | Path) -> DescripcionRopa:
    path = Path(image_path)
    if not path.is_absolute():
        candidates = [Path.cwd() / path, PROJECT_ROOT / path]
        if path.parent == Path("data"):
            candidates.append(IMAGES_DIR / path.name)
        path = next((candidate for candidate in candidates if candidate.exists()), PROJECT_ROOT / path)

    return describir_imagen_bytes(path.read_bytes(), detectar_media_type(path))
