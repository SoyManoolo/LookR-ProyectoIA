# 1. Imagen base ligera de Python
FROM python:3.10-slim

# 2. Instalar dependencias del sistema para Rust/Tantivy
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 3. Establecer directorio de trabajo
WORKDIR /app

# 4. Copiar e instalar dependencias (Caché de Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar el código fuente (Regla A10: No copiamos /data)
COPY src/ ./src/
COPY config/ ./config/
COPY CLAUDE.md .

# 6. Crear directorios para los artefactos que se descargarán (Regla A10)
RUN mkdir -p data/index data/processed data/raw

# 7. Variable de entorno para el puerto
ENV PORT=8080

# 8. Comando para arrancar (ejemplo con un futuro servidor API)
# Por ahora, dejamos que pueda ejecutar tus scripts de búsqueda
CMD ["python", "src/searcher.py"]
