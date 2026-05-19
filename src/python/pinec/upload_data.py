import json
import uuid
from pathlib import Path

try:
    from .index import crear_index
    from .embeddings import embed_imagen
    from categories import DescripcionRopa
except ImportError:
    from index import crear_index
    from embeddings import embed_imagen
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from categories import DescripcionRopa

dense_index = crear_index()

# Ruta raíz del proyecto para resolver rutas de imágenes relativas
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


def subir_datos(path, ns):
    """Carga registros desde un JSON al índice, generando embeddings CLIP por imagen."""
    with open(path, "r", encoding="utf-8") as f:
        registros = json.load(f)

    vectors = []
    for r in registros:
        imagen_path = _PROJECT_ROOT / r["imagen"]
        vector = embed_imagen(imagen_path)
        vectors.append({
            "id": r["id"],
            "values": vector,
            "metadata": {
                "nombre": r.get("nombre", ""),
                "descripcion": r.get("descripcion", ""),
                "categoria": r.get("categorias", []),
                "estilo": r.get("estilo", ""),
                "imagen": r["imagen"],
            },
        })

    dense_index.upsert(vectors=vectors, namespace=ns)


def subir_prenda(datos: DescripcionRopa, imagen_path: str) -> str:
    """Sube una prenda analizada por el agente usando embedding CLIP de la imagen.

    Returns:
        El id generado para el registro.
    """
    record_id = str(uuid.uuid4())
    vector = embed_imagen(imagen_path)
    dense_index.upsert(
        vectors=[{
            "id": record_id,
            "values": vector,
            "metadata": {
                "nombre": Path(imagen_path).stem,
                "descripcion": datos.descripcion,
                "categoria": datos.categoria,
                "estilo": datos.estilo,
                "imagen": imagen_path,
            },
        }],
        namespace="mi-espacio",
    )
    return record_id
