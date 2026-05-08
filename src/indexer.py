import os
import json
import tantivy

# 1. Definimos el esquema según la Regla A1
schema_builder = tantivy.SchemaBuilder()
schema_builder.add_text_field("id", stored=True)
schema_builder.add_text_field("name", stored=True, tokenizer_name="default")
schema_builder.add_text_field("description", stored=True, tokenizer_name="default")
schema_builder.add_unsigned_field("popularity", stored=True)
schema = schema_builder.build()

# 2. Creamos el índice físico en data/index (Regla A10)
index_path = "data/index"
os.makedirs(index_path, exist_ok=True)
index = tantivy.Index(schema, path=index_path)

def ejecutar_indexacion():
    # Leemos los datos de la Fase 0
    with open("data/raw/catalog.json", "r") as f:
        productos = json.load(f)

    writer = index.writer()
    for p in productos:
        writer.add_document(tantivy.Document(
            id=p["id"],
            name=p["name"],
            description=p["description"],
            popularity=p["popularity"]
        ))
    
    writer.commit()
    print(f"✅ Índice creado con {len(productos)} productos.")

if __name__ == "__main__":
    ejecutar_indexacion()
