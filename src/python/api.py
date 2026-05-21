from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Carga de variables de entorno (al principio de todo)
load_dotenv(Path(__file__).parent.parent.parent / ".env")

# Importaciones de tu estructura refactorizada
from rutes.dependencies import inicializar_servicios
from rutes.utils import _STATIC
from rutes import (
    recomendar_api,
    analizar_api,
    descubrir_api,
    armario_api,
    imagen_api
)

# Gestión del ciclo de vida (Solo una función)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializa el agente y modelos de Pinecone una sola vez al arrancar
    await inicializar_servicios() 
    yield

# Instancia de la aplicación
app = FastAPI(title="Recomendador de ropa", lifespan=lifespan)

# Middleware (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro de Rutas (Routers)
# Aquí conectamos los archivos de la carpeta /rutes
app.include_router(recomendar_api.router, tags=["Recomendaciones"])
app.include_router(analizar_api.router, tags=["Análisis"])
app.include_router(descubrir_api.router, tags=["Descubrir"])
app.include_router(armario_api.router, tags=["Armario"])
app.include_router(imagen_api.router, tags=["Imágenes"])

# Archivos estáticos y ruta base
app.mount("/static", StaticFiles(directory=_STATIC), name="static")

@app.get("/")
async def index():
    return FileResponse(_STATIC / "index.html")

# 8. Ejecución del servidor
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=False)
