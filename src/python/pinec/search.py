import argparse

from index import crear_index

# Obtenemos el índice de Pinecone al cargar este módulo
dense_index = crear_index()

# Función para hacer búsquedas semánticas en el índice
def search(query):
    """Busca registros en Pinecone usando búsqueda semántica por texto.
    
    Args:
        query: Texto de búsqueda (p.ej. 'rojo', 'camisa elegante')
        
    Returns:
        Lista de tuplas con (id, score, nombre, descripción) de los resultados
    """
    # Ejecutamos la búsqueda en el índice usando el texto como query
    results = dense_index.search(
        # Especificamos el namespace donde están nuestros registros
        namespace="mi-espacio",
        # Solicitamos los 5 resultados más relevantes
        top_k=5,
        # Pasamos el texto de búsqueda que será embebido automáticamente
        inputs={"text": query}
    )

    # Procesamos los resultados para extraer información útil
    formateados = []
    # Iteramos sobre cada resultado (hit) encontrado
    for hit in results['result']['hits']:
        # Extraemos el nombre de la prenda (N/A si no existe el campo)
        nombre = hit['fields'].get('nombre', 'N/A')
        # Extraemos la descripción de la prenda (N/A si no existe el campo)
        desc = hit['fields'].get('descripcion', 'N/A')
        # Creamos una tupla con información relevante: id, score de similitud, nombre, descripción
        formateados.append((hit['id'], hit['score'], nombre, desc))
    # Retornamos la lista formateada de resultados
    return formateados

# Función principal para ejecutar búsquedas desde línea de comandos
def main():
    """Interfaz de línea de comandos para hacer búsquedas en Pinecone."""
    # Creamos el parser de argumentos de línea de comandos
    parser = argparse.ArgumentParser()
    # Añadimos el argumento posicional 'query' para el texto de búsqueda
    parser.add_argument("query", help="Texto de búsqueda")
    # Parseamos los argumentos proporcionados
    args = parser.parse_args()

    # Ejecutamos la búsqueda con el texto proporcionado
    resultados = search(args.query)
    # Mostramos cada resultado en pantalla
    for item in resultados:
        print(item)

# Condición para ejecutar solo cuando el script se lanza directamente
if __name__ == "__main__":
    main()