import os
import asyncio
from agent import process_sense_experience # Reutilizamos tu lógica existente

# Configuración
FOLDER_PATH = "fotos_entrada" # Carpeta donde pondrás las fotos
SUPPORTED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp')

async def process_all_discoveries():
    # 1. Crear la carpeta si no existe
    if not os.path.exists(FOLDER_PATH):
        os.makedirs(FOLDER_PATH)
        print(f"📂 Carpeta '{FOLDER_PATH}' creada. Pon tus fotos ahí y vuelve a ejecutar.")
        return

    # 2. Listar archivos de imagen
    files = [f for f in os.listdir(FOLDER_PATH) if f.lower().endswith(SUPPORTED_EXTENSIONS)]
    
    if not files:
        print(f"Empty 📭: No se encontraron imágenes en '{FOLDER_PATH}'.")
        return

    print(f"🚀 SENSE BATCH: Iniciando procesamiento de {len(files)} descubrimientos...\n")

    for filename in files:
        # Extraemos el nombre sin extensión porque tu función process_sense_experience la busca
        base_name = os.path.splitext(filename)[0]
        full_path = os.path.join(FOLDER_PATH, base_name)
        
        print(f"📸 Procesando: {filename}...")
        try:
            # Llamamos a la función que ya tenemos en agent.py
            await process_sense_experience(full_path)
            print(f"✅ Finalizado: {filename}\n")
            print("-" * 40)
        except Exception as e:
            print(f"❌ Error procesando {filename}: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("✨ SENSE AI - BATCH DISCOVERY MODE")
    print("=" * 60)
    asyncio.run(process_all_discoveries())
