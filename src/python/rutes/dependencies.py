from fastapi import HTTPException
from agent import crear_agente
from pinec.embeddings import get_model, get_text_model

class AppState:
    agent = None

state = AppState()

async def inicializar_servicios():
    """Se llama una sola vez en el lifespan de api.py"""
    get_model()
    get_text_model()
    state.agent = crear_agente()

def get_agent():
    """Dependencia para usar en las rutas"""
    if state.agent is None:
        raise HTTPException(status_code=503, detail="Agente de IA no inicializado")
    return state.agent