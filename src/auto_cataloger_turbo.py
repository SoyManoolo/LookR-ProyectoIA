import os
import json
import base64
import re
from ollama import Client

client = Client(host='http://localhost:11434')

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def generar_slug(texto):
    texto = texto.lower()
    texto = re.sub(r'[^a-z0-9]+', '-', texto)
    return texto.strip('-')

def turbo_process(carpeta_fotos="fotos_inventario"):
    catalogo = []
    fotos = [f for f in os.listdir(carpeta_fotos) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    print(f"⚡ Iniciando Modo Turbo para {len(fotos)} imágenes...")

    for i, foto_name in enumerate(fotos, 1):
        path_original = os.path.join(carpeta_fotos, foto_name)
        try:
            img_64 = encode_image(path_original)
            
            # PASO 1: Visión Cruda (Muy rápido)
            # Solo pedimos palabras clave técnicas, no frases bonitas
            vision_res = client.generate(
                model='qwen3-vl:2b',
                prompt="Identify: garment type, color, material, pattern. Short keywords only.",
                images=[img_64]
            )
            raw_features = vision_res['response']

            # PASO 2: Naming Lógico (Casi instantáneo)
            # Usamos un modelo de texto para darle sentido a lo que vio la visión
            naming_prompt = (
                f"Based on these features: '{raw_features}', create a professional retail name "
                "and category (Womens clothing, Mens clothing, Jewelry, Bags and luggage, Shoes, Home). "
                "Respond ONLY with JSON: {\"name\": \"...\", \"category\": \"...\", \"vibe\": \"...\"}"
            )
            
            # Usamos qwen2 (solo texto) que es mucho más ágil
            text_res = client.generate(model='qwen2:7b', prompt=naming_prompt)
            
            # Limpieza y parsing
            match = re.search(r'\{.*\}', text_res['response'], re.DOTALL)
            data = json.loads(match.group(0)) if match else {"name": "Producto Sense", "category": "Home"}

            # --- RENOMBRADO ---
            slug = generar_slug(data['name'])
            ext = os.path.splitext(foto_name)[1]
            nuevo_nombre = f"{slug}{ext}"
            path_nuevo = os.path.join(carpeta_fotos, nuevo_nombre)

            if not os.path.exists(path_nuevo):
                os.rename(path_original, path_nuevo)

            data.update({
                "id": slug,
                "image_path": nuevo_nombre,
                "description": raw_features, # Guardamos el ADN técnico aquí
                "popularity": 100
            })
            
            catalogo.append(data)
            print(f"🚀 {i}/{len(fotos)} | {data['name']}")

        except Exception as e:
            print(f"⚠️ Error en {foto_name}: {e}")

    # Guardado final
    os.makedirs("data/raw", exist_ok=True)
    with open("data/raw/catalog.json", "w", encoding="utf-8") as f:
        json.dump(catalogo, f, indent=2, ensure_ascii=False)
    
    print("\n✅ ¡Catálogo Turbo completado!")

if __name__ == "__main__":
    turbo_process()
