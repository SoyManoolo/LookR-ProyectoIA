from pinecone import Pinecone
from dotenv import load_dotenv

from config import settings

# Función para crear o acceder al índice de Pinecone
def crear_index():
    """Crea un nuevo índice en Pinecone o retorna uno existente para búsquedas vectoriales."""

    # Instanciamos el cliente de Pinecone con la API key
    pc = Pinecone(api_key=settings.PINECONE_APIKEY)

    # Definimos el nombre del índice que usaremos
    index_name = "buscador"

    # Comprobamos si el índice ya existe, si no lo creamos
    if not pc.has_index(index_name):
        # Creamos un nuevo índice con embeddings automáticos usando el modelo llama-text-embed-v2
        pc.create_index_for_model(
            name=index_name,
            # Configuración de cloud: AWS en región us-east-1
            cloud="aws",
            region="us-east-1",
            # Configuración de embeddings: modelo y mapeo de campos
            embed={
                # Modelo de embedding que generará automáticamente los vectores
                "model": "llama-text-embed-v2",
                # Mapeamos el campo 'descripcion' para que sea embebido
                "field_map": {"text": "descripcion"}
            }
        )

    # Obtenemos una referencia al índice (nuevo o existente) para operaciones futuras
    dense_index = pc.Index(index_name)

    # Retornamos el objeto índice para usarlo en otras funciones
    return dense_index