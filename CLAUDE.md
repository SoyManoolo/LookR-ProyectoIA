SearchMO Playbook — CLAUDE.md para construir tu propio buscador
Plantilla open-source publicada por Mercadona Tech como parte del componente sociedad del Modelo de Mercadona. Licencia MIT. Adáptalo a tu catálogo y a tu negocio.

Cómo usarlo: guarda este fichero como CLAUDE.md en la raíz de un repositorio Python nuevo y abre Claude Code en ese directorio. Pídele que lea las reglas y empiece por la Fase 0.


0. Stack obligatorio
Estas son las dependencias concretas que el agente debe instalar. Cualquier sustitución requiere justificación explícita en un ADR (Architecture Decision Record).

Búsqueda lexical: tantivy-py (Rust embebido, MIT)
Embeddings: intfloat/multilingual-e5-small exportado a ONNX INT8 (MIT)
Inferencia ONNX: onnxruntime (MIT)
Learning-to-rank: catboost con loss YetiRank (Apache 2.0)
Cómputo numérico: numpy, scikit-learn (BSD)
Lenguaje: Python 3.10+

NO se usan: Elasticsearch/OpenSearch, bases de datos vectoriales (Pinecone, Weaviate, Qdrant, pgvector), GPU, ni servicios externos de cobro recurrente. Toda la inferencia corre en CPU dentro del propio proceso.


1. Performance budgets (latencia p99)
Cada componente tiene un presupuesto de latencia que NO puede superarse. CI ejecuta benchmark en cada PR. Si un componente excede su budget, el PR se bloquea.

Normalización (unicode + lowercase + tokenize): 0,5 ms
BM25 retrieval (Tantivy, top-100): 3 ms
Embedding encode (e5-small INT8, 384d): 5 ms
Cosine similarity (query vs todo el catálogo): 1 ms
Merge RRF + bitset filter: 1 ms
Feature computation (14 features): 1 ms
CatBoost predict (~60 candidatos): 1 ms
Serialización JSON: 0,5 ms
Total pipeline sin cache: 15 ms
Total pipeline con cache: 2 ms
Autocomplete (Trie lookup): 0,5 ms

Reglas de enforcement:

CI ejecuta el benchmark contra un índice de referencia congelado en cada PR.
Si cualquier componente supera su budget, el check falla y el PR no se mergea.
Los benchmarks corren en runner dedicado para evitar ruido.
El budget total (15 ms) incluye margen de orquestación.


2. Reglas de arquitectura (no negociables)
A1. Motor lexical embebido, no Elasticsearch
Regla: Tantivy embebido, in-process. Elasticsearch/OpenSearch prohibido.

Por qué: Para catálogos de menos de 100.000 documentos, un clúster externo es overkill. Tantivy corre in-process con ~20 MB de RAM, sin red, sin operación dedicada. Diferencia: ~150 USD/mes vs >2.000 USD/mes solo en infra de búsqueda.
A2. Embeddings en RAM, no Vector DB
Regla: Los embeddings se almacenan como matriz NumPy en RAM. Pinecone, Weaviate, Qdrant, pgvector prohibidos.

Por qué: Un catálogo típico (5.000-50.000 documentos × 384 dimensiones) cabe en memoria de un solo proceso (6-60 MB). Una multiplicación de matriz NumPy resuelve la similitud en <1 ms. No hay justificación para añadir una base de datos especializada.
A3. Un solo índice maestro + bitsets por tenant
Regla: UN índice Tantivy maestro con todo el catálogo. El filtro por tenant (tienda, marca, región) se aplica vía bitset AND post-retrieval. NO crear un índice por tenant.

Por qué: Un bitset de 5.000 productos ocupa ~625 bytes. Mil tenants ocupan ~600 KB totales. Actualizar un surtido es swap de un bitset. Comparado con miles de índices físicos: x1.000 menos de almacenamiento, x1.000 menos de complejidad operativa.
A4. CatBoost YetiRank, no otro algoritmo LTR
Regla: El modelo LTR es CatBoost con loss YetiRank, formato nativo .cbm. NO XGBoost, LightGBM ni red neuronal sin competición previa con resultado >0,5% MRR.

Por qué: Competición de 5 modelos con 5-fold CV temporal: CatBoost YetiRank ganó con menor varianza y mejor inferencia. ONNX export del LTR pierde optimizaciones del runtime nativo.
A5. e5-small, no e5-base ni mayor
Regla: Embeddings con intfloat/multilingual-e5-small (384d) ejecutado vía ONNX Runtime INT8.

