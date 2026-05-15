from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


PRODUCT_TEXT_FIELDS = (
    "nombre",
    "marca",
    "categorias",
    "estilo",
    "descripcion",
    "carpeta",
)


@dataclass
class Product:
    id: str
    nombre: str
    descripcion: str
    marca: str = ""
    categorias: list[str] = field(default_factory=list)
    estilo: str = ""
    carpeta: str = ""
    imagen: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Product":
        categorias = data.get("categorias", data.get("categoria", []))
        if isinstance(categorias, str):
            categorias = [categorias]

        return cls(
            id=str(data["id"]),
            nombre=str(data.get("nombre", "")),
            descripcion=str(data.get("descripcion", "")),
            marca=str(data.get("marca", "")),
            categorias=[str(categoria) for categoria in categorias],
            estilo=str(data.get("estilo", "")),
            carpeta=str(data.get("carpeta", data.get("folder", ""))),
            imagen=str(data.get("imagen", data.get("image", ""))),
        )


@dataclass
class SearchResult:
    producto: Product
    puntuacion: float
    score_embedding: float | None = None

    def to_dict(self) -> dict[str, Any]:
        data = {
            "puntuacion": round(self.puntuacion, 2),
            "producto": asdict(self.producto),
        }
        if self.score_embedding is not None:
            data["score_embedding"] = round(self.score_embedding, 4)
        return data


def product_fields(product: Product) -> dict[str, str]:
    return {
        field: " ".join(product.categorias) if field == "categorias" else getattr(product, field)
        for field in PRODUCT_TEXT_FIELDS
    }


def product_embedding_text(product: Product) -> str:
    fields = product_fields(product)
    return "\n".join(
        [f"{field.capitalize()}: {fields[field]}" for field in PRODUCT_TEXT_FIELDS]
    )
