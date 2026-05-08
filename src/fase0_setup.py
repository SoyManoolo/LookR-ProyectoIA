import json
import numpy as np
import os

# 1. Asegurar que existan las carpetas de datos (Regla A10)
os.makedirs('data/raw', exist_ok=True)

# 2. Catalogo
# Actualiza tu lista de productos en src/fase0_setup.py
catalogo = [
    {
        "id": "1", 
        "name": "Sweater Azul Punto Fino", 
        "description": "Sweater cerrado de cuello redondo y tejido ligero.", 
        "vibe": "Minimalismo sofisticado, profesional, calma", 
        "contexto": "Oficina, cena ligera, primavera",
        "popularity": 120
    },
    {
        "id": "2", 
        "name": "Sweater Blanco Lana Trenzada", 
        "description": "Sweater cerrado grueso de invierno con diseño de ochos.", 
        "vibe": "Tradición artesanal, acogedor, rústico",
        "contexto": "Escapada montaña, invierno frío",
        "popularity": 85
    },
    {
        "id": "3", 
        "name": "Cardigan Gris Lana", 
        "description": "Cárdigan abierto gris con botones de madera y bolsillos.", 
        "vibe": "Versatilidad urbana, comodidad, atemporal",
        "contexto": "Día a día, look capas, otoño",
        "popularity": 250
    }
]

# 3. Simulación de clics con IPW (Regla ML1)
# El peso corrige el sesgo de posición: weight = 1 / log2(pos + 1)
clics = [
    {"query": "sweater azul", "product_id": "1", "position": 1, "weight": 1.0},
    {"query": "cardigan gris", "product_id": "3", "position": 1, "weight": 1.0},
    {"query": "sweater lana", "product_id": "2", "position": 2, "weight": 0.63}, # 1/log2(2+1)
    {"query": "ropa gris", "product_id": "3", "position": 1, "weight": 1.0}
]

# 4. Guardar archivos en data/raw/
with open('data/raw/catalog.json', 'w') as f:
    json.dump(catalogo, f, indent=2)

with open('data/raw/clicks.json', 'w') as f:
    json.dump(clics, f, indent=2)

print("✅ Fase 0: Catálogo y Clics (con IPW) generados con éxito.")
