# Lookr — Buscador y recomendador de moda con IA

Lookr es un sistema de búsqueda y recomendación de prendas que combina visión artificial, embeddings multimodales y búsqueda vectorial semántica. Permite buscar ropa por texto, por imagen o por foto de inspiración, gestionar un armario personal por usuario y guardar favoritos, todo con recomendaciones generadas por un agente de IA.

---

## Características

- **Búsqueda híbrida por texto** — combina similitud visual (CLIP), semántica multilingüe y matching por palabras clave
- **Búsqueda por imagen** — encuentra prendas visualmente similares usando CLIP
- **Inspiración** — sube cualquier foto, el agente la analiza y recomienda prendas similares del catálogo sin añadirla
- **Mi armario** — espacio personal por usuario: sube prendas propias, el agente las describe y quedan indexadas en un namespace privado de Pinecone
- **Similares desde el armario** — busca en el catálogo prendas que combinan con cualquier prenda del armario personal
- **Favoritos** — guarda prendas con ♥ en una wishlist persistente (localStorage)
- **Modal de detalle** — vista ampliada de cada prenda con descripción completa y categorías

---

## Stack técnico

| Componente | Tecnología |
|---|---|
| Agente IA | pydantic-ai + Ollama (`gemma3:12b`) |
| Embeddings visuales | CLIP `clip-ViT-B-32` (GPU) — 512d |
| Embeddings semánticos | `paraphrase-multilingual-mpnet-base-v2` (CPU) — 768d |
| Base de datos vectorial | Pinecone serverless (AWS us-east-1) |
| Backend | FastAPI + uvicorn |
| Frontend | HTML / CSS / JS |

### Índices Pinecone

| Índice | Dimensión | Namespace | Función |
|---|---|---|---|
| `buscador-multimodal` | 512d cosine | `mi-espacio` | Similitud visual (CLIP imagen) |
| `buscador-semantico` | 768d cosine | `mi-espacio` | Comprensión semántica del catálogo |
| `buscador-semantico` | 768d cosine | `armario-{user_id}` | Armario personal por usuario |

---

## Estructura del proyecto

```text
ProyectoIA/
├── README.md
├── requirements.txt
├── data/
│   ├── .env                          # Variables de entorno (no incluir en git)
│   ├── images/                       # Imágenes del catálogo
│   │   └── armario/                  # Imágenes del armario personal
│   ├── armarios/                     # Metadatos JSON por usuario ({user_id}.json)
│   └── examples/
│       └── training_examples.jsonl   # Ejemplos de entrenamiento para el agente
└── src/
    ├── java/
    │   └── ImageDescriptionAgent.java
    └── python/
        ├── api.py                    # Servidor FastAPI (punto de entrada principal)
        ├── agent.py                  # Configuración del agente Ollama
        ├── armario.py                # Gestión del armario personal (JSON + Pinecone)
        ├── image_utils.py            # Análisis de imágenes con el agente
        ├── categories.py             # Categorías permitidas y modelo DescripcionRopa
        ├── examples.py               # Carga de ejemplos de estilo para el agente
        ├── main.py                   # CLI para analizar imágenes desde terminal
        ├── reindexar.py              # Script de reindexación masiva del catálogo
        ├── static/
        │   └── index.html            # Interfaz web completa
        └── pinec/
            ├── __init__.py
            ├── index.py              # Creación de índices Pinecone
            ├── embeddings.py         # Modelos CLIP y multilingual
            ├── upload_data.py        # Subida a ambos índices Pinecone
            └── search.py             # Búsqueda híbrida (visual + semántica + keyword)
```

---

## Instalación

### Requisitos previos

