from typing import Literal
from pydantic import BaseModel


# Categorías utilizadas para que el agente elija una o más de estas
# Incluye tipos de prendas, accesorios y etiquetas de uso
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

# Cargamos las categorías en una variable para pasarselas todas al agente
# Esto permite que el agente vea exactamente qué opciones tiene disponibles
categorias_permitidas = Categoria.__args__

# Definimos todas las claves que tendrá la respuesta del agente
# Este modelo Pydantic valida y estructura la salida del agente
class DescripcionRopa(BaseModel):
    # Descripción textual breve y atractiva de la prenda
    descripcion: str
    # Lista de categorías que aplican a la prenda
    categoria: list[Categoria]
    # Etiqueta de estilo o uso (elegante, casual, formal, etc.)
    estilo: str
