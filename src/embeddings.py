import numpy as np
from sentence_transformers import SentenceTransformer
import json
import os

def generar_embeddings():
    # REGLA A5: Modelo ultra-ligero para latencia <5ms
    model = SentenceTransformer('intfloat/multilingual-e5-small')
    
    # Cargar catálogo de la Fase 0
    with open("data/raw/catalog.json", "r") as f:
        productos = json.load(f)
    
    # El prefijo 'passage: ' es obligatorio para modelos E5
    textos = [f"passage: {p['name']} {p['description']}" for p in productos]
    
    # Generar vectores (384 dimensiones)
    embeddings = model.encode(textos, normalize_embeddings=True)
    
    # REGLA A10: Guardar como artefacto procesado
    os.makedirs("data/processed", exist_ok=True)
    np.save("data/processed/embeddings.npy", embeddings)
    
    print(f"✅ Fase 2: Matriz de {embeddings.shape} generada.")

if __name__ == "__main__":
    generar_embeddings()
