# ProyectoIA - Agentes de moda y búsqueda de productos

Proyecto híbrido Python/Java para trabajar con un catálogo de moda. Tiene dos flujos principales:

- describir imágenes de prendas con un modelo multimodal servido por Ollama;
- buscar productos del catálogo por texto, filtros, imagen, embeddings semánticos locales o Pinecone.

La salida de los agentes es JSON para que pueda consumirse desde terminal, tests o una aplicación Java.

## Estructura del proyecto

```text
.
├── data
│   ├── catalog
│   │   └── products.json
│   ├── examples
│   │   └── training_examples.jsonl
│   ├── images
│   │   └── ...
│   └── pruebaBBDD.json
├── src
│   ├── java
│   │   ├── ImageDescriptionAgent.java
│   │   ├── ProductSearchAgent.java
│   │   └── PythonAgentUtils.java
│   └── python
│       ├── cli
│       │   ├── embeddings_cli.py
│       │   ├── image_description_cli.py
│       │   └── product_search_cli.py
│       ├── core
│       │   └── config.py
│       ├── models
│       │   ├── fashion.py
│       │   └── product.py
│       ├── repositories
│       │   └── product_catalog.py
│       ├── search
│       │   └── ranking.py
│       └── services
│           ├── embeddings.py
│           └── image_description.py
├── tests
│   └── test_product_search.py
├── embedding.py
├── requirements.txt
└── README.md
```

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Para las rutas con Ollama necesitas tener Ollama levantado y los modelos descargados:

```bash
ollama serve
ollama pull gemma4:e4b
ollama pull nomic-embed-text-v2-moe:latest
```

## Configuración

El proyecto carga variables desde `.env` si existe. Valores por defecto:

```text
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=gemma4:e4b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text-v2-moe:latest
PINECONE_INDEX_NAME=buscador
PINECONE_NAMESPACE=mi-espacio
PINECONE_EMBEDDING_MODEL=llama-text-embed-v2
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
```

Para Pinecone añade también `PINECONE_APIKEY` o `PINECONE_API_KEY`.

## Descriptor de imágenes

El descriptor analiza una imagen de ropa y devuelve:

```json
{
  "descripcion": "...",
  "categoria": ["camiseta", "casual"],
  "estilo": "casual deportivo"
}
```

Uso con una imagen concreta:

```bash
python3 src/python/cli/image_description_cli.py data/images/classic-red-logo-tee.jpg
```

Si no pasas ruta, usa `data/images/classic-red-logo-tee.jpg`:

```bash
python3 src/python/cli/image_description_cli.py
```

Este flujo depende de Ollama y de un modelo compatible con imágenes. Los ejemplos de `data/examples/training_examples.jsonl` se cargan automáticamente para guiar el estilo de la respuesta; no es fine tuning real.

## Buscador de productos

El buscador lee `data/catalog/products.json` y devuelve un JSON con:

- `query`: consulta final utilizada;
- `filters`: filtros aplicados;
- `embedding_model` y `embedding_cache`: modelo y caché usados para embeddings;
- `total`: número de resultados devueltos;
- `results`: lista de productos con puntuación semántica y `score_embedding`;
- `image_description`: aparece al buscar desde imagen.

### Búsqueda semántica

El buscador usa siempre embeddings.

Flujo interno:

- convierte la consulta en un embedding con Ollama;
- crea o reutiliza la caché de embeddings del catálogo;
- compara la consulta contra cada producto con similitud coseno;
- aplica filtros opcionales;
- descarta resultados por debajo de `--semantic-threshold`;
- ordena de mayor a menor similitud.

```bash
python3 src/python/cli/product_search_cli.py "calzado para evento elegante" --semantic-threshold 0.25 --limite 5
```

Este flujo necesita Ollama. Si Ollama no está disponible, el CLI termina con error porque no existe fallback textual.

### Filtros

Los filtros no buscan por sí solos: solo acotan una búsqueda semántica.

```bash
python3 src/python/cli/product_search_cli.py "camiseta roja" --marca Adidas
python3 src/python/cli/product_search_cli.py "calzado elegante" --categoria zapatos
python3 src/python/cli/product_search_cli.py "look casual" --carpeta camisetas
```

Si no pasas consulta ni imagen, el CLI termina con error:

```text
Indica una busqueda o una imagen. Los filtros solo acotan una busqueda semantica.
```

### Búsqueda por imagen

Primero describe la imagen y luego utiliza la descripción, categorías y estilo como consulta de búsqueda:

```bash
python3 src/python/cli/product_search_cli.py --imagen data/images/classic-red-logo-tee.jpg --limite 3
```

La búsqueda por imagen no acepta texto adicional. Si quieres acotar resultados, usa filtros como `--marca`, `--categoria` o `--carpeta`.

## Embeddings locales y Pinecone

Generar o refrescar caché local de embeddings:

```bash
python3 src/python/cli/product_search_cli.py --build-embeddings
python3 src/python/cli/product_search_cli.py "zapatillas blancas" --refresh-embeddings
python3 src/python/cli/embeddings_cli.py --build-local
python3 src/python/cli/embeddings_cli.py --build-local --refresh
```

