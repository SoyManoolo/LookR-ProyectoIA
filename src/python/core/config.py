from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

DATA_DIR = PROJECT_ROOT / "data"
CATALOG_DIR = DATA_DIR / "catalog"
EXAMPLES_DIR = DATA_DIR / "examples"
IMAGES_DIR = DATA_DIR / "images"

DEFAULT_PRODUCTS_PATH = CATALOG_DIR / "products.json"
DEFAULT_EMBEDDINGS_CACHE_PATH = CATALOG_DIR / "product_embeddings.json"
DEFAULT_EXAMPLES_PATH = EXAMPLES_DIR / "training_examples.jsonl"
DEFAULT_IMAGE_PATH = IMAGES_DIR / "classic-red-logo-tee.jpg"

DEFAULT_OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
DEFAULT_OLLAMA_API_BASE_URL = DEFAULT_OLLAMA_BASE_URL.removesuffix("/v1")
DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e4b")
DEFAULT_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text-v2-moe:latest")

DEFAULT_PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "buscador")
DEFAULT_PINECONE_NAMESPACE = os.getenv("PINECONE_NAMESPACE", "mi-espacio")
DEFAULT_PINECONE_MODEL = os.getenv("PINECONE_EMBEDDING_MODEL", "llama-text-embed-v2")
DEFAULT_PINECONE_CLOUD = os.getenv("PINECONE_CLOUD", "aws")
DEFAULT_PINECONE_REGION = os.getenv("PINECONE_REGION", "us-east-1")
