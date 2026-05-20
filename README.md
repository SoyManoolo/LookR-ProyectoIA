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
│   │   └── eleganza-beige-satin-gown.png
│   └── examples/
│       └── training_examples.json
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
python src/python/main.py data/images/eleganza-beige-satin-gown.png
```

Si no pasas imagen, usa por defecto `data/images/eleganza-beige-satin-gown.png`:

```bash
python src/python/main.py
```

### Búsqueda vectorial con Pinecone

Para buscar prendas en el índice vectorial:

```bash
python src/python/pinec/search.py --texto "rojo"
python src/python/pinec/search.py --texto "camisa roja"
python src/python/pinec/search.py --imagen data/images/eleganza-beige-satin-gown.png
```

Para subir datos a Pinecone:

```python
import sys
sys.path.insert(0, "src/python")

from pinec.upload_data import subir_datos

# Subir el archivo de prueba
subir_datos("data/pruebaBBDD.json", "mi-espacio")
```

## Configuración

### Variables de entorno

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```env
# Configuración de Ollama (para el agente de descripción)
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=gemma4:e4b
TRAINING_EXAMPLES_PATH=data/examples/training_examples.json

# Configuración de Pinecone (para búsqueda vectorial)
PINECONE_APIKEY=tu_api_key_aqui
PINECONE_INDEX_NAME=buscador
PINECONE_REGION=us-east-1
PINECONE_NAMESPACE=mi-espacio
```

### Modelo de Ollama

Por defecto usa `gemma4:e4b`.

```bash
OLLAMA_MODEL=tu-modelo python src/python/main.py data/images/eleganza-beige-satin-gown.png
```

### Ejemplos de entrenamiento

Los ejemplos de `data/examples/training_examples.json` se cargan automáticamente para guiar el estilo de respuesta del agente. No es fine tuning real, pero mantiene la consistencia de formato en las respuestas.

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

La clase `ImageDescriptionAgent` ejecuta `python3 src/python/main.py <imagen>` y devuelve el JSON como `String`.
La clase espera recibir la raíz del proyecto y ejecuta internamente `src/python/main.py`.

```bash
javac src/java/ImageDescriptionAgent.java
java -cp src/java ImageDescriptionAgent data/images/eleganza-beige-satin-gown.png
```

Uso dentro de una aplicación Java:

```java
ImageDescriptionAgent agent = new ImageDescriptionAgent(Paths.get("/ruta/a/ProyectoIA"));
String json = agent.describeImage(Paths.get("data/images/eleganza-beige-satin-gown.png"));
```
