import argparse
import sys
import os

# Añadimos el directorio padre al path para poder importar módulos de src/python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

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


def search_by_image(image_path):
    """Busca prendas similares a partir de una imagen.
    
    Describe la imagen usando el agente de IA y luego busca en Pinecone
    usando la descripción generada como query de texto.
    
    Args:
        image_path: Ruta de la imagen a analizar
        
    Returns:
        Tupla con (descripcion_generada, lista de resultados)
    """
    from agent import crear_agente
    from image_utils import describir_imagen

    # Creamos el agente y obtenemos la descripción de la imagen
    agent = crear_agente()
    datos = describir_imagen(agent, image_path)

    # Usamos la descripción generada como query de texto para buscar en Pinecone
    resultados = search(datos.descripcion)
    return datos.descripcion, resultados


# Función principal para ejecutar búsquedas desde línea de comandos
def main():
    """Interfaz de línea de comandos para hacer búsquedas en Pinecone por texto o imagen."""
    # Creamos el parser de argumentos de línea de comandos
    parser = argparse.ArgumentParser(description="Búsqueda semántica en Pinecone por texto o imagen.")
    # Grupo mutuamente excluyente: texto O imagen
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--texto", "-t", help="Texto de búsqueda (p.ej. 'camisa elegante roja')")
    group.add_argument("--imagen", "-i", help="Ruta de la imagen a buscar (p.ej. 'data/images/foto.jpg')")
    # Parseamos los argumentos proporcionados
    args = parser.parse_args()

    if args.imagen:
        # Búsqueda por imagen: describimos la imagen y luego buscamos por el texto generado
        print(f"Analizando imagen: {args.imagen}")
        descripcion, resultados = search_by_image(args.imagen)
        print(f"Descripción generada: {descripcion}\n")
    else:
        # Búsqueda por texto directa
        resultados = search(args.texto)

    # Mostramos cada resultado en pantalla
    for item in resultados:
        print(item)

# Condición para ejecutar solo cuando el script se lanza directamente
if __name__ == "__main__":
    main()