import argparse
import json
import logging
import os
import urllib.request

logger = logging.getLogger(__name__)

try:
    from .index import crear_index, crear_index_semantico
    from .embeddings import embed_texto, embed_imagen, embed_descripcion, embed_combinado
except ImportError:
    from index import crear_index, crear_index_semantico
    from embeddings import embed_texto, embed_imagen, embed_descripcion, embed_combinado

dense_index = crear_index()
semantic_index = crear_index_semantico()

_NAMESPACE = "mi-espacio"


def _imagen_from_meta(meta: dict) -> str:
    """Devuelve la ruta de imagen del metadata, sea 'imagen' (catálogo) o 'imagen_path' (armario)."""
    return meta.get("imagen") or meta.get("imagen_path") or ""
# Pesos del score final: visual (CLIP) + semántico (multilingual) + keyword (metadatos)
_W_VISUAL = 0.20
_W_SEMANTIC = 0.50
_W_KEYWORD = 0.30


# Caché manual: solo almacena traducciones exitosas; los fallos se reintentarán
_translate_cache: dict[str, str] = {}
_expand_cache: dict[str, str] = {}


def _get_ollama_url() -> str:
    return (
        os.getenv("OLLAMA_BASE_URL") or os.getenv("OLLAMA_LOCAL") or "http://localhost:11434"
    ).rstrip("/v1").rstrip("/")


def _llamar_ollama(prompt: str, timeout: int = 10) -> str | None:
    """Llama a Ollama. Devuelve None si no está disponible."""
    model = os.getenv("OLLAMA_MODEL", "gemma3:12b")
    keep_alive = os.getenv("OLLAMA_KEEP_ALIVE", "5m")
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False, "keep_alive": keep_alive}).encode()
    try:
        req = urllib.request.Request(
            f"{_get_ollama_url()}/api/generate", data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())["response"].strip()
    except Exception as e:
        logger.warning("Ollama no disponible: %s", e)
        return None


def _traducir_al_ingles(texto: str) -> str | None:
    """Traduce al inglés para CLIP. Devuelve None si Ollama no está disponible."""
    if texto in _translate_cache:
        return _translate_cache[texto]
    result = _llamar_ollama(
        f"Translate this fashion search query to English. Reply with ONLY the translation, no explanation:\n{texto}"
    )
    if result:
        _translate_cache[texto] = result
    return result


def _keyword_score(query: str, meta: dict) -> float:
    """Overlap entre palabras de la query y metadatos del item (desc + categorías + estilo)."""
    import unicodedata
    def normalizar(t: str) -> set[str]:
        t = unicodedata.normalize("NFKD", t.lower()).encode("ascii", "ignore").decode()
        return set(t.split())

    query_words = normalizar(query)
    item_words = (
        normalizar(meta.get("descripcion", ""))
        | normalizar(" ".join(meta.get("categoria", [])))
        | normalizar(meta.get("estilo", ""))
    )
    coincidencias = query_words & item_words
    return len(coincidencias) / max(len(query_words), 1)


def _es_contextual(query: str) -> bool:
    """Detecta si la query es contextual (ocasión, evento, temporada)."""
    palabras_clave = [
        "para", "evento", "boda", "fiesta", "trabajo", "playa", "verano",
        "invierno", "otoño", "primavera", "noche", "día", "casual", "look",
        "outfit", "ocasión", "reunión", "cena", "cóctel",
    ]
    q = query.lower()
    return any(p in q for p in palabras_clave)


def _expandir_query(query: str) -> str | None:
    """Expande queries contextuales con Ollama. Devuelve None si no está disponible."""
    if query in _expand_cache:
        return _expand_cache[query]
    result = _llamar_ollama(
        f"A user is searching for fashion items with this query: '{query}'\n"
        "Generate a short English description (max 15 words) of the ideal clothing item "
        "that would match this query. Only output the description, nothing else.",
        timeout=12,
    )
    if result:
        _expand_cache[query] = result
    return result


