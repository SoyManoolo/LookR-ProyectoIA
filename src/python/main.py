from __future__ import annotations

import argparse
import logging
from pathlib import Path

from dotenv import load_dotenv

from image_utils import describir_imagen
from agent import crear_agente
from pinec.upload_data import subir_prenda

# Configuramos el logging para mostrar mensajes informativos
logging.basicConfig(level=logging.INFO)
# Cargamos las variables de entorno del archivo .env
load_dotenv(Path(__file__).parent.parent.parent / ".env")

# Función principal que ejecuta el script desde la línea de comandos
def main() -> None:
    """Punto de entrada principal del programa que permite pasar una o varias imágenes."""
    # Configuramos el parser de argumentos de línea de comandos
    parser = argparse.ArgumentParser(description="Describe una o varias imágenes de ropa y las sube a Pinecone.")
    
    # Mantenemos nargs="+" de develop para permitir múltiples imágenes
    parser.add_argument("images", nargs="+", help="Ruta(s) de imagen")
    args = parser.parse_args()

    # Inicializamos el agente una sola vez fuera del bucle (esto faltaba en develop)
    agent = crear_agente()

    for ruta in args.images:
        print(f"\n=== Procesando: {ruta} ===")
        try:
            # Llamamos a la función que describe la imagen
            datos = describir_imagen(agent, ruta)
            
            # Mostramos el resultado en formato JSON
            print(datos.model_dump_json(indent=2))
            
            # Subimos los datos a Pinecone como en la versión de develop
            record_id = subir_prenda(datos, ruta)
            print(f"Subido a Pinecone con id: {record_id}")
            
        except Exception as e:
            logging.error(f"Error procesando {ruta}: {e}")


# Condición para ejecutar solo cuando el script se lanza directamente, no cuando se importa
if __name__ == "__main__":
    main()
