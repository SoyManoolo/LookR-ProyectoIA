from fastapi import HTTPException
from agent import crear_agente

class AppState:
    agent = None

state = AppState()

async def inicializar_servicios():
    # Railway puede reiniciar el contenedor si el startup tarda demasiado o consume
    # demasiada memoria. Los modelos de embeddings se cargan bajo demanda en pinec.embeddings.
    state.agent = crear_agente()

def get_agent():
    """Dependencia para usar en las rutas"""
    if state.agent is None:
        raise HTTPException(status_code=503, detail="Agente de IA no inicializado")
    return state.agent
