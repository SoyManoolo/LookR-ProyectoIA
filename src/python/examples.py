import json
import os
from pathlib import Path

# Función para cargar unos ejemplos de descripción para que el agente tenga algunos ejemplos, ya que no se hace fine tuning
def cargar_ejemplos_entrenamiento(path: str | Path | None = None, limite: int = 3) -> str:
    """Carga pocos ejemplos JSONL para guiar al modelo sin fine tuning completo."""
    # Obtenemos la ruta del archivo de ejemplos desde variable de entorno o usamos la ruta por defecto
    examples_path = Path(path or os.getenv("TRAINING_EXAMPLES_PATH", "data/examples/training_examples.jsonl"))
    # En caso de que el path no exista devolvemos un string vacio
    if not examples_path.exists():
        return ""

    # Si el path existe vamos guardando los ejemplos del json en la lista
    ejemplos: list[str] = []
    for line in examples_path.read_text(encoding="utf-8").splitlines():
        # Saltamos líneas vacías
        if not line.strip():
            continue
        # Parseamos cada línea como JSON
        data = json.loads(line)
        # Extraemos el campo 'output' si existe, si no usamos el JSON completo
        output = data.get("output", data)
        # Añadimos el ejemplo formateado como JSON a la lista
        ejemplos.append(json.dumps(output, ensure_ascii=False))
        # Paramos cuando alcanzamos el límite de ejemplos
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
