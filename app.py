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
    # Usamos ID para evitar errores de búsqueda
    return client.open_by_key("17YUr7sP7cQgqHofUK7awOQQArQ7wEALTmplD1kkEjNI").sheet1

def cargar_datos():
    try:
        sheet = get_sheet()
        data_str = sheet.acell('A2').value 
        return json.loads(data_str) if data_str else {}
    except:
        return {}

def guardar_datos(data):
    sheet = get_sheet()
    sheet.update_acell('A2', json.dumps(data))

# --- CONFIGURACIÓN DE LA APP ---
st.set_page_config(page_title="App Universitaria", page_icon="🎓", layout="centered")

# CSS para forzar colores en móvil (Evita el fondo blanco en inputs/botones)
st.markdown("""
<style>
    .stApp { background-color: #1A2A3A; }
    h1, h2, h3, p, label, div { color: #FFFFFF !important; }
    input, div[data-baseweb="input"] { background-color: #2E4053 !important; color: white !important; }
    button { background-color: #2E4053 !important; color: white !important; border: 1px solid #4A5568 !important; }
</style>
""", unsafe_allow_html=True)

if 'curso_actual' not in st.session_state: st.session_state.curso_actual = None

# --- DATOS ---
datos = cargar_datos()

# --- LÓGICA DE MENÚ ---
menu = st.sidebar.radio("Navegación 🧭", ["Mis Notas", "Malla Curricular", "Asistencias"])

if menu == "Mis Notas":
    if st.session_state.curso_actual is None:
        st.header("📊 Resumen General")
        if datos:
            for perfil_usuario, cursos in datos.items():
                for nombre_curso, info in cursos.items():
                    # Cálculo rápido de promedio
                    # (Nota: Asumimos que si no hay info, es 0)
                    if st.button(f"📝 {nombre_curso} (Perfil: {perfil_usuario})"):
                        st.session_state.curso_actual = (perfil_usuario, nombre_curso)
                        st.rerun()
        
        st.write("---")
        perfil_nuevo = st.selectbox("Perfil", ["Sebastián", "Dionila"])
        nuevo_curso = st.text_input("Crear nuevo curso:")
        if st.button("Añadir Curso"):
            if nuevo_curso:
                if perfil_nuevo not in datos: datos[perfil_nuevo] = {}
                datos[perfil_nuevo][nuevo_curso] = {"parcial": 0.0, "final": 0.0, "notas_practicas": [0.0, 0.0, 0.0, 0.0], "rendidas": {"parcial": False, "final": False, "practicas": [False, False, False, False]}}
                guardar_datos(datos)
                st.rerun()

    else:
        perfil_usuario, curso = st.session_state.curso_actual
        if st.button("⬅️ Volver al Resumen"):
            st.session_state.curso_actual = None
            st.rerun()
            
        st.subheader(f"Editando: {curso} ({perfil_usuario})")
        
        # Inputs con Checkbox de "Rendido"
        col1, col2 = st.columns(2)
        with col1:
            parcial = st.number_input("Nota Parcial", min_value=0.0, max_value=20.0, value=float(datos[perfil_usuario][curso]["parcial"]), step=0.5)
            rendido_p = st.checkbox("¿Parcial rendido?", value=datos[perfil_usuario][curso]["rendidas"]["parcial"])
        with col2:
            final = st.number_input("Nota Final", min_value=0.0, max_value=20.0, value=float(datos[perfil_usuario][curso]["final"]), step=0.5)
            rendido_f = st.checkbox("¿Final rendido?", value=datos[perfil_usuario][curso]["rendidas"]["final"])
        
        num_practicas = st.number_input("¿Cuántas prácticas?", min_value=1, max_value=10, value=len(datos[perfil_usuario][curso]["notas_practicas"]), step=1)
        
        # Ajuste de listas
        if len(datos[perfil_usuario][curso]["notas_practicas"]) != num_practicas:
            datos[perfil_usuario][curso]["notas_practicas"] = [0.0] * num_practicas
            datos[perfil_usuario][curso]["rendidas"]["practicas"] = [False] * num_practicas
        
        notas_practicas = []
        rendidas_practicas = []
        for i in range(num_practicas):
            val = st.number_input(f"Práctica {i+1}", min_value=0.0, max_value=20.0, value=float(datos[perfil_usuario][curso]["notas_practicas"][i]), step=0.5)
            rend = st.checkbox(f"¿Práctica {i+1} rendida?", value=datos[perfil_usuario][curso]["rendidas"]["practicas"][i], key=f"p{i}")
            notas_practicas.append(val)
            rendidas_practicas.append(rend)
        
        # Guardar estado
        datos[perfil_usuario][curso].update({
            "parcial": parcial, "final": final, "notas_practicas": notas_practicas,
            "rendidas": {"parcial": rendido_p, "final": rendido_f, "practicas": rendidas_practicas}
        })
        guardar_datos(datos)
        
        # CÁLCULOS DE SALVACIÓN
        st.write("---")
        st.subheader("📈 Análisis y Salvación")
        
        puntos_acumulados = 0
        peso_acumulado = 0
        
        if rendido_p:
            puntos_acumulados += parcial * 0.30
            peso_acumulado += 0.30
        if rendido_f:
            puntos_acumulados += final * 0.30
            peso_acumulado += 0.30
            
        peso_practica = 0.40 / num_practicas
        for i in range(num_practicas):
            if rendidas_practicas[i]:
                puntos_acumulados += notas_practicas[i] * peso_practica
                peso_acumulado += peso_practica
        
        peso_faltante = 1.0 - peso_acumulado
        
        if peso_acumulado > 0:
            promedio_actual = puntos_acumulados / peso_acumulado
            st.write(f"Promedio actual con lo rendido: **{promedio_actual:.2f}**")
        
        if peso_faltante > 0:
            puntos_necesarios = 10.5 - puntos_acumulados
            nota_necesaria = puntos_necesarios / peso_faltante
            if nota_necesaria > 20:
                st.error(f"¡Matemáticamente imposible! Necesitas {nota_necesaria:.2f} en lo que falta.")
            else:
                st.warning(f"Necesitas un promedio de **{nota_necesaria:.2f}** en lo que falta para llegar al 10.5.")
        elif puntos_acumulados >= 10.5:
            st.success("¡Ya estás aprobado!")
        else:
            st.error("Ya diste todo y no llegaste al 10.5.")
