FROM python:3.11-slim

WORKDIR /app

# Copiar requirements e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el proyecto completo
COPY . .

# Exponer el puerto (para referencia, Railway asigna el puerto via variable de entorno)
EXPOSE 8080

# Comando de inicio
CMD ["python", "src/python/api.py"]
