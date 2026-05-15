from __future__ import annotations

import re
import unicodedata

from models.product import Product, SearchResult
from services.embeddings import cosine_similarity


SEMANTIC_SCORE_WEIGHT = 10.0
DEFAULT_SEMANTIC_THRESHOLD = 0.25


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def filter_matches(value: str | None, candidates: list[str]) -> bool:
    if not value:
        return True

    normalized_value = normalize_text(value)
    return normalized_value in {normalize_text(candidate) for candidate in candidates}


def matches_filters(
    product: Product,
    brand: str | None = None,
    category: str | None = None,
    folder: str | None = None,
) -> bool:
    return (
        filter_matches(brand, [product.marca])
        and filter_matches(category, product.categorias)
        and filter_matches(folder, [product.carpeta])
    )


def search_products(
    products: list[Product],
    brand: str | None = None,
    category: str | None = None,
    folder: str | None = None,
    limit: int = 10,
    query_embedding: list[float] | None = None,
    product_embeddings: dict[str, list[float]] | None = None,
    semantic_threshold: float = DEFAULT_SEMANTIC_THRESHOLD,
) -> list[SearchResult]:
    if query_embedding is None or product_embeddings is None:
        return []

    results: list[SearchResult] = []

    for product in products:
        if not matches_filters(product, brand=brand, category=category, folder=folder):
            continue

        product_embedding = product_embeddings.get(product.id)
        if product_embedding is None:
            continue

        embedding_score = cosine_similarity(query_embedding, product_embedding)
        if embedding_score < semantic_threshold:
            continue

        results.append(
            SearchResult(
                product,
                max(embedding_score, 0.0) * SEMANTIC_SCORE_WEIGHT,
                score_embedding=embedding_score,
            )
        )

    results.sort(key=lambda result: (-result.puntuacion, result.producto.nombre))
    return results[:limit]
