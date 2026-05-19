import os
from pathlib import Path
from dotenv import load_dotenv

# Cargamos el archivo .env una sola vez al importar este módulo
load_dotenv()

class Settings:
    # Ollama
    OLLAMA_URL = (
        os.getenv("OLLAMA_BASE_URL") 
        or os.getenv("OLLAMA_URL")   # Añadido por consistencia con tu .env
        or os.getenv("OLLAMA_LOCAL") 
        or "http://localhost:11434/v1"
    )
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e4b")

    # Pinecone
    PINECONE_APIKEY = os.getenv("PINECONE_APIKEY")
    PINECONE_INDEX_NAME = "buscador"
    PINECONE_REGION = "us-east-1"

    # Datos
    # Corregido a .jsonl basándome en tu estructura de carpetas
    TRAINING_EXAMPLES_PATH = Path(os.getenv("TRAINING_EXAMPLES_PATH", "data/examples/training_examples.json"))

# Instancia única para usar en todo el proyecto
settings = Settings()