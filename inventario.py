import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
import base64

# --- CONFIGURACIÓN DE TUS ENLACES ---
# La URL de tu Google Apps Script (el puente para Drive)
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzABmkQBkLv0ZxtqvoKXhabiGYbvJyq8SbYRE9MsROdE5_zZin4UVYZ5sKw5KxXgfMo/exec"
# La URL de tu Google Sheet (Asegúrate de que sea EDITABLE por cualquiera con el link)
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1dFBk0k1X_MjAqIeQEbHi77OdeFP2_9bCktzg3gR9OZ0/edit?usp=sharing"

# Configuración de página móvil
st.set_page_config(page_title="Inventario Pro", layout="centered")

# --- CONEXIÓN CON TU EXCEL ---
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    # ttl=0 obliga a la app a no usar caché y leer los cambios reales del Excel cada vez
    return conn.read(spreadsheet=SPREADSHEET_URL, ttl=0)

# Cargamos los datos actuales
try:
    df = cargar_datos()
except Exception as e:
    st.error(f"Error al conectar con Google Sheets: {e}")
    st.stop()

st.title("📦 Mi Inventario Organizado")

# --- VENTANA 1: JERARQUÍA DE UBICACIÓN ---
st.subheader("📍 ¿Dónde estamos?")
col1, col2, col3 = st.columns(3)

with col1:
    ubi_sel = st.selectbox("Ubicación", ["Nave", "Trastero", "Garaje"])

with col2:
    mueble_sel = st.selectbox("Mueble/Estante", ["Estantería A", "Armario 1", "Suelo"])

with col3:
    cont_sel = st.selectbox("Contenedor/Caja", ["Caja 1", "Caja 2", "Sin Caja"])

st.divider()

# --- VENTANA 2: CARGA RÁPIDA (Solo nombre y foto) ---
# Hereda automáticamente la ubicación y contenedor seleccionados arriba
with st.expander(f"➕ Añadir objeto a: {cont_sel}", expanded=False):
    with st.form("nuevo_registro", clear_on_submit=True):
        nombre = st.text_input("Nombre del objeto")
        foto_file = st.camera_input("Hacer Foto")
        
        btn_guardar = st.form_submit_button("Guardar en Drive y Excel")

        if btn_guardar and nombre and foto_file:
            with st.spinner("Subiendo foto a Drive..."):
                try:
                    # Convertir imagen a base64 para enviarla al script de Apps Script
                    img_base64 = base64.b64encode(foto_file.getvalue()).decode()
                    
                    # Enviar al Script de Google para guardar en Drive
                    res = requests.post(SCRIPT_URL, json={
                        "base64": img_base64,
                        "type": foto_file.type,
                        "name": f"{nombre}.jpg"
                    })
                    
                    if res.status_code == 200:
                        url_drive = res.json().get("url")
                        
                        # Crear la nueva fila (Asegúrate de que las columnas coincidan con el Excel)
                        nueva_fila = pd.DataFrame([{
                            "ID": len(df) + 1,
                            "Nombre": nombre,
                            "Ubicación": ubi_sel,
                            "Mueble": mueble_sel,
                            "Contenedor": cont_sel,
                            "Estado": "Guardado",
                            "Foto_URL": url_drive
                        }])
                        
                        # Guardar en el Google Sheet
                        df_final = pd.concat([df, nueva_fila], ignore_index=True)
                        conn.update(spreadsheet=SPREADSHEET_URL, data=df_final)
                        
                        st.success(f"✅ {nombre} guardado correctamente.")
                        st.rerun()
                    else:
                        st.error("Error en el Script de Drive. Revisa los permisos.")
                except Exception as e:
                    st.error(f"Error durante el proceso: {e}")

# --- VENTANA 3: LISTADO DEL CONTENEDOR SELECCIONADO ---
st.subheader(f"🔍 Contenido en {cont_sel}")

# Filtramos los objetos que coinciden con nuestra selección de arriba
# Asegúrate de que los nombres de columna coincidan exactamente con tu Excel
items = df[(df["Ubicación"] == ubi_sel) & (df["Contenedor"] == cont_sel)]

if not items.empty:
    for _, row in items.iterrows():
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 2, 1])
            with c1:
                # Muestra la imagen directamente desde el link de Drive generado por el Script
                if pd.notnull(row["Foto_URL"]):
                    st.image(row["Foto_URL"], width=100)
            with c2:
                st.write(f"**{row['Nombre']}**")
                st.caption(f"Estado: {row['Estado']}")
            with c3:
                # Acción para sacar el objeto
                if st.button("Sacar", key=f"btn_{row['ID']}"):
                    df.loc[df["ID"] == row["ID"], "Estado"] = "Fuera"
                    conn.update(spreadsheet=SPREADSHEET_URL, data=df)
                    st.toast(f"{row['Nombre']} retirado.")
                    st.rerun()
else:
    st.info("No hay objetos en este contenedor.")


