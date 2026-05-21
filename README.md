# Lookr — Buscador y recomendador de moda con IA

Lookr es un sistema de búsqueda y recomendación de prendas que combina visión artificial, embeddings multimodales y búsqueda vectorial semántica. Permite buscar ropa por texto, por imagen o por foto de inspiración, gestionar un armario personal por usuario y guardar favoritos, todo con recomendaciones generadas por un agente de IA.

---

## Características

- **Búsqueda híbrida por texto** — combina similitud visual (CLIP), semántica multilingüe y matching por palabras clave
- **Búsqueda por imagen** — encuentra prendas visualmente similares usando CLIP
- **Búsqueda combinada** — imagen base + modificador de texto (ej. "pero en azul, más formal")
- **Inspiración** — sube cualquier foto, el agente la analiza y recomienda prendas similares del catálogo sin añadirla
- **Mi armario** — espacio personal por usuario: sube prendas propias, el agente las describe y quedan indexadas en un namespace privado de Pinecone
- **Similares desde el armario** — busca en el catálogo prendas que combinan con cualquier prenda del armario personal
- **Favoritos** — guarda prendas con ♥ en una wishlist persistente (localStorage)
- **Filtros por categoría** — filtra los resultados por tipo de prenda sin nueva búsqueda
- **Modal de detalle** — vista ampliada de cada prenda con descripción completa y categorías
- **Carga masiva** — script `upload_batch.py` para poblar el catálogo desde una carpeta de imágenes

---

## Stack técnico

| Componente | Tecnología |
|---|---|
| Agente IA | pydantic-ai + Ollama (`gemma3:12b`) |
| Embeddings visuales | CLIP `clip-ViT-B-32` (CPU) — 512d |
| Embeddings semánticos | `paraphrase-multilingual-mpnet-base-v2` (CPU) — 768d |
| Base de datos vectorial | Pinecone serverless (AWS us-east-1) |
| Backend | FastAPI + uvicorn |
| Frontend | HTML + CSS + JS (archivos separados) |

> **Nota sobre GPU**: CLIP y el modelo semántico corren en CPU para ceder la VRAM completa a Ollama. Con una GPU de ≥8 GB y sin necesidad de ejecutar el agente simultáneamente, se pueden mover a GPU cambiando `device="cpu"` en `pinec/embeddings.py`.

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
│       └── training_examples.json    # Ejemplos de entrenamiento para el agente
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
        ├── upload_batch.py           # Carga masiva de imágenes al catálogo
        ├── rutes/
            ├── analizar_api.py
            ├── armario_api.py
            ├── dependencies.py
            ├── descubrir_api.py
            ├── imagen_api.py
            ├── models.py
            ├── recomendar_api.py
            ├── utils.py
        ├── static/
        │   ├── index.html            # Estructura HTML de la interfaz
        │   ├── styles.css            # Estilos (variables, layout, cards, modal)
        │   └── app.js                # Lógica de la interfaz (búsquedas, armario, modal)
        └── pinec/
            ├── index.py              # Creación de índices Pinecone
            ├── embeddings.py         # Modelos CLIP y multilingual
            ├── upload_data.py        # Subida a ambos índices Pinecone
            └── search.py             # Búsqueda híbrida (visual + semántica + keyword)
```

## Instalación

### Pasos
1. **Entorno**: `python3 -m venv venv && source venv/bin/activate`
2. **Dependencias**: `pip install -r requirements.txt`
3. **Variables**: Configura tu `.env` en la raíz

### Configuración (`.env`)
```env
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=gemma3:12b
PINECONE_APIKEY=tu_api_key
PINECONE_INDEX_NAME=buscador
PINECONE_REGION=us-east-1
TRAINING_EXAMPLES_PATH=data/examples/training_examples.json

`OLLAMA_KEEP_ALIVE` controla cuánto tiempo Ollama retiene el modelo en VRAM tras la última llamada. Usar `0` para liberar VRAM inmediatamente; `5m` es el valor recomendado para uso interactivo.

---

## Arrancar el servidor

```bash
source venv/bin/activate
cd src/python
python3 api.py
```

