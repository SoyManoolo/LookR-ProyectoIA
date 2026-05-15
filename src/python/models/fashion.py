from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


Categoria = Literal[
    "vestido",
    "chaqueta",
    "pantalón",
    "camisa",
    "camiseta",
    "blusa",
    "falda",
    "abrigo",
    "traje",
    "jersey",
    "sudadera",
    "top",
    "zapatos",
    "bota",
    "deportivas",
    "accesorio",
    "bolso",
    "joyería",
    "gafas",
    "elegante",
    "casual",
    "formal",
    "deportivo",
    "noche",
    "otro",
]

categorias_permitidas = Categoria.__args__


class DescripcionRopa(BaseModel):
    descripcion: str
    categoria: list[Categoria]
    estilo: str
