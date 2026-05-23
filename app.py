import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# --- CONFIGURACIÓN DE CONEXIÓN A GOOGLE SHEETS ---
def get_sheet():
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, 
            ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive'])
    client = gspread.authorize(creds)
    # Abre tu hoja de cálculo por nombre
    return client.open("BaseDatosNotas").sheet1

def cargar_datos():
    try:
        sheet = get_sheet()
        data_str = sheet.acell('A2').value # Leemos el JSON guardado en A2
        return json.loads(data_str) if data_str else {}
    except:
        return {}

def guardar_datos(data):
    sheet = get_sheet()
    sheet.update_acell('A2', json.dumps(data)) # Guardamos el JSON en A2

# --- CONFIGURACIÓN DE LA APP ---
st.set_page_config(page_title="App Universitaria", page_icon="🎓", layout="centered")

if 'curso_actual' not in st.session_state:
    st.session_state.curso_actual = None

perfil = st.sidebar.radio("👤 ¿Quién usa la app?", ["Sebastián", "Dionila"])
color_fondo = "#1A2A3A" if perfil == "Sebastián" else "#F8BBD0"
color_texto = "#FFFFFF" if perfil == "Sebastián" else "#1E1E1E"

st.markdown(f"""<style>.stApp {{ background-color: {color_fondo}; }} h1, h2, h3, p, label {{ color: {color_texto} !important; }}</style>""", unsafe_allow_html=True)

datos = cargar_datos()
if perfil not in datos:
    datos[perfil] = {}
    guardar_datos(datos)

# --- MENÚ Y LÓGICA ---
menu = st.sidebar.radio("Navegación 🧭", ["Mis Notas", "Malla Curricular", "Asistencias"])

if menu == "Mis Notas":
    # 1. Dashboard (Si no hay curso seleccionado)
    if st.session_state.curso_actual is None:
        st.header("📊 Resumen General")
        if datos[perfil]:
            for nombre_curso, info in datos[perfil].items():
                promedio = (info["parcial"]*0.3) + (info["final"]*0.3) + (sum(info["notas_practicas"])/len(info["notas_practicas"])*0.4)
                estado = "✅" if promedio >= 10.5 else "❌"
                if st.button(f"{estado} {nombre_curso} | Promedio: {promedio:.1f}"):
                    st.session_state.curso_actual = nombre_curso
                    st.rerun()
        
        st.write("---")
        nuevo_curso = st.text_input("Crear nuevo curso:")
        if st.button("Añadir Curso"):
            if nuevo_curso and nuevo_curso not in datos[perfil]:
                datos[perfil][nuevo_curso] = {"parcial": 0.0, "final": 0.0, "notas_practicas": [0.0, 0.0, 0.0, 0.0]}
                guardar_datos(datos)
                st.rerun()

    # 2. Vista Edición
    else:
        curso = st.session_state.curso_actual
        if st.button("⬅️ Volver al Resumen"):
            st.session_state.curso_actual = None
            st.rerun()
            
        st.subheader(f"Editando: {curso}")
        col1, col2 = st.columns(2)
        with col1:
            parcial = st.number_input("Nota Parcial", min_value=0.0, max_value=20.0, value=float(datos[perfil][curso]["parcial"]), step=0.5)
        with col2:
            final = st.number_input("Nota Final", min_value=0.0, max_value=20.0, value=float(datos[perfil][curso]["final"]), step=0.5)
        
        num_practicas = st.number_input("¿Cuántas prácticas?", min_value=1, max_value=10, value=len(datos[perfil][curso]["notas_practicas"]), step=1)
        if len(datos[perfil][curso]["notas_practicas"]) != num_practicas:
            datos[perfil][curso]["notas_practicas"] = [0.0] * num_practicas
        
        notas_practicas = []
        for i in range(num_practicas):
            val = st.number_input(f"Práctica {i+1}", min_value=0.0, max_value=20.0, value=float(datos[perfil][curso]["notas_practicas"][i]), step=0.5)
            notas_practicas.append(val)
        
        datos[perfil][curso].update({"parcial": parcial, "final": final, "notas_practicas": notas_practicas})
        guardar_datos(datos)
        st.success("¡Datos guardados en la nube! ☁️")