Por qué: Para texto de producto (5-10 palabras de media), e5-small captura toda la semántica necesaria. e5-base duplica la latencia (5 ms → 10 ms) sin mejora medible de calidad.
A6. BM25 con b=0 para documentos cortos
Regla: Tantivy BM25 con k1=0,5, b=0,0 (o b=0,001 si la implementación no permite b=0 exacto).

Por qué: El parámetro b controla normalización por longitud. Con documentos cortos y uniformes (nombres de producto, ~5 palabras de media), normalizar es contraproducente: penaliza productos con nombres descriptivos. Grid search con 175 configuraciones lo confirma.
A7. NO motor de reglas (pin/boost) sobre el LTR
Regla: No hay motor de reglas que modifique el ranking del LTR. Excepción única: la "hide rule" para moderación de contenido (requisito legal, no de relevancia).

Por qué: Auditorías reales muestran que >70% de los pin rules tienen IDs que ya no existen, y los boosts redundan con popularity (Spearman ~0,9 contra purchase count). Aplicar boosts sobre LTR es doble-conteo: el modelo ya aprendió esos pesos.
A8. Corrección ortográfica con fuzzy contra el índice, no SymSpell
Regla: Corrección de typos vía fuzzy_query en Tantivy (edit distance ≤2 contra el índice real). NO SymSpell con diccionario genérico.

Por qué: SymSpell con diccionario genérico produce ~62% de correcciones falsas en contexto de producto. Fuzzy contra el índice solo sugiere productos que existen, eliminando falsos positivos.
A9. Lanza solo con un idioma, añade el resto cuando lo valides
Regla: El primer release soporta UN idioma. Idiomas adicionales requieren cross-lingual retrieval validado con MRR >0,60 contra ground truth en ese idioma.

Por qué: Los usuarios buscan en su idioma de uso, no en el idioma de la app. Lanzar más idiomas sin validación cross-lingual produce queries en idioma A contra catálogo en idioma B, con MRR <0,30.
A10. Artefactos ML en almacenamiento de objetos, no en la imagen Docker
Regla: Modelo CatBoost (.cbm), embeddings ONNX (.onnx), índice Tantivy y features precomputadas viven en almacenamiento de objetos versionado. Los pods los descargan al arrancar.

Por qué: Si el modelo va en Docker, cada retrain semanal requiere rebuild + redeploy. Con artefactos externos: el pod detecta nueva versión, descarga, hace swap atómico en caliente. Desacopla ciclo de vida del código del ciclo de vida del modelo.


3. Reglas de Machine Learning (no negociables)
ML1. IPW obligatorio en cada retrain
Regla: Todo reentrenamiento del LTR DEBE usar Inverse Propensity Weighting: weight = 1 / log2(position + 1). Sin IPW, el retrain se rechaza automáticamente.

Por qué: Los clics tienen position bias: el primer resultado se clica ~6× más que el quinto, sea relevante o no. Sin IPW, el modelo aprende a reforzar sus propios errores (feedback loop). En ~3 retrains, la diversidad colapsa.
ML2. Walk-forward CV obligatorio (nunca random)
Regla: Validación temporal: train semanas 1-3, test semana 4. NUNCA random shuffle de clics.

Por qué: Los clics tienen estructura temporal (estacionalidad, lanzamientos, campañas). Random CV mezcla futuro con pasado, inflando MRR offline en 5-10%. Walk-forward replica producción.
ML3. Golden set estático obligatorio
Regla: Mantener un golden set de 500 queries con relevance judgments manuales. NO modificar nunca (sí añadir queries nuevas, no eliminar ni cambiar juicios). Toda evaluación de modelo incluye MRR y NDCG sobre el golden set.

Por qué: El golden set es la única defensa contra feedback loop. Si solo evalúas con clics propios, el modelo puede degradar silenciosamente: los clics siguen llegando porque el usuario no tiene alternativa.
ML4. Guardrail −2%: ningún modelo peor pasa
Regla: Un modelo candidato se RECHAZA si CUALQUIERA de estas métricas cae más de 2% respecto al modelo en producción:

MRR en golden set
NDCG@10 en golden set
MRR en walk-forward test set
NDCG@10 en walk-forward test set

Tres decisiones del pipeline:

PROMOTE si mejora >0,5% en todas las métricas
HOLD si está en rango neutro (-2% a +0,5%) — no se despliega
REJECT si cae >2% en alguna métrica
ML5. Mínimo 50.000 clics para reentrenar
Regla: El pipeline de retrain NO ejecuta si hay menos de 50.000 clics acumulados en las últimas 4 semanas. Abort silencioso con log.

