# Agente descriptor de moda

Proyecto Python para describir imágenes de prendas y devolver un JSON con:

```json
{
  "descripcion": "...",
  "categoria": ["..."],
  "estilo": "..."
}
```

## Estructura

```text
.
├── README.md
├── requirements.txt
├── data/
│   ├── pruebaBBDD.json           # Base de datos de ejemplo para Pinecone
│   ├── images/                   # Imágenes de prueba
│   │   ├── bolso.jpeg
│   │   ├── unnamed.png
│   │   └── vestido_gala.png
│   └── examples/
│       └── training_examples.jsonl
├── src/
│   ├── java/
│   │   └── ImageDescriptionAgent.java
│   └── python/
│       ├── main.py               # CLI principal para describir imágenes
│       ├── agent.py              # Creación y configuración del agente IA
│       ├── image_utils.py        # Utilidades para procesar imágenes
│       ├── categories.py         # Tipos, categorías y modelos Pydantic
│       ├── examples.py           # Carga de ejemplos de entrenamiento
│       └── pinec/                # Módulos para búsqueda vectorial con Pinecone
│           ├── index.py          # Creación del índice vectorial
│           ├── upload_data.py    # Carga de datos a Pinecone
│           └── search.py         # Búsquedas semánticas
```

## Probar

### Descripción de imágenes con IA

Para describir una imagen de prenda usando el agente especializado en moda:

```bash
pip install -r requirements.txt
python main.py data/images/bolso.jpeg
```

Si no pasas imagen, usa por defecto `data/images/unnamed.png`:

```bash
python main.py
```

### Búsqueda vectorial con Pinecone

Para buscar prendas en el índice vectorial:

```bash
cd src/python/pinec
python search.py "rojo"          # Búsqueda simple
python search.py "camisa roja"   # Búsqueda con múltiples palabras
```

Para subir datos a Pinecone (dentro de `src/python`):

```python
from pinec.upload_data import subir_datos

# Subir el archivo de prueba
subir_datos("../../data/pruebaBBDD.json", "mi-espacio")
```

## Configuración

### Variables de entorno

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```env
# Configuración de Ollama (para el agente de descripción)
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=gemma4:e4b
TRAINING_EXAMPLES_PATH=data/examples/training_examples.jsonl

# Configuración de Pinecone (para búsqueda vectorial)
PINECONE_APIKEY=tu_api_key_aqui
```

### Modelo de Ollama

Por defecto usa `gemma4:e4b`.

```bash
OLLAMA_MODEL=tu-modelo python main.py data/images/bolso.jpeg
```

### Ejemplos de entrenamiento

Los ejemplos de `data/examples/training_examples.jsonl` se cargan automáticamente para guiar el estilo de respuesta del agente. No es fine tuning real, pero mantiene la consistencia de formato en las respuestas.

### Pinecone

El índice vectorial se crea automáticamente la primera vez que ejecutas `search.py` o `upload_data.py`. Usa:

- **Modelo de embedding**: `llama-text-embed-v2`
- **Cloud**: AWS
- **Región**: us-east-1
- **Índice**: `buscador`
- **Namespace**: `mi-espacio` (para búsquedas)

## Arquitectura del código

El proyecto se divide en dos funcionalidades principales:

### 1. Agente de Descripción de Imágenes

- **`agent.py`**: Crea y configura el agente IA con el modelo Ollama
- **`image_utils.py`**: Maneja lectura de imágenes y detección de tipos MIME
- **`categories.py`**: Define las categorías de prendas y el modelo de salida
- **`examples.py`**: Carga ejemplos para mantener consistencia en las respuestas
- **`main.py`**: Interfaz CLI para analizar imágenes

### 2. Búsqueda Vectorial con Pinecone

- **`pinec/index.py`**: Crea o accede al índice vectorial
- **`pinec/upload_data.py`**: Carga datos JSON en Pinecone
- **`pinec/search.py`**: Realiza búsquedas semánticas sobre las prendas

## Llamar desde Java

La clase `ImageDescriptionAgent` ejecuta `python3 main.py <imagen>` y devuelve el JSON como `String`.

```bash
cd src/java
javac ImageDescriptionAgent.java
java ImageDescriptionAgent data/images/bolso.jpeg
```

Uso dentro de una aplicación Java:

```java
ImageDescriptionAgent agent = new ImageDescriptionAgent(Paths.get("/ruta/a/ProyectoIA"));
String json = agent.describeImage(Paths.get("data/images/bolso.jpeg"));
```
