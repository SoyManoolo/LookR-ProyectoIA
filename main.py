from pydantic_ai import Agent, BinaryContent
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.providers.ollama import OllamaProvider
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Literal
import logging

# Mostramos los logs en caso de que haya un error
logging.basicConfig(level=logging.INFO)

# Cargamos las variables de entorno
load_dotenv()
url = os.getenv('OLLAMA_LOCAL')

# Categorias para la definición de las prendas de vestir
Categoria = Literal[
    # Prendas principales
    'vestido', 'chaqueta', 'pantalón', 'camisa', 'camiseta', 'blusa', 
    'falda', 'abrigo', 'traje', 'jersey', 'sudadera', 'top', 
    # Calzado
    'zapatos', 'bota', 'deportivas',
    # Accesorios
    'accesorio', 'bolso', 'joyería', 'gafas',
    # Estilos/Ocasiones
    'elegante', 'casual', 'formal', 'deportivo', 'noche',
    # Otros
    'otro'
]

# Las guardamos en una variable para poder pasarselo al agente
categorias_permitidas = Categoria.__args__

# Clase DescripcionRpopa para definir las partes que tendrá la descripción de la ropa
class DescripcionRopa(BaseModel):
    descripcion: str
    categoria: list[Categoria]
    estilo: str

# Creamos el modelo
model = OllamaModel(
    'gemma4:e4b',
    provider=OllamaProvider(base_url=url),
)


with open('./data/unnamed.png', 'rb') as f:
    image_bytes = f.read()


# Creamos el agente pasandole el modelo, el output que queremos y el system_prompt para definir la manera en la que queremos que el agente responda
agent = Agent(
    model,
    output_type=DescripcionRopa,
    system_prompt='Eres un experto en moda. Analiza prendas de ropa en imágenes y devuelve descripciones estructuradas y atractivas para el cliente que esté directamente en formato JSON, nada de markdown'
    'Devuelve descripciones atractivas pero BREVES (máximo 30 palabras)'
    'El JSON SOLO puede contener estas llaves: "descripcion", "categoria" y "estilo"'
    'Incluye TODAS las categorías que apliquen, pero elige solo un tipo de prenda principal (ej: no pongas camisa y camiseta a la vez). Puedes añadir más etiquetas solo si describen el uso como "elegante" o "accesorio".'
    f'IMPORTANTE: En "Categoria" SOLO puedes usar estos valores: {categorias_permitidas}'
    'No inventes categorías nuevas.'
)

# Le pasamos la imagen al agente para que haga la descripción
result = agent.run_sync([
    BinaryContent(data=image_bytes, media_type='image/png'),
])

# Guardamos la respuesta del agente
datos = result.output

# Mostramos el JSON creado por el agente
print(datos.model_dump_json(indent=2))