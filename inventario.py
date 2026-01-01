import streamlit as st
import pandas as pd
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Mi Inventario Pro", layout="centered")

# 1. SIMULACIÓN DE BASE DE DATOS (En un caso real, usarías un CSV o SQL)
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=[
        "ID", "Nombre", "Ubicación", "Contenedor", "Estado", "Fecha"
    ])

st.title("📦 Gestor de Inventario")

# --- VENTANA 1: SELECCIÓN DE UBICACIÓN ---
st.subheader("📍 ¿Dónde estamos?")
ubicaciones = ["Nave A", "Trastero", "Garaje", "Taller"]
ubi_sel = st.selectbox("Selecciona Ubicación", ubicaciones)

# --- VENTANA 2: SELECCIÓN DE CONTENEDOR (Estante/Caja) ---
# Aquí puedes añadir subniveles fácilmente
contenedores = ["Estantería 1", "Estantería 2", "Caja Herramientas", "Balda 3"]
cont_sel = st.selectbox("Selecciona el Contenedor/Caja", contenedores)

st.divider()

# --- VENTANA 3: CARGA RÁPIDA (Solo nombre y foto) ---
with st.expander(f"➕ Añadir objeto a {cont_sel}", expanded=False):
    with st.form("nuevo_objeto"):
        nombre = st.text_input("Nombre del objeto")
        foto = st.camera_input("Tomar foto") # Abre la cámara en el móvil
        
        submitted = st.form_submit_button("Guardar en este lugar")
        
        if submitted and nombre:
            nuevo_registro = {
                "ID": len(st.session_state.db) + 1,
                "Nombre": nombre,
                "Ubicación": ubi_sel,
                "Contenedor": cont_sel,
                "Estado": "Guardado",
                "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([nuevo_registro])], ignore_index=True)
            st.success(f"✅ {nombre} guardado en {cont_sel}")

# --- VENTANA 4: LISTADO FILTRADO ---
st.subheader(f"🔍 Objetos en {cont_sel}")
df_filtrado = st.session_state.db[
    (st.session_state.db['Ubicación'] == ubi_sel) & 
    (st.session_state.db['Contenedor'] == cont_sel)
]

if not df_filtrado.empty:
    for index, row in df_filtrado.iterrows():
        col1, col2 = st.columns([3, 1])
        col1.write(f"**{row['Nombre']}**")
        if col2.button("Sacar", key=f"btn_{row['ID']}"):
            st.info(f"Has sacado: {row['Nombre']}")
            # Aquí iría la lógica para cambiar el estado a 'Fuera'
else:
    st.write("No hay objetos en este contenedor.")