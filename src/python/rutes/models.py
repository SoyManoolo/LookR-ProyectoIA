from pydantic import BaseModel

class Recomendacion(BaseModel):
    id: str
    score: float
    nombre: str
    descripcion: str
    imagen_url: str | None = None
    categoria: list[str] = []
    estilo: str = ""

class RespuestaRecomendaciones(BaseModel):
    resultados: list[Recomendacion]

class ItemArmario(BaseModel):
    id: str
    nombre: str
    descripcion: str
    categoria: list[str]
    estilo: str
    imagen_url: str | None = None


class RespuestaArmario(BaseModel):
    items: list[ItemArmario]

class ResultadoAnalisis(BaseModel):
    record_id: str
    descripcion: str
    categoria: list[str]
    estilo: str
    imagen_url: str | None = None

class ResultadoDescubrir(BaseModel):
    descripcion: str
    categoria: list[str]
    estilo: str
    recomendaciones: list[Recomendacion]