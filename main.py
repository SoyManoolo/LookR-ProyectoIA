from pydantic_ai import Agent
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.providers.ollama import OllamaProvider
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv('OLLAMA_URL')

model = OllamaModel(
    'gemma4:31b', provider=OllamaProvider(base_url=url)
    # system_prompt=(
    #     'Actúa como un experto en moda para describir ropa, como si estuvieras hablando directamente con el cliente'
    # )
)

agent = Agent(model)

result_sync = agent.run_sync('Desarrolla la formula de MRUA')

print(result_sync.output)