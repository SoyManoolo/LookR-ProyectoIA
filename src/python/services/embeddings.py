from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any
from urllib import error, request

from core.config import (
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_EMBEDDINGS_CACHE_PATH,
    DEFAULT_OLLAMA_API_BASE_URL,
    DEFAULT_PINECONE_CLOUD,
    DEFAULT_PINECONE_INDEX_NAME,
    DEFAULT_PINECONE_MODEL,
    DEFAULT_PINECONE_NAMESPACE,
    DEFAULT_PINECONE_REGION,
)
from models.product import Product, product_embedding_text


PINECONE_FIELD_MAP = {"text": "descripcion"}


class EmbeddingError(RuntimeError):
    pass


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0

    dot_product = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0

    return dot_product / (left_norm * right_norm)


def _ollama_base_url() -> str:
    base_url = os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_API_BASE_URL).rstrip("/")
    return base_url[:-3] if base_url.endswith("/v1") else base_url


def _post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    http_request = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(http_request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.URLError as exc:
        raise EmbeddingError(f"No se pudo conectar con Ollama en {url}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise EmbeddingError(f"Ollama devolvio una respuesta no valida desde {url}") from exc


def _extract_embeddings(response_data: dict[str, Any]) -> list[list[float]]:
    embeddings = response_data.get("embeddings")
    if isinstance(embeddings, list) and embeddings:
        return [[float(value) for value in embedding] for embedding in embeddings]

    embedding = response_data.get("embedding")
    if isinstance(embedding, list) and embedding:
        return [[float(value) for value in embedding]]

    raise EmbeddingError("Ollama no devolvio embeddings en la respuesta.")


def embed_texts(texts: list[str], model: str = DEFAULT_EMBEDDING_MODEL) -> list[list[float]]:
    if not texts:
        return []

    base_url = _ollama_base_url()
    payload = {"model": model, "input": texts}

    try:
        embeddings = _extract_embeddings(_post_json(f"{base_url}/api/embed", payload))
    except EmbeddingError:
        fallback_embeddings = []
        for text in texts:
            data = _post_json(f"{base_url}/api/embeddings", {"model": model, "prompt": text})
            fallback_embeddings.extend(_extract_embeddings(data))
        embeddings = fallback_embeddings

    if len(embeddings) != len(texts):
        raise EmbeddingError(
            f"Ollama devolvio {len(embeddings)} embeddings para {len(texts)} textos."
        )

    return embeddings


def load_embedding_cache(path: str | Path, model: str = DEFAULT_EMBEDDING_MODEL) -> dict[str, Any]:
    cache_path = Path(path)
    if not cache_path.exists():
        return {}

    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EmbeddingError(f"La cache de embeddings no es JSON valido: {cache_path}") from exc

    if data.get("model") != model:
        return {}

    records = data.get("records", {})
    return records if isinstance(records, dict) else {}


def save_embedding_cache(
    path: str | Path,
    model: str,
    records: dict[str, dict[str, Any]],
) -> None:
    cache_path = Path(path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps({"model": model, "records": records}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_or_create_product_embeddings(
    products: list[Product],
    cache_path: str | Path = DEFAULT_EMBEDDINGS_CACHE_PATH,
    model: str = DEFAULT_EMBEDDING_MODEL,
    refresh: bool = False,
) -> dict[str, list[float]]:
    cached_products = {} if refresh else load_embedding_cache(cache_path, model)
    records: dict[str, dict[str, Any]] = {}
    products_to_embed: list[tuple[Product, str]] = []

    for product in products:
        embedding_text = product_embedding_text(product)
        cached_product = cached_products.get(product.id)
        if (
            isinstance(cached_product, dict)
            and cached_product.get("text") == embedding_text
            and isinstance(cached_product.get("embedding"), list)
        ):
            records[product.id] = cached_product
        else:
            products_to_embed.append((product, embedding_text))

    if products_to_embed:
        embedding_texts = [embedding_text for _, embedding_text in products_to_embed]
        embeddings = embed_texts(embedding_texts, model=model)
        for (product, embedding_text), embedding in zip(products_to_embed, embeddings):
            records[product.id] = {"text": embedding_text, "embedding": embedding}

        save_embedding_cache(cache_path, model, records)

    return {
        product_id: [float(value) for value in record["embedding"]]
        for product_id, record in records.items()
    }


def _get_pinecone_client() -> Any:
    api_key = os.getenv("PINECONE_APIKEY") or os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise EmbeddingError("Falta PINECONE_APIKEY o PINECONE_API_KEY en el entorno.")

    try:
        from pinecone import Pinecone
    except ImportError as exc:
        raise EmbeddingError("Instala pinecone para usar la busqueda con Pinecone.") from exc

    return Pinecone(api_key=api_key)


def get_or_create_pinecone_index(index_name: str = DEFAULT_PINECONE_INDEX_NAME) -> Any:
    pc = _get_pinecone_client()
    if not pc.has_index(index_name):
        pc.create_index_for_model(
            name=index_name,
            cloud=os.getenv("PINECONE_CLOUD", DEFAULT_PINECONE_CLOUD),
            region=os.getenv("PINECONE_REGION", DEFAULT_PINECONE_REGION),
            embed={
                "model": DEFAULT_PINECONE_MODEL,
                "field_map": PINECONE_FIELD_MAP,
            },
        )
    return pc.Index(index_name)


def product_to_pinecone_record(product: Product) -> dict[str, Any]:
    return {
        "id": product.id,
        "nombre": product.nombre,
        "descripcion": product.descripcion,
        "marca": product.marca,
        "categorias": product.categorias,
        "estilo": product.estilo,
        "carpeta": product.carpeta,
        "imagen": product.imagen,
    }


def upsert_products_to_pinecone(
    products: list[Product],
    index_name: str = DEFAULT_PINECONE_INDEX_NAME,
    namespace: str = DEFAULT_PINECONE_NAMESPACE,
) -> Any:
    index = get_or_create_pinecone_index(index_name)
    records = [product_to_pinecone_record(product) for product in products]
    if records:
        index.upsert_records(namespace=namespace, records=records)
    return index.describe_index_stats()


def search_pinecone(
    query: str,
    index_name: str = DEFAULT_PINECONE_INDEX_NAME,
    namespace: str = DEFAULT_PINECONE_NAMESPACE,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    index = get_or_create_pinecone_index(index_name)
    results = index.search(namespace=namespace, top_k=top_k, inputs={"text": query})
    return list(results.get("result", {}).get("hits", []))
