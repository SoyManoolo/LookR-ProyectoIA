from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

PYTHON_ROOT = Path(__file__).resolve().parents[1]
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from core.config import DEFAULT_EMBEDDINGS_CACHE_PATH, DEFAULT_PRODUCTS_PATH
from repositories.product_catalog import load_products
from search.ranking import DEFAULT_SEMANTIC_THRESHOLD, search_products
from services.embeddings import DEFAULT_EMBEDDING_MODEL, EmbeddingError, embed_texts
from services.embeddings import load_or_create_product_embeddings


def describe_image_as_query(image_path: str | Path) -> dict[str, Any]:
    from services.image_description import describir_imagen

    description = describir_imagen(image_path)
    data = description.model_dump()
    data["query"] = " ".join(
        [
            data.get("descripcion", ""),
            data.get("estilo", ""),
            " ".join(data.get("categoria", [])),
        ]
    ).strip()
    return data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Busca productos con embeddings semanticos.")
    parser.add_argument("query", nargs="?", default="", help="Texto a buscar")
    parser.add_argument("--products", default=str(DEFAULT_PRODUCTS_PATH), help="Ruta del catalogo JSON")
    parser.add_argument("--brand", "--marca", dest="brand", help="Filtrar por marca")
    parser.add_argument("--category", "--categoria", dest="category", help="Filtrar por categoria")
    parser.add_argument("--folder", "--carpeta", dest="folder", help="Filtrar por carpeta")
    parser.add_argument("--image", "--imagen", dest="image", help="Buscar usando una imagen como entrada")
    parser.add_argument("--limit", "--limite", dest="limit", type=int, default=10, help="Maximo de resultados")
    parser.add_argument(
        "--embedding-model",
        default=os.getenv("OLLAMA_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL),
        help="Modelo de embeddings de Ollama",
    )
    parser.add_argument("--embedding-cache", default=str(DEFAULT_EMBEDDINGS_CACHE_PATH), help="Cache de embeddings")
    parser.add_argument("--refresh-embeddings", action="store_true", help="Regenera la cache antes de buscar")
    parser.add_argument("--build-embeddings", action="store_true", help="Genera la cache y termina")
    parser.add_argument("--semantic-threshold", type=float, default=DEFAULT_SEMANTIC_THRESHOLD, help="Umbral minimo")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    image_description: dict[str, Any] | None = None
    query = args.query.strip()

    if args.image:
        if query:
            parser.error("No combines texto e imagen. Usa una busqueda de texto o --imagen.")
        image_description = describe_image_as_query(args.image)
        query = image_description["query"]

    products = load_products(args.products)
    if args.build_embeddings:
        product_embeddings = load_or_create_product_embeddings(
            products,
            cache_path=args.embedding_cache,
            model=args.embedding_model,
            refresh=True,
        )
        print(
            json.dumps(
                {
                    "embedding_model": args.embedding_model,
                    "embedding_cache": args.embedding_cache,
                    "total": len(product_embeddings),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if not query:
        parser.error("Indica una busqueda o una imagen. Los filtros solo acotan una busqueda semantica.")

    query_embedding: list[float] | None = None
    product_embeddings: dict[str, list[float]] | None = None

    try:
        product_embeddings = load_or_create_product_embeddings(
            products,
            cache_path=args.embedding_cache,
            model=args.embedding_model,
            refresh=args.refresh_embeddings,
        )
        query_embedding = embed_texts([query], model=args.embedding_model)[0]
    except EmbeddingError as exc:
        parser.error(str(exc))

    results = search_products(
        products,
        brand=args.brand,
        category=args.category,
        folder=args.folder,
        limit=args.limit,
        query_embedding=query_embedding,
        product_embeddings=product_embeddings,
        semantic_threshold=args.semantic_threshold,
    )

    output = {
        "query": query,
        "filters": {
            "brand": args.brand,
            "category": args.category,
            "folder": args.folder,
        },
        "embedding_model": args.embedding_model,
        "embedding_cache": args.embedding_cache,
        "total": len(results),
        "results": [result.to_dict() for result in results],
    }
    if image_description:
        output["image_description"] = image_description

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
