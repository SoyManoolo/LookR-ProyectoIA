import json
import numpy as np
import tantivy
from sentence_transformers import SentenceTransformer

class SearchEngine:
    def __init__(self):
        # 1. Cargar artefactos
        self.model = SentenceTransformer('intfloat/multilingual-e5-small')
        self.embeddings_db = np.load("data/processed/embeddings.npy")
        self.index = tantivy.Index.open("data/index")
        
        with open("data/raw/catalog.json", "r") as f:
            self.catalog = json.load(f)
            self.catalog_map = {p["id"]: p for p in self.catalog}

    def search(self, query_text, top_k=5):
        # --- CAPA 1: Búsqueda Léxica ---
        searcher = self.index.searcher()
        query_parser = self.index.parse_query(query_text, ["name", "description"])
        lexical_hits = searcher.search(query_parser, 20).hits
        
        lexical_results = {}
        for i, (score, handle) in enumerate(lexical_hits):
            doc = searcher.doc(handle)
            lexical_results[doc["id"][0]] = 1.0 / (i + 1) 

        # --- CAPA 2: Búsqueda Semántica ---
        query_vector = self.model.encode(f"query: {query_text}", normalize_embeddings=True)
        semantic_scores = np.dot(self.embeddings_db, query_vector)
        
        # --- CAPA 3: Fusión y Razonamiento (UX) ---
        final_ranking = []
        for idx, product in enumerate(self.catalog):
            p_id = product["id"]
            s_score = semantic_scores[idx]
            l_score = lexical_results.get(p_id, 0.0)
            
            pop_factor = np.log1p(product.get("popularity", 0)) / 10.0
            combined_score = (s_score * 0.6) + (l_score * 0.4) + (pop_factor * 0.1)
            
            # Lógica de Explicabilidad para el usuario
            if s_score > 0.82:
                razon = f"Match total con tu estética {product.get('vibe', 'actual')}"
            elif l_score > 0.5:
                razon = "Coincidencia técnica exacta con tu búsqueda"
            else:
                razon = "Seleccionado por tendencia y relevancia local"
            
            final_ranking.append({
                "id": p_id,
                "name": product["name"],
                "score": round(combined_score, 4),
                "porque_sense": razon,
                "popularity": product["popularity"]
            })

        final_ranking.sort(key=lambda x: x["score"], reverse=True)
        return final_ranking[:top_k]

if __name__ == "__main__":
    # Instanciamos el motor
    engine = SearchEngine()
    import sys
    
    # Tomamos la query de la terminal o usamos una por defecto
    query = sys.argv[1] if len(sys.argv) > 1 else "ropa de abrigo"
    
    # Ejecutamos la búsqueda
    results = engine.search(query)
    
    print(f"\n🚀 RESULTADOS DEL MOTOR HÍBRIDO SENSE")
    print(f"Query analizada: '{query}'")
    print("="*50)
    
    for res in results:
        # Imprimimos el Score, el Nombre y la EXPLICACIÓN de la IA
        print(f"[{res['score']}] {res['name']}")
        print(f"👉 Razonamiento: {res['porque_sense']}")
        print(f"📈 Popularidad: {res['popularity']}")
        print("-" * 50)
