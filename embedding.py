from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
import os
import json

load_dotenv()

apikey = os.getenv("PINECONE_APIKEY")

pc = Pinecone(api_key=apikey)

index_name = "buscador"

if not pc.has_index(index_name):
    pc.create_index_for_model(
        name=index_name,
        cloud="aws",
        region="us-east-1",
        embed={
            "model":"llama-text-embed-v2",
            "field_map":{"text": "descripcion"}
        }
    )

dense_index = pc.Index(index_name)

with open("./data/pruebaBBDD.json", "r", encoding="utf-8") as f:
    ejemplos = json.load(f)

dense_index.upsert_records(namespace="mi-espacio", records=ejemplos)

stats = dense_index.describe_index_stats()
print(stats)

query = "rojo"

results = dense_index.search(
    namespace="mi-espacio",
    top_k= 5, 
    inputs= {"text": query}
)

for hit in results['result']['hits']:
    nombre = hit['fields'].get('nombre', 'N/A')
    desc = hit['fields'].get('descripcion', 'N/A')
    print(f"id: {hit['id']} | score: {round(hit['score'], 2)} | Nombre: {nombre} | Text: {desc[:50]}...")