- Python 3.12+
- [Ollama](https://ollama.com) con el modelo `gemma3:12b` descargado
- Cuenta en [Pinecone](https://pinecone.io) con API key
- GPU NVIDIA recomendada (CUDA 12.x) para CLIP

### Pasos

```bash
# 1. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Instalar PyTorch con CUDA (RTX / GPU NVIDIA)
pip install torch==2.5.1+cu121 --index-url https://download.pytorch.org/whl/cu121

# 4. Configurar variables de entorno
cp data/.env.example data/.env
# Editar data/.env con tus credenciales
```

### Variables de entorno (`data/.env`)

```env
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_LOCAL=http://localhost:11434/v1
OLLAMA_MODEL=gemma3:12b
PINECONE_APIKEY=tu_api_key_aqui
```

---

## Arrancar el servidor

```bash
source venv/bin/activate
cd src/python
python3 api.py
```

La interfaz estará disponible en [http://localhost:8000](http://localhost:8000)

---

## API REST

### Búsqueda y catálogo

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/recomendar/texto?query=...` | Búsqueda híbrida por texto |
| `POST` | `/recomendar/imagen` | Búsqueda visual por imagen subida |
| `POST` | `/descubrir` | Analiza foto + recomienda similares (sin indexar) |
| `POST` | `/analizar` | Analiza imagen y la añade al catálogo |
| `GET` | `/imagen/{filename}` | Sirve imágenes del catálogo |
| `GET` | `/imagen/armario/{filename}` | Sirve imágenes del armario personal |

### Armario personal

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/armario/{user_id}` | Lista todas las prendas del armario |
| `POST` | `/armario/{user_id}` | Añade una imagen al armario (analiza con IA) |
| `DELETE` | `/armario/{user_id}/{item_id}` | Elimina una prenda del armario |
| `GET` | `/armario/{user_id}/{item_id}/similares` | Busca en el catálogo prendas que combinan |

El `user_id` se genera automáticamente en el navegador (UUID en localStorage) sin necesidad de registro.

---

## Búsqueda híbrida

Cada búsqueda por texto combina tres capas:

```
Score final = 0.20 × visual (CLIP) + 0.50 × semántico (multilingual) + 0.30 × keyword (metadatos)
```

- **Visual**: CLIP traduce la query a inglés y busca por similitud de imagen
- **Semántico**: modelo multilingüe entiende el español directamente
- **Keyword**: boost cuando la query coincide con descripción, categorías o estilo
- **Contextual**: queries como "outfit para una boda" se expanden con Ollama antes de embedear

---

## Armario personal — almacenamiento

Cada usuario tiene un espacio privado identificado por un UUID generado en el navegador:

| Tipo | Ubicación |
|---|---|
| Metadatos | `data/armarios/{user_id}.json` |
| Imágenes | `data/images/armario/{user_id}_{item_id}.{ext}` |
| Vectores | Pinecone `buscador-semantico`, namespace `armario-{user_id}` |

---

## Reindexación

Para re-analizar las imágenes del catálogo con el agente y regenerar ambos índices:

```bash
cd src/python
python3 reindexar.py --todo          # Reindexar todo (pide confirmación)
python3 reindexar.py "Captura*"      # Solo imágenes cuyo nombre coincida con el patrón
python3 reindexar.py                 # Solo imágenes con nombre sin slug legible
```

### Eliminar una entrada duplicada de Pinecone

```python
# Desde src/python/
from pinec.index import crear_index, crear_index_semantico

dense    = crear_index()
semantic = crear_index_semantico()

dup_id = "id-del-vector-a-eliminar"
dense.delete(ids=[dup_id], namespace="mi-espacio")
semantic.delete(ids=[dup_id], namespace="mi-espacio")
```

---

## CLI — Analizar imágenes desde terminal

```bash
cd src/python
python3 main.py data/images/vestido.jpg
python3 main.py img1.jpg img2.jpg img3.jpg  # Múltiples imágenes
```

---

## Integración Java

La clase `ImageDescriptionAgent` ejecuta `python3 main.py` y devuelve el JSON como `String`.

```bash
cd src/java
javac ImageDescriptionAgent.java
java ImageDescriptionAgent data/images/bolso.jpeg
```

```java
ImageDescriptionAgent agent = new ImageDescriptionAgent(Paths.get("/ruta/a/ProyectoIA"));
String json = agent.describeImage(Paths.get("data/images/bolso.jpeg"));
```

---

## Modelos descargados automáticamente

Al arrancar la API por primera vez se descargan:

- `clip-ViT-B-32` (~340 MB) — embeddings visuales, cargado en GPU
- `paraphrase-multilingual-mpnet-base-v2` (~280 MB) — embeddings semánticos, cargado en CPU

Los modelos se cachean en `~/.cache/huggingface/`.
