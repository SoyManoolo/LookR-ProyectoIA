import os
import requests
import json
import base64
import re
from ollama import Client

# Configuración de Sense
OLLAMA_HOST = 'http://localhost:11434'
client = Client(host=OLLAMA_HOST)

def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

def extract_json(text):
    """Extrae el JSON de la respuesta de la IA de forma segura."""
    match = re.search(r'\{.*\}', text, re.DOTALL)
    return match.group(0) if match else None

def get_discovery_search(adn, keys):
    try:
        res = requests.get("http://localhost:8000/search", 
                           params={"q": f"{adn} {keys}"}, timeout=5)
        return res.json().get("results", [])
    except:
        return []

def process_sense_experience(image_name):
    # 1. Localizar Imagen
    img_path = next((f"{image_name}{ext}" for ext in ['.jpg', '.png', '.jpeg'] if os.path.exists(f"{image_name}{ext}")), None)
    if not img_path:
        print(f"❌ Error: No se encuentra {image_name}")
        return

    print(f"🔍 [PASO 1] Análisis Visual: Extrayendo ADN de la prenda...")
    img_64 = encode_image(img_path)
    
    # Prompt de Visión: Solo descripción técnica
    vision_prompt = (
        "Describe esta prenda detalladamente para un experto en retail. "
        "Indica material, texturas, tipo de costura, silueta y estilo. "
        "Sé muy específico con los detalles táctiles."
    )
    
    v_res = client.generate(model='qwen3-vl:2b', prompt=vision_prompt, images=[img_64])
    dna_description = v_res['response']
    
    print(f"🧠 [PASO 2] Estructuración: Traduciendo a formato Sense...")
    
    # Prompt de Estructuración: Forzamos valores de texto simple para una UI limpia
    struct_prompt = (
        f"Basado en esta descripción: '{dna_description}', genera un JSON para Sense App Barcelona. "
        "IMPORTANTE: Todos los valores deben ser TEXTO (strings), no listas ni diccionarios. "
        "Estructura: {"
        "\"perfil_estetico\": \"Nombre corto del estilo\", "
        "\"mensaje_usuario\": \"Feedback experto sobre el diseño local\", "
        "\"adn_rag\": \"Descripción sensorial para búsqueda\", "
        "\"query_precision\": \"Keywords bilingües\", "
        "\"sugerencia_carpeta\": \"Nombre creativo\", "
        "\"confidence_score\": 0.95, "
        "\"es_sostenible\": true, "
        "\"ocasion_uso\": \"Lugar o plan específico en Barcelona\""
        "}"
        "Responde ÚNICAMENTE con el objeto JSON."
    )
     
    s_res = client.generate(model='qwen2:7b', prompt=struct_prompt) # Usamos qwen2 para lógica pura
    json_text = extract_json(s_res['response'])
    
    if not json_text:
        print("❌ Error en la estructuración de datos.")
        return

    data = json.loads(json_text)
    
    # --- RESULTADOS ---
    print(f"\n✨ RESULTADO SENSE DISCOVERY")
    print(f"🎨 Estilo: {data['perfil_estetico']} | 📍 {data['ocasion_uso']}")
    print(f"💬 '{data['mensaje_usuario']}'")
    print("-" * 50)
    
    # 3. Búsqueda de Matches
    matches = get_discovery_search(data['adn_rag'], data['query_precision'])
    if matches:
        print(f"🛍️ TOP MATCHES EN BARCELONA:")
        for m in matches[:3]:
            print(f"🔹 {m['name']} | Coincidencia: {m.get('porque_sense', 'Estética local')}")
    else:
        print("🤖 Sense: Guardado en tu wishlist. Buscando en nuevos talleres...")

if __name__ == "__main__":
    process_sense_experience("prenda_test1")
