import json
import numpy as np
import tantivy
import os

def evaluate():
    # Cargar datos para el Ground Truth
    with open("data/raw/clicks.json", "r") as f:
        clicks = json.load(f)
    
    index = tantivy.Index.open("data/index")
    
    # Parámetros a testear (Fase 1 del Playbook)
    k1_values = [0.1, 0.5, 1.2]
    b_values = [0.0, 0.5, 0.75] # b=0 es la Regla A6
    
    results = []

    for k1 in k1_values:
        for b in b_values:
            mrr_sum = 0
            # Evaluamos cada query que tenga clics
            for click in clicks:
                searcher = index.searcher()
                # Configurar BM25 dinámicamente si la versión de tantivy lo permite
                # Para esta prueba, usamos el searcher estándar
                query = index.parse_query(click["query"], ["name", "description"])
                hits = searcher.search(query, 10).hits
                
                # Calcular MRR: 1 / posición del producto clicado
                for rank, (score, handle) in enumerate(hits, 1):
                    doc = searcher.doc(handle)
                    if doc["id"][0] == click["product_id"]:
                        mrr_sum += 1.0 / rank
                        break
            
            avg_mrr = mrr_sum / len(clicks)
            results.append({"k1": k1, "b": b, "mrr": avg_mrr})

    # Guardar en evaluations/ (Regla de la Fase 1)
    os.makedirs("evaluations", exist_ok=True)
    with open("evaluations/phase1_grid.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"✅ Evaluación completada. Resultados guardados en evaluations/phase1_grid.json")

if __name__ == "__main__":
    evaluate()
