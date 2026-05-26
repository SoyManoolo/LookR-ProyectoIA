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
        ├── upload_batch.py           # Carga masiva de imágenes al catálogo
        ├── static/
        │   ├── index.html            # HTML puro — 5 paneles + modal (sin CSS ni JS inline)
        │   ├── styles.css            # Estilos completos: variables, layout, cards, skeleton, modal, armario, filtros
        │   └── app.js                # Toda la lógica JS: búsquedas, wishlist, armario, modal, filtros por categoría
        └── pinec/
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
- GPU NVIDIA recomendada (CUDA 12.x) para Ollama

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
OLLAMA_KEEP_ALIVE=5m
PINECONE_APIKEY=tu_api_key_aqui
```

`OLLAMA_KEEP_ALIVE` controla cuánto tiempo Ollama retiene el modelo en VRAM tras la última llamada. Usar `0` para liberar VRAM inmediatamente; `5m` es el valor recomendado para uso interactivo.

---

## Arrancar el servidor

```bash
source venv/bin/activate
cd src/python
python3 api.py
```

La interfaz estará disponible en [http://localhost:8000](http://localhost:8000)

---

## Demo pública con Cloudflare Tunnel

Para exponer el servidor localmente a través de una URL pública sin configuración de red, usa [cloudflared](https://github.com/cloudflare/cloudflared). No requiere cuenta.

### Primera vez — descargar cloudflared

```bash
cd /ruta/a/ProyectoIA
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cloudflared
chmod +x cloudflared
```

### Cada vez que quieras levantar la demo

Abre 3 terminales en orden:

**Terminal 1 — verificar Ollama**
```bash
curl http://localhost:11434/api/tags
# Si no responde:
ollama serve
```

**Terminal 2 — FastAPI**
```bash
cd src/python
source ../../venv/bin/activate
python3 api.py
# Espera: "Application startup complete."
```

**Terminal 3 — túnel**
```bash
./cloudflared tunnel --protocol http2 --url http://localhost:8000
# Aparecerá: https://xxxx.trycloudflare.com  ← URL pública
```

La URL cambia cada vez que reinicias el túnel. Las 3 terminales deben permanecer abiertas mientras dure la demo.

---

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

- `clip-ViT-B-32` (~340 MB) — embeddings visuales, cargado en CPU
- `paraphrase-multilingual-mpnet-base-v2` (~280 MB) — embeddings semánticos, cargado en CPU

Los modelos se cachean en `~/.cache/huggingface/`.

---

## Cheatsheet de comandos

Referencia rápida de los comandos más usados.

### Entorno
```bash
# Activar entorno virtual (siempre primero)
cd /ruta/a/ProyectoIA
source venv/bin/activate
```

### Ollama
```bash
# Verificar si está corriendo
curl http://localhost:11434/api/tags

# Arrancar (si no está corriendo)
ollama serve

# Ver modelos descargados
ollama list

# Liberar VRAM
kill $(pgrep ollama)
```

### Servidor FastAPI
```bash
# Arrancar
cd src/python
source ../../venv/bin/activate
python3 api.py

# Ver qué proceso ocupa el puerto 8000
ss -tlnp | grep 8000

# Liberar el puerto 8000
kill $(lsof -t -i:8000)
```

### Demo pública
```bash
# Levantar túnel (desde la raíz del proyecto)
./cloudflared tunnel --protocol http2 --url http://localhost:8000
```

### Subir fotos al catálogo
```bash
cd src/python
source ../../venv/bin/activate

# Subir todas las fotos de una carpeta
python3 upload_batch.py --carpeta ../../data/fotos_kaggle

# Subir con límite
python3 upload_batch.py --carpeta ../../data/fotos_kaggle --limite 50

# Reanudar una carga interrumpida
python3 upload_batch.py --carpeta ../../data/fotos_kaggle --reanudar

# Orden aleatorio para mayor variedad
python3 upload_batch.py --carpeta ../../data/fotos_kaggle --limite 50 --reanudar --aleatorio
```

### Pinecone — mantenimiento
```python
# Desde src/python/ con el entorno activo: python3
from pinec.index import crear_index, crear_index_semantico

dense    = crear_index()
semantic = crear_index_semantico()

# Eliminar un vector por ID
dense.delete(ids=["id-aqui"], namespace="mi-espacio")
semantic.delete(ids=["id-aqui"], namespace="mi-espacio")

# Eliminar por filtro de metadatos
semantic.delete(filter={"categoria": {"$in": ["categoria-a-borrar"]}}, namespace="mi-espacio")
```
