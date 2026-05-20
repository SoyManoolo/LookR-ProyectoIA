import sys
import uuid
from pathlib import Path

try:
    from .index import crear_index, crear_index_semantico
    from .embeddings import embed_imagen, embed_descripcion
    from categories import DescripcionRopa
except ImportError:
    from index import crear_index, crear_index_semantico
    from embeddings import embed_imagen, embed_descripcion
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from categories import DescripcionRopa

dense_index = crear_index()
semantic_index = crear_index_semantico()

_NAMESPACE = "mi-espacio"



def subir_prenda(datos: DescripcionRopa, imagen_path: str) -> str:
    """Sube una prenda a los índices visual (CLIP) y semántico (multilingual).

    Returns:
        El id generado para el registro.
    """
    record_id = str(uuid.uuid4())
    nombre = datos.descripcion.split(",")[0].strip()[:60]
    metadata = {
        "nombre": nombre,
        "descripcion": datos.descripcion,
        "categoria": datos.categoria,
        "estilo": datos.estilo,
        "imagen": imagen_path,
    }

    # Índice visual: embedding CLIP de la imagen
    dense_index.upsert(
        vectors=[{"id": record_id, "values": embed_imagen(imagen_path), "metadata": metadata}],
        namespace=_NAMESPACE,
    )

    # Índice semántico: embedding multilingual de descripción + categorías + estilo
    texto_semantico = f"{datos.descripcion}. Categorías: {', '.join(datos.categoria)}. Estilo: {datos.estilo}"
    semantic_index.upsert(
        vectors=[{"id": record_id, "values": embed_descripcion(texto_semantico), "metadata": metadata}],
        namespace=_NAMESPACE,
    )

    return record_id