Por qué: Con <50K clics, el modelo no tiene suficientes ejemplos para aprender patrones robustos en cola larga. Mejor mantener el modelo actual que reentrenar con datos sparse.
ML6. feature_spec.json es contrato entre training y serving
Regla: Las features del modelo están definidas únicamente en config/feature_spec.json. El código de training lee de ahí. El código de serving lee de ahí. CI verifica paridad.

Por qué: Feature parity es el riesgo principal de cualquier sistema ML en producción. Si training usa log1p(popularity) pero serving usa popularity raw, el modelo produce rankings erróneos silenciosamente.
ML7. Exploration budget del 5%
Regla: En producción, el 5% de las queries reciben 2-3 resultados aleatorios en posiciones [3, 5, 7]. Los resultados explorados se marcan en click_events con metadata.explored=true.

Por qué: Sin exploración, el modelo solo recibe feedback de los resultados que él mismo posicionó arriba. Productos nuevos nunca reciben clics y se quedan atrapados. El 5% es suficiente para generar datos no sesgados sin degradar la experiencia del 95%.
ML8. Nunca deploy automático de modelo
Regla: El pipeline produce un candidato. La decisión PROMOTE/HOLD/REJECT la toma el pipeline automáticamente, PERO el deploy real espera 1 hora antes de activarse. Cualquier persona del equipo puede abortar en esa ventana.

Por qué: Un modelo aprobado por guardrails automáticos puede tener problemas no capturados por las métricas (sesgo hacia una categoría, queries específicas degradadas). La ventana de 1 hora es el último gate humano.


4. Las cuatro fases del proyecto
Cada fase termina con un experimento canónico, un fichero de evaluación versionado, y una decisión documentada.
Fase 0 — Caracterización del catálogo y las consultas
Objetivo: Entender qué buscan tus usuarios antes de optimizar nada.

Prompt sugerido para Claude Code:

Analiza los datos de catálogo y de consultas en data/raw/. Responde estas preguntas con números: cuántas palabras tiene la consulta media; qué porcentaje contiene tildes; cuál es el vocabulario activo; cuántas consultas distintas hay; qué porcentaje de consultas no devuelve resultados con un BM25 baseline básico. Genera un fichero data/processed/eda.json con todas las métricas.

Decisión al final: ¿Qué normalización aplicar (acentos, mayúsculas, plurales)? ¿Qué porcentaje de consultas son de cola larga? ¿Hay un patrón de búsqueda predominante (1 palabra, 2 palabras, lenguaje natural)?
Fase 1 — Baseline lexical con grid search
Objetivo: Tener un baseline BM25 sólido antes de añadir complejidad.

Prompt sugerido:

Implementa un BM25 sobre Tantivy en src/bm25_index.py. Construye un ground truth a partir de los clics: para cada query, el producto más clicado es el resultado ideal. Ejecuta un grid search sobre k1 ∈ {0,1; 0,3; 0,5; 0,8; 1,0; 1,2; 1,5} y b ∈ {0,0; 0,25; 0,5; 0,75; 1,0}. Reporta MRR y NDCG@10 para cada combinación. Guarda los resultados en data/evaluations/phase1_grid.json.

Decisión al final: ¿Qué configuración BM25 maximiza MRR sobre el ground truth? Para documentos cortos espera b cerca de 0.
Fase 2 — Capa semántica con comparación de modelos
Objetivo: Añadir embeddings y validar que el sistema híbrido (BM25 + semántica) mejora respecto a BM25 solo.

Prompt sugerido:

Compara tres modelos de embeddings: intfloat/multilingual-e5-small, intfloat/multilingual-e5-base y BAAI/bge-m3. Para cada uno, calcula MRR y NDCG@10 (a) usando solo embeddings, (b) usando híbrido con RRF k=60. Mide latencia de encoding p99 en CPU con ONNX Runtime INT8. Guarda en data/evaluations/phase2_embeddings.json.

Decisión al final: ¿Qué modelo gana en la frontera calidad/latencia? ¿Cuánto mejora el sistema híbrido vs BM25 solo (recall@50)?
Fase 3 — Learning-to-rank con competición
Objetivo: Reordenar los candidatos del híbrido con un modelo entrenado.

Prompt sugerido:

Define las features en config/feature_spec.json (BM25 score, embedding similarity, popularity, recency, has_bm25, etc.). Genera training data con IPW (weight = 1/log2(pos+1)) y skip-above. Entrena 5 modelos: CatBoost YetiRank, XGBoost, LightGBM con LambdaRank, una baseline pointwise y una listwise. Usa 5-fold CV walk-forward (3 semanas train, 1 semana test). Reporta MRR ± std, NDCG@10 ± std, feature importance, latencia de inferencia. Guarda en data/evaluations/phase3_ltr.json.

