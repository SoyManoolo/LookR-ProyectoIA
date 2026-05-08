import os
import json
import base64
import re
from ollama import Client

def encode_image(image_path):
    """Convierte la imagen a base64 para enviarla a Ollama."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def limpiar_respuesta_json(raw_response):
    """Extrae el contenido entre llaves para obtener un JSON válido."""
    raw_response = raw_response.strip()
    start = raw_response.find('{')
    end = raw_response.rfind('}')
    if start != -1 and end != -1:
        return raw_response[start:end+1]
    return raw_response

def generar_slug(texto):
    """Convierte el nombre en un ID limpio para archivos: 'Vestido Seda' -> 'vestido-seda'"""
    texto = texto.lower()
    # Eliminar acentos y caracteres especiales
    texto = re.sub(r'[^a-z0-9]+', '-', texto)
    return texto.strip('-')

def generar_catalogo_desde_imagenes(carpeta_fotos="fotos_inventario"):
    try:
        # Asegúrate de que Ollama esté corriendo
        client = Client(host='http://localhost:11434')
    except Exception as e:
        print(f"❌ Error de conexión con Ollama: {e}")
        return

    catalogo = []
    
    if not os.path.exists(carpeta_fotos):
        os.makedirs(carpeta_fotos)
        print(f"⚠️ Carpeta '{carpeta_fotos}' creada. Añade tus fotos ahí.")
        return

    valid_exts = ('.jpg', '.jpeg', '.png', '.webp')
    fotos = [f for f in os.listdir(carpeta_fotos) if f.lower().endswith(valid_exts)]
    
    if not fotos:
        print(f"⚠️ No hay imágenes en '{carpeta_fotos}'.")
        return

    print(f"🚀 Sense está analizando y renombrando {len(fotos)} prendas...")

    for i, foto_name in enumerate(fotos, 1):
        path_original = os.path.join(carpeta_fotos, foto_name)
        try:
            img_base64 = encode_image(path_original)
            
            # PROMPT OPTIMIZADO: Obliga a la IA a ser descriptiva (Tipo + Característica)
            prompt = (
                "Analiza esta prenda para un catálogo de lujo en Barcelona. "
                "Genera un nombre que sea DESCRIPTIVO (Tipo de prenda + Característica). "
                "NO uses nombres abstractos o artísticos. "
                "EJEMPLO CORRECTO: 'Vestido Seda Floral', 'Chaqueta Cuero Negra'. "
                "Responde ÚNICAMENTE con un JSON puro con este formato: "
                "{"
                "\"name\": \"Nombre descriptivo comercial\", "
                "\"category\": \"Una de estas: Womens clothing, Mens clothing, Jewelry, Bags and luggage, Shoes, Home\", "
                "\"description\": \"Descripción técnica del ADN de la prenda (materiales, corte)\", "
                "\"vibe\": \"Estética urbana (ej: Born Minimalist, Eixample Elegance)\""
                "}"
            )
            
            response = client.generate(model='qwen3-vl:2b', prompt=prompt, images=[img_base64])
            json_text = limpiar_respuesta_json(response['response'])
            data = json.loads(json_text)
            
            # --- LÓGICA DE AUTO-NAMING Y RENOMBRADO ---
            # Creamos un nombre de archivo amigable a partir del nombre descriptivo de la IA
            slug = generar_slug(data.get("name", f"producto-{i}"))
            ext = os.path.splitext(foto_name)[1]
            nuevo_nombre_archivo = f"{slug}{ext}"
            path_nuevo = os.path.join(carpeta_fotos, nuevo_nombre_archivo)

            # Si el nombre nuevo ya existe, le añadimos el índice para evitar conflictos
            if os.path.exists(path_nuevo) and path_original != path_nuevo:
                nuevo_nombre_archivo = f"{slug}-{i}{ext}"
                path_nuevo = os.path.join(carpeta_fotos, nuevo_nombre_archivo)

            # Renombrar archivo físico
            os.rename(path_original, path_nuevo)

            # Preparar datos para el catálogo
            data["id"] = slug
            data["image_path"] = nuevo_nombre_archivo
            data["popularity"] = 100
            
            catalogo.append(data)
            print(f"✅ [{i}/{len(fotos)}] {data['name']} -> {nuevo_nombre_archivo}")

        except Exception as e:
            print(f"❌ Error procesando {foto_name}: {e}")

    # Guardar el JSON final en la carpeta de datos
    os.makedirs("data/raw", exist_ok=True)
    with open("data/raw/catalog.json", "w", encoding="utf-8") as f:
        json.dump(catalogo, f, indent=2, ensure_ascii=False)
    
    print(f"\n✨ Proceso terminado. Catálogo actualizado en 'data/raw/catalog.json'")

if __name__ == "__main__":
    generar_catalogo_desde_imagenes()
