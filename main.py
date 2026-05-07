from pydantic_ai import Agent, BinaryContent
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.providers.ollama import OllamaProvider
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from llama_cpp import Llama
from typing import Literal

load_dotenv()
url = os.getenv('OLLAMA_URL')

Categoria = Literal[
    'vestido',
    'chaqueta',
    'pantalón',
    'camisa',
    'camiseta',
    'falda',
    'abrigo',
    'traje',
    'zapatos',
    'accesorio',
    'otro'
]

class DescripcionRopa(BaseModel):
    Descripcion: str
    Categoria: list[Categoria]
    estilo: str


model = OllamaModel(
    'gemma4:e4b',
    provider=OllamaProvider(base_url=url),
)

#model = Llama.from_pretrained(
#	repo_id="jc-builds/Qwen3.5-9B-VLM-Q4_K_M-GGUF",
#	filename="Qwen3.5-9B-Q4_K_M.gguf",
#)

#model.create_chat_completion(
#	messages = [
#		{
#			"role": "user",
#			"content": [
#				{
#					"type": "text",
#					"text": "Describe this image in one sentence."
#				},
#				{
#					"type": "image_url",
#					"image_url": {
#						"url": "https://cdn.britannica.com/61/93061-050-99147DCE/Statue-of-Liberty-Island-New-York-Bay.jpg"
#					}
#				}
#			]
#		}
#	]
#)


with open('unnamed.png', 'rb') as f:
    image_bytes = f.read()

agent = Agent(
    model,
    output_type=DescripcionRopa,
    system_prompt='Eres un experto en moda. Analiza prendas de ropa en imágenes y devuelve descripciones estructuradas y atractivas para el cliente.'
)

result = agent.run_sync([
    BinaryContent(data=image_bytes, media_type='image/png'),
])

print(result.output)