import os

from pydantic_ai import Agent
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.providers.ollama import OllamaProvider

from categories import categorias_permitidas
from examples import cargar_ejemplos_entrenamiento

# Función para crear el agente de IA especializado en describir prendas de ropa
def crear_agente() -> Agent:
    # Cargamos la URL base de Ollama desde las variables de entorno, con valores por defecto
    # Prioridad: OLLAMA_BASE_URL > OLLAMA_LOCAL > URL local por defecto
    url = (
        os.getenv("OLLAMA_BASE_URL")
        or os.getenv("OLLAMA_LOCAL")
        or "http://localhost:11434/v1"
    )

    # Cargamos el nombre del modelo desde las variables de entorno, con gemma4:e4b como valor por defecto
    model_name = os.getenv("OLLAMA_MODEL", "gemma4:e4b")
    # Cargamos algunos ejemplos del JSON de entrenamiento para que el agente siga un estilo consistente
    contexto_ejemplos = cargar_ejemplos_entrenamiento()

    # Instanciamos el modelo de Ollama con la URL y el nombre configurados
    model = OllamaModel(
        model_name,
        provider=OllamaProvider(base_url=url),
    )

    # Creamos el system_prompt con instrucciones detalladas para que el agente sea lo más específico posible
    # Incluimos las categorías permitidas y los ejemplos de estilo para mantener consistencia
    system_prompt = "\n".join(
        [
            "Eres un experto en moda.",
            "Analiza prendas de ropa en imágenes y devuelve descripciones estructuradas y atractivas para el cliente.",
            "Devuelve SOLO JSON, sin markdown ni texto extra.",
            'El JSON SOLO puede contener estas llaves: "descripcion", "categoria" y "estilo".',
            "La descripción debe ser atractiva pero breve, máximo 30 palabras.",
            "Incluye todas las categorías que apliquen, pero elige solo un tipo de prenda principal.",
            'Puedes añadir etiquetas de uso como "elegante", "casual", "formal", "deportivo", "noche" o "accesorio" si aplican.',
            f'En "categoria" SOLO puedes usar estos valores: {categorias_permitidas}.',
            "No inventes categorías nuevas.",
            contexto_ejemplos,
        ]
    )

    # Retornamos el agente sin output_type para evitar tool calling (incompatible con modelos multimodales)
    return Agent(model, system_prompt=system_prompt)
