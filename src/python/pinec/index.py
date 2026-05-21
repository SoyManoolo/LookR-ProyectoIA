from pinecone import Pinecone, ServerlessSpec
from config import settings

def _get_pc():
    """Obtiene el cliente de Pinecone usando la configuración centralizada."""
    if not settings.PINECONE_APIKEY:
        raise RuntimeError("Falta PINECONE_APIKEY en la configuración.")
    return Pinecone(api_key=settings.PINECONE_APIKEY)

def crear_index():
    """Crea o accede al índice multimodal de Pinecone (vectores CLIP 512d)."""
    pc = _get_pc()
    # Usamos el nombre base de config.py para mantener la consistencia
    index_name = f"{settings.PINECONE_INDEX_NAME}-multimodal"
    
    if not pc.has_index(index_name):
        pc.create_index(
            name=index_name, 
            dimension=512,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region=settings.PINECONE_REGION),
        )
    return pc.Index(index_name)

def crear_index_semantico():
    """Crea o accede al índice semántico de Pinecone (768d, multilingual)."""
    pc = _get_pc()
    index_name = f"{settings.PINECONE_INDEX_NAME}-semantico"
    
    if not pc.has_index(index_name):
        pc.create_index(
            name=index_name, 
            dimension=768,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region=settings.PINECONE_REGION),
        )
    return pc.Index(index_name)