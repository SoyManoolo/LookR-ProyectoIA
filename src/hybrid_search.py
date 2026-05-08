import numpy as np
import tantivy
from sentence_transformers import SentenceTransformer

# Cargamos el modelo y los artefactos (Regla A2 y A5)
model = SentenceTransformer('intfloat/multilingual-e5-small')
embeddings_db = np.load("data/processed/embeddings.npy")
index = tantivy.Index.open("data/index")

def search(query_text):
    # 1. Búsqueda Léxica (Tantivy)
    searcher = index.searcher()
    # Aplicamos Regla A6 (b=0) de forma implícita en la recuperación
    query_lexical = index.parse_query(query_text, ["name", "description"])
    lexical_hits = searcher.search(query_lexical, 10).hits
    
    # 2. Búsqueda Semántica (NumPy)
    query_vector = model.encode(f"query: {query_text}", normalize_embeddings=True)
    # Similitud de coseno (Regla A2)
    semantic_scores = np.dot(embeddings_db, query_vector)
    
    print(f"\n--- Resultados Híbridos para: '{query_text}' ---")
    
    # Por ahora, mostramos la potencia semántica
    best_semantic_idx = np.argmax(semantic_scores)
    doc = searcher.doc(lexical_hits[0][1]) if lexical_hits else None
    
    # Si la búsqueda léxica falla, la semántica te salva
    if semantic_scores[best_semantic_idx] > 0.8:
        from json import load
        with open("data/raw/catalog.json") as f:
            cat = load(f)
            prod = cat[best_semantic_idx]
            print(f"✨ Recomendación semántica: {prod['name']} (Score: {semantic_scores[best_semantic_idx]:.4f})")

if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "prenda de abrigo"
    search(q)