def _query_pinecone(index, vector, top_k: int) -> dict:
    return index.query(
        namespace=_NAMESPACE, vector=vector,
        top_k=top_k, include_metadata=True,
    )


def search(query: str, por_imagen: bool = False, top_k: int = 6) -> list[tuple]:
    """Búsqueda híbrida: combina similitud visual (CLIP) y semántica (multilingual).

    Para imágenes: solo índice visual.
    Para texto: índice visual + índice semántico, scores combinados.
    """
    if por_imagen:
        results = _query_pinecone(dense_index, embed_imagen(query), top_k)
        return _formatear(results["matches"])

    # Expansión contextual si la query lo requiere
    if _es_contextual(query):
        query_en = _expandir_query(query)
    else:
        query_en = _traducir_al_ingles(query)

    # Si Ollama no está disponible, búsqueda solo semántica (multilingual entiende español)
    if query_en is None:
        logger.info("Ollama no disponible — búsqueda semántica pura para: %s", query)
        results = _query_pinecone(semantic_index, embed_descripcion(query), top_k)
        return _formatear(results["matches"])

    # Búsqueda visual con CLIP (texto en inglés)
    visual_results = _query_pinecone(dense_index, embed_texto(query_en), top_k * 2)
    # Búsqueda semántica con modelo multilingual (texto original en español)
    semantic_results = _query_pinecone(semantic_index, embed_descripcion(query), top_k * 2)

    # Combinar scores normalizados por ID
    scores: dict[str, dict] = {}
    for m in visual_results["matches"]:
        scores[m["id"]] = {"meta": m["metadata"], "visual": m["score"], "semantic": 0.0}
    for m in semantic_results["matches"]:
        if m["id"] in scores:
            scores[m["id"]]["semantic"] = m["score"]
        else:
            scores[m["id"]] = {"meta": m["metadata"], "visual": 0.0, "semantic": m["score"]}

    # Score final ponderado: visual + semántico + keyword
    ranked = sorted(
        scores.items(),
        key=lambda x: (
            _W_VISUAL   * x[1]["visual"]
            + _W_SEMANTIC * x[1]["semantic"]
            + _W_KEYWORD  * _keyword_score(query, x[1]["meta"])
        ),
        reverse=True,
    )[:top_k]

    return [
        (
            rid,
            round(
                _W_VISUAL * v["visual"]
                + _W_SEMANTIC * v["semantic"]
                + _W_KEYWORD * _keyword_score(query, v["meta"]),
                4,
            ),
            v["meta"].get("nombre", "N/A"),
            v["meta"].get("descripcion", "N/A"),
            _imagen_from_meta(v["meta"]),
            v["meta"].get("categoria", []),
            v["meta"].get("estilo", ""),
        )
        for rid, v in ranked
    ]


def _formatear(matches: list) -> list[tuple]:
    return [
        (
            m["id"], m["score"],
            m["metadata"].get("nombre", "N/A"),
            m["metadata"].get("descripcion", "N/A"),
            _imagen_from_meta(m["metadata"]),
            m["metadata"].get("categoria", []),
            m["metadata"].get("estilo", ""),
        )
        for m in matches
    ]


def search_combinado(imagen_path: str, texto: str, top_k: int = 6, alpha: float = 0.7) -> list[tuple]:
    """Búsqueda multimodal: imagen base + modificador de texto en espacio CLIP.

    Traduce el texto al inglés antes de embeddear (CLIP fue entrenado en inglés).
    alpha controla el peso de la imagen vs. el texto (0.7 = 70% imagen, 30% texto).
    """
    texto_en = _traducir_al_ingles(texto) if texto.strip() else None
    vector = embed_combinado(imagen_path, texto_en, alpha=alpha) if texto_en else embed_imagen(imagen_path)
    results = _query_pinecone(dense_index, vector, top_k)
    return _formatear(results["matches"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="Texto de búsqueda o ruta de imagen")
    parser.add_argument("--imagen", action="store_true")
    args = parser.parse_args()
    for item in search(args.query, por_imagen=args.imagen):
        print(item)


if __name__ == "__main__":
    main()
