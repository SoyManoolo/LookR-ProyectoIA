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
load_dotenv(Path(__file__).parent.parent.parent / "data" / ".env")

# Función principal que ejecuta el script desde la línea de comandos
def main() -> None:
    """Punto de entrada principal del programa que permite pasar una imagen como argumento."""
    # Creamos una instancia del agente con toda la configuración necesaria
    agent = crear_agente()
    # Configuramos el parser de argumentos de línea de comandos
    parser = argparse.ArgumentParser(description="Describe una imagen de ropa y devuelve JSON.")
    parser.add_argument("images", nargs="+", help="Ruta(s) de imagen")
    args = parser.parse_args()

    for ruta in args.images:
        print(f"\n=== {ruta} ===")
        datos = describir_imagen(agent, ruta)
        print(datos.model_dump_json(indent=2))
        record_id = subir_prenda(datos, ruta)
        print(f"Subido a Pinecone con id: {record_id}")


# Condición para ejecutar solo cuando el script se lanza directamente, no cuando se importa
if __name__ == "__main__":
    main()