Sincronizar el catálogo con Pinecone:

```bash
python3 src/python/cli/embeddings_cli.py --sync-pinecone
```

Buscar directamente en Pinecone:

```bash
python3 src/python/cli/embeddings_cli.py --pinecone-query "camiseta roja" --top-k 5
```

`embedding.py` es un script de ejemplo más directo para crear el índice Pinecone, subir `data/pruebaBBDD.json` y lanzar una búsqueda simple. El flujo mantenido y parametrizable está en `src/python/cli/embeddings_cli.py`.

## Integración Java

Compilar los wrappers Java:

```bash
mkdir -p build/classes
javac -d build/classes src/java/PythonAgentUtils.java src/java/ImageDescriptionAgent.java src/java/ProductSearchAgent.java
```

Descriptor de imagen:

```bash
java -cp build/classes ImageDescriptionAgent data/images/classic-red-logo-tee.jpg
```

Buscador:

```bash
java -cp build/classes ProductSearchAgent camiseta adidas roja
```

Uso desde una aplicación Java:

```java
ImageDescriptionAgent imageAgent = new ImageDescriptionAgent(Paths.get("/ruta/a/ProyectoIA"));
String descriptionJson = imageAgent.describeImage(Paths.get("data/images/classic-red-logo-tee.jpg"));

ProductSearchAgent searchAgent = new ProductSearchAgent(Paths.get("/ruta/a/ProyectoIA"));
String searchJson = searchAgent.search("camiseta adidas roja");
String imageSearchJson = searchAgent.searchByImage(Paths.get("data/images/classic-red-logo-tee.jpg"));
```

## Qué hace cada clase

### Python

- `models.product.Product`: representa un producto del catálogo. Normaliza entradas desde JSON con `from_dict`, acepta `categoria` o `categorias`, `folder` o `carpeta`, e `image` o `imagen`.
- `models.product.SearchResult`: representa un resultado semántico con producto, puntuación final y `score_embedding`. `to_dict` prepara el JSON de salida.
- `models.fashion.DescripcionRopa`: modelo Pydantic de la respuesta del descriptor de imagen. Obliga a devolver `descripcion`, `categoria` y `estilo`.
- `services.embeddings.EmbeddingError`: excepción propia para errores de Ollama, caché de embeddings o Pinecone.
- `tests.test_product_search.ProductSearchTest`: suite de pruebas unitarias del ranking semántico: orden por similitud, filtros, umbral mínimo, ausencia de embeddings y texto usado para embeddings.

### Java

- `ImageDescriptionAgent`: wrapper Java del CLI `image_description_cli.py`. Ejecuta Python con timeout de 120 segundos y devuelve el JSON como `String`.
- `ProductSearchAgent`: wrapper Java del CLI `product_search_cli.py`. Permite buscar por texto, filtros básicos o imagen y devuelve el JSON como `String`.
- `PythonAgentUtils`: utilidad compartida para lanzar procesos Python desde Java, fijar el directorio del proyecto, esperar con timeout, leer stdout/stderr y convertir errores de proceso en `IOException`.

## Módulos importantes

- `core.config`: centraliza rutas del proyecto, rutas por defecto de datos y variables de entorno.
- `repositories.product_catalog`: carga el catálogo JSON y lo convierte a objetos `Product`.
- `search.ranking`: aplica filtros, calcula similitud semántica y ordena resultados.
- `services.image_description`: crea el agente Pydantic AI con Ollama, carga ejemplos de estilo y describe imágenes.
- `services.embeddings`: genera embeddings con Ollama, mantiene caché local, calcula similitud coseno y gestiona Pinecone.
- `cli.image_description_cli`: punto de entrada por terminal para describir imágenes.
- `cli.product_search_cli`: punto de entrada por terminal para búsqueda semántica por texto o imagen.
- `cli.embeddings_cli`: punto de entrada para caché local y Pinecone.

## Pruebas y comprobaciones

Tests unitarios:

```bash
python3 -m unittest tests/test_product_search.py
```

Comprobaciones con servicios externos:

```bash
python3 src/python/cli/image_description_cli.py data/images/classic-red-logo-tee.jpg
python3 src/python/cli/product_search_cli.py "zapatos elegantes"
python3 src/python/cli/product_search_cli.py "camiseta roja" --marca Adidas
python3 src/python/cli/embeddings_cli.py --sync-pinecone
```

## Estado verificado

En este entorno se han verificado correctamente:

- `python3 -m unittest tests/test_product_search.py`
- error controlado cuando no se pasa consulta ni imagen;
- error controlado cuando se mezcla texto con `--imagen`;
- compilación Java de `PythonAgentUtils`, `ImageDescriptionAgent` y `ProductSearchAgent`.

Las rutas de imagen, búsqueda semántica real y Pinecone requieren servicios externos activos. Si Ollama no está accesible, la búsqueda falla porque el proyecto ya no tiene búsqueda por palabras de respaldo.
