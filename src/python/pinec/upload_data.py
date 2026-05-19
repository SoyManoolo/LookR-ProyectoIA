import json
from index import crear_index

# Obtenemos el índice de Pinecone al cargar este módulo
dense_index = crear_index()

# Función para subir datos de prendas al índice
def subir_datos(path, ns):
    """Carga registros de prendas desde un archivo JSON al índice de Pinecone.
    
    Args:
        path: Ruta del archivo JSON con los registros de prendas
        ns: Namespace (espacio de nombres) donde se guardarán los registros
    """
    # Abrimos el archivo JSON en modo lectura con codificación UTF-8
    with open(path, "r", encoding="utf-8") as f:
        # Parseamos el JSON y cargamos todos los registros en memoria
        ejemplos = json.load(f)

    # Subimos los registros al índice en el namespace especificado
    # Pinecone generará automáticamente los embeddings usando el modelo configurado
    dense_index.upsert_records(namespace=ns, records=ejemplos)