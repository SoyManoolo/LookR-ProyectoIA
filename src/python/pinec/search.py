import argparse

try:
    from .index import crear_index
    from .embeddings import embed_texto, embed_imagen
except ImportError:
    from index import crear_index
    from embeddings import embed_texto, embed_imagen

dense_index = crear_index()


def search(query: str, por_imagen: bool = False, top_k: int = 5) -> list[tuple]:
    """Busca prendas similares por texto o por imagen usando embeddings CLIP.

    Args:
        query: Texto de búsqueda o ruta a una imagen.
        por_imagen: Si True, trata query como ruta de imagen.
        top_k: Número de resultados a devolver.

    Returns:
        Lista de tuplas (id, score, nombre, descripcion).
    """
    vector = embed_imagen(query) if por_imagen else embed_texto(query)

    results = dense_index.query(
        namespace="mi-espacio",
        vector=vector,
        top_k=top_k,
        include_metadata=True,
    )

    return [
        (
            m["id"],
            m["score"],
            m["metadata"].get("nombre", "N/A"),
            m["metadata"].get("descripcion", "N/A"),
            m["metadata"].get("imagen", ""),
            m["metadata"].get("categoria", []),
            m["metadata"].get("estilo", ""),
        )
        for m in results["matches"]
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="Texto de búsqueda o ruta de imagen")
    parser.add_argument("--imagen", action="store_true", help="Buscar por imagen")
    args = parser.parse_args()

    resultados = search(args.query, por_imagen=args.imagen)
    for item in resultados:
        print(item)


if __name__ == "__main__":
    main()
