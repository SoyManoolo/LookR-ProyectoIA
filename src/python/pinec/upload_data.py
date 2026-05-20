import json
from pathlib import Path

try:
    from .index import crear_index
except ImportError:
    from index import crear_index

# Función para subir datos de prendas al índice
def subir_datos(path, ns):
    """Carga registros de prendas desde un archivo JSON al índice de Pinecone.
    
    Args:
        path: Ruta del archivo JSON con los registros de prendas
        ns: Namespace (espacio de nombres) donde se guardarán los registros
    """
    dense_index = crear_index()

    # Abrimos el archivo JSON en modo lectura con codificación UTF-8
    with Path(path).open("r", encoding="utf-8") as f:
        # Parseamos el JSON y cargamos todos los registros en memoria
        ejemplos = json.load(f)

    # Subimos los registros al índice en el namespace especificado
    # Pinecone generará automáticamente los embeddings usando el modelo configurado
    dense_index.upsert_records(namespace=ns, records=ejemplos)