La interfaz estará disponible en [http://localhost:8000](http://localhost:8000)

Los ejemplos de `data/examples/training_examples.json` se cargan automáticamente para guiar el estilo de respuesta del agente. No es fine tuning real, pero mantiene la consistencia de formato en las respuestas.


## API REST

### Búsqueda y catálogo

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/recomendar/texto?query=...&top_k=5` | Búsqueda híbrida por texto |
| `POST` | `/recomendar/texto` | Búsqueda híbrida por texto (form data) |
| `POST` | `/recomendar/imagen` | Búsqueda visual por imagen subida |
| `POST` | `/recomendar/combinado` | Imagen base + modificador de texto (`alpha` controla el peso) |
| `POST` | `/descubrir` | Analiza foto + recomienda similares (sin indexar) |
| `POST` | `/analizar` | Analiza imagen y la añade al catálogo |
| `GET` | `/imagen/{filepath}` | Sirve imágenes desde cualquier subdirectorio de `data/` |

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

- **Visual**: CLIP traduce la query a inglés y busca por similitud de embedding de imagen
- **Semántico**: modelo multilingüe entiende el español directamente sin traducción
- **Keyword**: boost cuando la query coincide con descripción, categorías o estilo
- **Contextual**: queries como "outfit para una boda" se expanden con Ollama antes de embedear

La búsqueda **combinada** (imagen + texto) mezcla los vectores con un parámetro `alpha` (por defecto `0.7` = 70% imagen, 30% texto).

---

## Armario personal — almacenamiento

Cada usuario tiene un espacio privado identificado por un UUID generado en el navegador:

| Tipo | Ubicación |
|---|---|
| Metadatos | `data/armarios/{user_id}.json` |
| Imágenes | `data/images/armario/{user_id}_{item_id}.{ext}` |
| Vectores | Pinecone `buscador-semantico`, namespace `armario-{user_id}` |

---

## Carga masiva de imágenes

Para poblar el catálogo desde una carpeta de imágenes (JPG, PNG, WEBP):

```bash
cd src/python

# Primera carga
python3 upload_batch.py --carpeta ../../data/fotos_tienda

# Reanudar una carga interrumpida (omite las ya procesadas)
python3 upload_batch.py --carpeta ../../data/fotos_tienda --reanudar

# Limitar el número de imágenes por ejecución
python3 upload_batch.py --carpeta ../../data/fotos_tienda --limite 50 --reanudar

# Orden aleatorio (mayor variedad en lotes pequeños)
python3 upload_batch.py --carpeta ../../data/fotos_tienda --limite 50 --reanudar --aleatorio
```

El script registra las imágenes procesadas en `.upload_log.json` dentro de la carpeta para evitar duplicados entre ejecuciones. Fuerza CPU en embeddings para no competir con Ollama por VRAM.

---

## Reindexación

Para re-analizar las imágenes del catálogo con el agente y regenerar ambos índices:

```bash
cd src/python
python3 reindexar.py --todo          # Reindexar todo (pide confirmación)
python3 reindexar.py "Captura*"      # Solo imágenes cuyo nombre coincida con el patrón
python3 reindexar.py                 # Solo imágenes con nombre sin slug legible
```

### Eliminar una entrada de Pinecone

```python
# Desde src/python/
from pinec.index import crear_index, crear_index_semantico

dense    = crear_index()
semantic = crear_index_semantico()

item_id = "id-del-vector-a-eliminar"
dense.delete(ids=[item_id], namespace="mi-espacio")
semantic.delete(ids=[item_id], namespace="mi-espacio")
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
javac src/java/ImageDescriptionAgent.java
java -cp src/java ImageDescriptionAgent data/images/eleganza-beige-satin-gown.png
```

```java
ImageDescriptionAgent agent = new ImageDescriptionAgent(Paths.get("/ruta/a/ProyectoIA"));
String json = agent.describeImage(Paths.get("data/images/eleganza-beige-satin-gown.png"));
```

---

## Modelos descargados automáticamente

Al arrancar la API por primera vez se descargan:

- `clip-ViT-B-32` (~340 MB) — embeddings visuales, cargado en CPU
- `paraphrase-multilingual-mpnet-base-v2` (~280 MB) — embeddings semánticos, cargado en CPU

Los modelos se cachean en `~/.cache/huggingface/`.
