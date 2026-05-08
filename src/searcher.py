import tantivy
import sys

def buscar(termino):
    index = tantivy.Index.open("data/index")
    searcher = index.searcher()
    
    # Regla A6: BM25 optimizado para retail (b=0)
    # (Nota: Si tu versión no permite set_bm25_params, usa el default)
    
    query = index.parse_query(termino, ["name", "description"])
    results = searcher.search(query, 5)
    
    print(f"\n RESULTADOS ÚNICOS PARA: '{termino}'")
    print("="*45)
    
    # Usamos un set para evitar mostrar el mismo ID varias veces
    vistos = set()
    for score, handle in results.hits:
        doc = searcher.doc(handle)
        doc_id = doc['id'][0]
        if doc_id not in vistos:
            print(f"[{score:.4f}] {doc['name'][0]} (ID: {doc_id})")
            vistos.add(doc_id)

if __name__ == "__main__":
    query_input = sys.argv[1] if len(sys.argv) > 1 else "sweater"
    buscar(query_input)
