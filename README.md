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
├── main.py
├── ImageDescriptionAgent.java
├── requirements.txt
└── data
    ├── images
    │   ├── bolso.jpeg
    │   ├── unnamed.png
    │   └── vestido_gala.png
    └── examples
        └── training_examples.jsonl
```

## Probar

```bash
pip install -r requirements.txt
python main.py data/images/bolso.jpeg
```

Si no pasas imagen, usa `data/images/unnamed.png`:

```bash
python main.py
```

## Configuración

Por defecto usa:

```text
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=gemma4:e4b
```

Puedes cambiarlo así:

```bash
OLLAMA_MODEL=tu-modelo python main.py data/images/bolso.jpeg
```

Los ejemplos de `data/examples/training_examples.jsonl` se cargan automáticamente para guiar el estilo de respuesta. No es fine tuning real todavía, pero deja preparado el dataset mínimo para crecer hacia fine tuning o embeddings más adelante.

## Llamar desde Java

La clase `ImageDescriptionAgent` ejecuta `python3 main.py <imagen>` y devuelve el JSON como `String`.

```bash
javac ImageDescriptionAgent.java
java ImageDescriptionAgent data/images/bolso.jpeg
```

Uso dentro de una aplicación Java:

```java
ImageDescriptionAgent agent = new ImageDescriptionAgent(Paths.get("/ruta/a/ProyectoIA"));
String json = agent.describeImage(Paths.get("data/images/bolso.jpeg"));
```
