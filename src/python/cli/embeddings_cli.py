from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[1]
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from core.config import (
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_EMBEDDINGS_CACHE_PATH,
    DEFAULT_PINECONE_INDEX_NAME,
    DEFAULT_PINECONE_NAMESPACE,
    DEFAULT_PRODUCTS_PATH,
)
from repositories.product_catalog import load_products
from services.embeddings import (
    load_or_create_product_embeddings,
    search_pinecone,
    upsert_products_to_pinecone,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gestiona embeddings locales y Pinecone.")
    parser.add_argument(
        "--products",
        default=str(DEFAULT_PRODUCTS_PATH),
        help="Ruta del catalogo JSON",
    )
    parser.add_argument(
        "--cache",
        default=str(DEFAULT_EMBEDDINGS_CACHE_PATH),
        help="Ruta de la cache local de embeddings",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_EMBEDDING_MODEL,
        help="Modelo local de embeddings de Ollama",
    )
    parser.add_argument("--refresh", action="store_true", help="Regenera la cache local")
    parser.add_argument("--build-local", action="store_true", help="Construye la cache local")
    parser.add_argument("--sync-pinecone", action="store_true", help="Sube el catalogo a Pinecone")
    parser.add_argument("--pinecone-query", help="Busca texto directamente en Pinecone")
    parser.add_argument("--top-k", type=int, default=5, help="Numero de resultados de Pinecone")
    parser.add_argument("--namespace", default=DEFAULT_PINECONE_NAMESPACE, help="Namespace de Pinecone")
    parser.add_argument("--index", default=DEFAULT_PINECONE_INDEX_NAME, help="Indice de Pinecone")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.build_local:
        products = load_products(args.products)
        embeddings = load_or_create_product_embeddings(
            products,
            cache_path=args.cache,
            model=args.model,
            refresh=args.refresh,
        )
        print(json.dumps({"cache": args.cache, "model": args.model, "total": len(embeddings)}, indent=2))
        return

    if args.sync_pinecone:
        products = load_products(args.products)
        stats = upsert_products_to_pinecone(
            products,
            index_name=args.index,
            namespace=args.namespace,
        )
        print(json.dumps(stats, ensure_ascii=False, indent=2, default=str))
        return

    if args.pinecone_query:
        hits = search_pinecone(
            args.pinecone_query,
            index_name=args.index,
            namespace=args.namespace,
            top_k=args.top_k,
        )
        print(json.dumps(hits, ensure_ascii=False, indent=2, default=str))
        return

    parser.error("Indica --build-local, --sync-pinecone o --pinecone-query.")


if __name__ == "__main__":
    main()
