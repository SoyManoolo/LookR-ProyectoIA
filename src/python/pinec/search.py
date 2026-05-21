import argparse
import json
import logging
import os
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

# Intentamos importaciones relativas o absolutas
try:
    from .index import crear_index, crear_index_semantico
    from .embeddings import embed_texto, embed_imagen, embed_descripcion, embed_combinado
except ImportError:
    from index import crear_index, crear_index_semantico
    from embeddings import embed_texto, embed_imagen, embed_descripcion, embed_combinado

# Inicialización de índices
dense_index = crear_index()
semantic_index = crear_index_semantico()
_NAMESPACE = "mi-espacio"

# Pesos de la búsqueda híbrida
_W_VISUAL = 0.20
_W_SEMANTIC = 0.50
_W_KEYWORD = 0.30

_translate_cache: dict[str, str] = {}
_expand_cache: dict[str, str] = {}

def _get_ollama_url() -> str:
    return (os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434").rstrip("/v1").rstrip("/")

def _llamar_ollama(prompt: str, timeout: int = 10) -> str | None:
    """Llama a Ollama usando urllib para evitar dependencias extra."""
    model = os.getenv("OLLAMA_MODEL", "gemma3:12b")
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
    try:
        req = urllib.request.Request(f"{_get_ollama_url()}/api/generate", data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())["response"].strip()
    except Exception as e:
        logger.warning(f"Ollama no disponible: {e}")
        return None

def _keyword_score(query: str, meta: dict) -> float:
    """Calcula coincidencia de palabras clave exactas."""
    import unicodedata
    def normalizar(t: str):
        return set(unicodedata.normalize("NFKD", t.lower()).encode("ascii", "ignore").decode().split())
    q_words = normalizar(query)
    i_words = normalizar(meta.get("descripcion", "")) | normalizar(" ".join(meta.get("categoria", [])))
    return len(q_words & i_words) / max(len(q_words), 1)

def _query_pinecone(index, vector, top_k: int) -> dict:
    return index.query(namespace=_NAMESPACE, vector=vector, top_k=top_k, include_metadata=True)

def search(query: str, por_imagen: bool = False, top_k: int = 6) -> list[tuple]:
    """Búsqueda híbrida real (Visual + Semántica + Keywords)."""
    if por_imagen:
        results = _query_pinecone(dense_index, embed_imagen(query), top_k)
        return _formatear_resultados(results["matches"])

    # Intentamos traducir/expandir con Ollama para mejorar CLIP (que es inglés)
    query_en = _llamar_ollama(f"Translate to English fashion terms: {query}") or query

    # Obtenemos resultados de ambos índices
    v_res = _query_pinecone(dense_index, embed_texto(query_en), top_k * 2)
    s_res = _query_pinecone(semantic_index, embed_descripcion(query), top_k * 2)

    # Fusionar y puntuar (RRF o suma ponderada)
    scores = {}
    for m in v_res["matches"]:
        scores[m["id"]] = {"meta": m["metadata"], "v": m["score"], "s": 0.0}
    for m in s_res["matches"]:
        if m["id"] in scores: scores[m["id"]]["s"] = m["score"]
        else: scores[m["id"]] = {"meta": m["metadata"], "v": 0.0, "s": m["score"]}

    ranked = sorted(scores.items(), key=lambda x: (_W_VISUAL*x[1]["v"] + _W_SEMANTIC*x[1]["s"] + _W_KEYWORD*_keyword_score(query, x[1]["meta"])), reverse=True)[:top_k]
    
    return [(rid, round(_W_VISUAL*v["v"] + _W_SEMANTIC*v["s"], 4), v["meta"].get("nombre", "N/A"), v["meta"].get("descripcion", "N/A"), v["meta"].get("imagen", ""), v["meta"].get("categoria", []), v["meta"].get("estilo", "")) for rid, v in ranked]

def _formatear_resultados(matches):
    return [(m["id"], m["score"], m["metadata"].get("nombre", "N/A"), m["metadata"].get("descripcion", "N/A"), m["metadata"].get("imagen", ""), m["metadata"].get("categoria", []), m["metadata"].get("estilo", "")) for m in matches]

def search_combinado(imagen_path: str, texto: str, top_k: int = 6, alpha: float = 0.7) -> list[tuple]:
    vector = embed_combinado(imagen_path, texto, alpha=alpha)
    results = _query_pinecone(dense_index, vector, top_k)
    return _formatear_resultados(results["matches"])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    args = parser.parse_args()
    for res in search(args.query): print(res)