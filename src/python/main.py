from __future__ import annotations

import argparse
import logging

from image_utils import describir_imagen
from agent import crear_agente

# Configuramos el logging para mostrar mensajes informativos
logging.basicConfig(level=logging.INFO)

# Función principal que ejecuta el script desde la línea de comandos
def main() -> None:
    """Punto de entrada principal del programa que permite pasar una imagen como argumento."""
    # Creamos una instancia del agente con toda la configuración necesaria
    agent = crear_agente()
    # Configuramos el parser de argumentos de línea de comandos
    parser = argparse.ArgumentParser(description="Describe una imagen de ropa y devuelve JSON.")
    # Añadimos el argumento posicional 'image' con valor por defecto
    parser.add_argument("image", nargs="?", default="data/images/eleganza-beige-satin-gown.png", help="Ruta de la imagen")
    # Parseamos los argumentos pasados al script
    args = parser.parse_args()

    # Llamamos a la función que describe la imagen con la ruta proporcionada
    datos = describir_imagen(agent, args.image)
    # Mostramos el resultado en formato JSON indentado para mejor legibilidad
    print(datos.model_dump_json(indent=2))


# Condición para ejecutar solo cuando el script se lanza directamente, no cuando se importa
if __name__ == "__main__":
    main()