Decisión al final: ¿Qué modelo gana? ¿Cuál es la importancia de cada feature? ¿Hay features con importancia <1% que podemos descartar?


5. Checklist de las 5 decisiones algorítmicas
Para cada decisión, los criterios que te ayudan a aplicarla en tu caso.
D1 — Búsqueda híbrida vs solo lexical / solo semántica
¿Tu vocabulario de catálogo es cerrado y los usuarios escriben siempre con sus términos? → Empieza solo con lexical, añade semántica después.
¿Tus usuarios usan lenguaje natural, sinónimos, descripciones funcionales? → Híbrido desde el día 1.
¿Tienes >5% de consultas sin resultados con solo lexical? → Híbrido obligatorio.
D2 — Índice maestro + bitsets vs índice por tenant
¿Tu catálogo es mayoritariamente común a todos los tenants (tiendas, marcas)? → Índice maestro + bitsets.
¿Cada tenant tiene un catálogo radicalmente distinto? → Índices separados.
¿Tienes <100.000 documentos en total (suma de todos los tenants)? → Bitsets prácticamente seguro.
D3 — Walk-forward vs random CV
¿Tus datos tienen dimensión temporal (clics, ventas, búsquedas)? → Walk-forward obligatorio.
¿Estás validando un modelo de ranking sobre datos de comportamiento? → Walk-forward sin excepción.
¿Random CV en este contexto? → Nunca.
D4 — IPW + exploración
¿Entrenas un modelo a partir de clics? → IPW obligatorio.
¿Quieres dar oportunidad a productos nuevos? → Exploración 5% en posiciones [3, 5, 7].
¿No tienes log de impresiones (solo de clics)? → Reconstrúyelo. Sin log de impresiones no puedes hacer IPW correcto.
D5 — Guardrail automático en deploy
¿Despliegas modelos automáticamente? → Guardrail obligatorio.
¿Umbral estricto (tráfico crítico)? → −2%.
¿Umbral menos estricto (tráfico tolerante)? → −5%.
¿Ventana humana antes del deploy real? → Sí, mínimo 1 hora.


6. Reglas de CI/CD
Lo que DEBE pasar en CI para que un PR se mergee.

C1. Benchmark de latencia (1.000 queries) — falla si cualquier p99 supera su budget.
C2. Contract tests del formato de respuesta — falla si cambia el contrato sin versión nueva.
C3. Feature parity test — verifica que training y serving producen las mismas features con los mismos tipos.
C4. Golden queries MRR/NDCG — falla si caen >2% respecto a la baseline.
C5. ruff format --check y ruff check — sin warnings.
C6. pytest -x --timeout=60 con coverage ≥80% en src/.

Pipeline en orden: C5 + C6 + C2 + C3 + C4 en paralelo, luego C1 (más lento, solo si los anteriores pasan).


7. Reglas generales
G1. Nunca push directo a main. Todo cambio vía PR con CI verde.
G2. feature_spec.json y training_config.json son contratos. Cambiarlos requiere PR dedicado con justificación.
G3. Logs estructurados (JSON) con campos: timestamp, level, component, query (si aplica), latency_ms (si aplica), error (si aplica). Sin print(), sin logs sin estructura.
G4. Click logging es P0. Si se rompe, es incidencia crítica. Sin clics no hay retrain.
G5. Reentrenamiento semanal. Si falla, notificación. No retry automático: un humano investiga.
G6. Artefactos versionados e inmutables. Nunca sobrescribir, siempre versión nueva.
G7. Rollback de emergencia documentado, ejecutable por cualquier miembro del equipo en <30 segundos.


8. Métricas que importan
Calidad del ranking (offline)
MRR (Mean Reciprocal Rank): posición del primer resultado relevante. Más alto es mejor.
NDCG@10 (Normalized Discounted Cumulative Gain): calidad del orden de los 10 primeros. Más alto es mejor.
Recall@50: ¿el resultado relevante está entre los 50 primeros? Más alto es mejor.
No-results rate: % de queries sin resultados. Más bajo es mejor (objetivo <2%).
Calidad del ranking (producción)
CTR top 3: % de búsquedas con clic en posiciones 1-3. Más alto es mejor.
Deep scroll rate: % de búsquedas con clic en posición 21+. Más bajo es mejor.
Reformulation rate: % de búsquedas que el usuario reformula en la misma sesión. Más bajo es mejor.
Revenue per search (north star): ingreso medio por búsqueda. Más alto es mejor.
Latencia
p50, p95, p99 por componente y total.
Budget total: 15 ms p99 sin cache, 2 ms con cache.


Licencia
MIT. 
