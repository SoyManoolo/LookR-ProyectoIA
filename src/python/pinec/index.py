import os
from pathlib import Path

from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

def _get_pc():
    load_dotenv(Path(__file__).parent.parent.parent.parent / "data" / ".env")
    return Pinecone(api_key=os.getenv("PINECONE_APIKEY"))


def crear_index():
    """Crea o accede al índice multimodal de Pinecone (vectores CLIP 512d)."""
    pc = _get_pc()
    index_name = "buscador-multimodal"
    if not pc.has_index(index_name):
        pc.create_index(
            name=index_name, dimension=512, metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
    return pc.Index(index_name)


def crear_index_semantico():
    """Crea o accede al índice semántico de Pinecone (768d, multilingual)."""
    pc = _get_pc()
    index_name = "buscador-semantico"
    if not pc.has_index(index_name):
        pc.create_index(
            name=index_name, dimension=768, metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
    return pc.Index(index_name)
