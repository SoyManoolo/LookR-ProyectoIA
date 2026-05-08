import streamlit as st
import os
from agent import process_sense_experience 

# 1. Configuración de la interfaz
st.set_page_config(page_title="Sense Barcelona", page_icon="✨", layout="centered")

# Estilo personalizado para mejorar la estética de la demo
st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        height: 3em;
        background-color: #ff4b4b;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("✨ Sense Discovery")
st.subheader("Tu ADN de moda en Barcelona")
st.markdown("---")

# 2. Configuración de Preferencias (Sidebar)
with st.sidebar:
    st.header("👤 Perfil de Usuario")
    categorias = [
        "Womens clothing", "Mens clothing", "Jewelry", "Bags and luggage", 
        "Shoes", "Beauty", "Home", "Furniture", "Electronics"
    ]
    # Selección de categorías
    selected_cats = st.multiselect("Categorías Preferidas", categorias, default=["Womens clothing"])
    
    if len(selected_cats) > 5:
        st.error("⚠️ Máximo 5 categorías.")
    
    st.markdown("---")
    board_name = st.text_input("Board Activo", "Barcelona Summer")
    st.info(f"Guardando en: **{board_name}**")

# 3. Captura de Imagen
fuente = st.radio("Origen de la imagen:", ("📸 Cámara", "🖼️ Galería"), horizontal=True)

if fuente == "📸 Cámara":
    imagen_data = st.camera_input("Captura el ADN de la prenda")
else:
    imagen_data = st.file_uploader("Sube una foto de tu prenda", type=['jpg', 'jpeg', 'png'])

# 4. Ejecución del Agente
if imagen_data:
    # Guardamos la imagen temporalmente para que el agente la procese
    nombre_para_agente = "foto_demo"
    archivo_fisico = f"{nombre_para_agente}.jpg"
    
    with open(archivo_fisico, "wb") as f:
        f.write(imagen_data.getbuffer())
    
    st.success("📸 Imagen cargada correctamente")

    if st.button("🚀 ANALIZAR CON SENSE"):
        with st.spinner("🧠 Sense está extrayendo el ADN de la prenda..."):
            try:
                # LLAMADA CORREGIDA: Sin asyncio.run si la función es def normal
                # Pasamos el nombre base que espera el agente
                process_sense_experience(nombre_para_agente)
                
                st.balloons()
                st.success(f"✅ ¡Análisis completado y añadido a {board_name}!")
                
                # Espacio para mostrar resultados
                st.markdown("### 🔍 Análisis de Estilo")
                st.info("Revisa la terminal de la laptop para ver el desglose técnico y los matches detallados.")
                
            except Exception as e:
                # Si el error persiste, probamos a llamar con await por si fuera async
                st.error(f"❌ Error en el proceso: {e}")
                st.warning("Asegúrate de que la API (uvicorn) esté corriendo en el puerto 8000.")

st.markdown("---")
st.caption("Sense v1.0 | Techstars Demo Mode | Barcelona 2026")
