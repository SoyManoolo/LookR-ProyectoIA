import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Cargamos el archivo .env de la raíz del proyecto una sola vez al importar este módulo
load_dotenv(PROJECT_ROOT / ".env")


def project_path(path_value: str | Path) -> Path:
    """Resuelve rutas relativas tomando como base la raíz del proyecto."""
    path = Path(path_value)
    return path if path.is_absolute() else PROJECT_ROOT / path

class Settings:
    # Ollama
    OLLAMA_URL = (
        os.getenv("OLLAMA_BASE_URL") 
        or os.getenv("OLLAMA_URL") 
        or os.getenv("OLLAMA_LOCAL") 
        or "http://localhost:11434/v1"
    )
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e4b")

    # Pinecone
    PINECONE_APIKEY = os.getenv("PINECONE_APIKEY") or os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "buscador")
    PINECONE_REGION = os.getenv("PINECONE_REGION", "us-east-1")
    PINECONE_NAMESPACE = os.getenv("PINECONE_NAMESPACE", "mi-espacio")

    # Datos
    TRAINING_EXAMPLES_PATH = project_path(os.getenv("TRAINING_EXAMPLES_PATH", "data/examples/training_examples.json"))

# Instancia única para usar en todo el proyecto
settings = Settings()
