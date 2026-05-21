from fastapi import HTTPException
import asyncio
from concurrent.futures import ThreadPoolExecutor
from agent import crear_agente
from pinec.embeddings import get_model, get_text_model

class AppState:
    agent = None

state = AppState()

async def inicializar_servicios():
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        # Cargamos los modelos en hilos para no bloquear el arranque
        await loop.run_in_executor(pool, get_model)
        await loop.run_in_executor(pool, get_text_model)
    
    state.agent = crear_agente()

def get_agent():
    """Dependencia para usar en las rutas"""
    if state.agent is None:
        raise HTTPException(status_code=503, detail="Agente de IA no inicializado")
    return state.agent