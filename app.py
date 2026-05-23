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

if 'curso_actual' not in st.session_state: st.session_state.curso_actual = None

# --- SELECCIÓN DE PERFIL ---
perfil = st.sidebar.radio("👤 ¿Quién usa la app?", ["Sebastián", "Dionila"])
color_fondo = "#1A2A3A" if perfil == "Sebastián" else "#F8BBD0"
color_texto = "#FFFFFF" if perfil == "Sebastián" else "#1E1E1E"

st.markdown(f"""
<style>
    .stApp {{ background-color: {color_fondo}; }}
    h1, h2, h3, p, label, div {{ color: {color_texto} !important; }}
    input, div[data-baseweb="input"] {{ background-color: #2E4053 !important; color: white !important; }}
    button {{ background-color: #2E4053 !important; color: white !important; border: 1px solid #4A5568 !important; }}
</style>
""", unsafe_allow_html=True)

# --- DATOS ---
datos = cargar_datos()
if perfil not in datos:
    datos[perfil] = {}
    guardar_datos(datos)

# --- LÓGICA DE MENÚ ---
menu = st.sidebar.radio("Navegación 🧭", ["Mis Notas", "Malla Curricular", "Asistencias"])

if menu == "Mis Notas":
    # 1. Dashboard (Muestra solo los cursos del perfil seleccionado)
    if st.session_state.curso_actual is None:
        st.header("📊 Resumen General")
        if datos[perfil]:
            for nombre_curso, info in datos[perfil].items():
                # Actualizar cursos antiguos que no tienen 'rendidas'
                if "rendidas" not in info:
                    num_prac = len(info.get("notas_practicas", [0, 0, 0, 0]))
                    info["rendidas"] = {"parcial": False, "final": False, "practicas": [False] * num_prac}
                
                promedio = (info.get("parcial", 0)*0.3) + (info.get("final", 0)*0.3) + (sum(info.get("notas_practicas", [0]))/len(info.get("notas_practicas", [1]))*0.4)
                estado = "✅" if promedio >= 10.5 else "❌"
                if st.button(f"{estado} {nombre_curso} | Promedio referencial: {promedio:.1f}"):
                    st.session_state.curso_actual = nombre_curso
                    st.rerun()
        
        st.write("---")
        nuevo_curso = st.text_input("Crear nuevo curso:")
        if st.button("Añadir Curso"):
            if nuevo_curso and nuevo_curso not in datos[perfil]:
                datos[perfil][nuevo_curso] = {
                    "parcial": 0.0, "final": 0.0, "notas_practicas": [0.0, 0.0, 0.0, 0.0], 
                    "rendidas": {"parcial": False, "final": False, "practicas": [False, False, False, False]}
                }
                guardar_datos(datos)
                st.rerun()

    # 2. Vista Edición
    else:
        curso = st.session_state.curso_actual
        if st.button("⬅️ Volver al Resumen"):
            st.session_state.curso_actual = None
            st.rerun()
            
        st.subheader(f"Editando: {curso}")
        
        # Actualizar cursos antiguos antes de renderizar
        if "rendidas" not in datos[perfil][curso]:
            num_prac_actuales = len(datos[perfil][curso].get("notas_practicas", [0,0,0,0]))
            datos[perfil][curso]["rendidas"] = {"parcial": False, "final": False, "practicas": [False] * num_prac_actuales}
            guardar_datos(datos)

        col1, col2 = st.columns(2)
        with col1:
            parcial = st.number_input("Nota Parcial", min_value=0.0, max_value=20.0, value=float(datos[perfil][curso]["parcial"]), step=0.5)
            rendido_p = st.checkbox("¿Parcial rendido?", value=datos[perfil][curso]["rendidas"]["parcial"])
        with col2:
            final = st.number_input("Nota Final", min_value=0.0, max_value=20.0, value=float(datos[perfil][curso]["final"]), step=0.5)
            rendido_f = st.checkbox("¿Final rendido?", value=datos[perfil][curso]["rendidas"]["final"])
        
        num_practicas = st.number_input("¿Cuántas prácticas?", min_value=1, max_value=10, value=len(datos[perfil][curso]["notas_practicas"]), step=1)
        
        if len(datos[perfil][curso]["notas_practicas"]) != num_practicas:
            datos[perfil][curso]["notas_practicas"] = [0.0] * num_practicas
            datos[perfil][curso]["rendidas"]["practicas"] = [False] * num_practicas
        
        notas_practicas = []
        rendidas_practicas = []
        for i in range(num_practicas):
            val = st.number_input(f"Práctica {i+1}", min_value=0.0, max_value=20.0, value=float(datos[perfil][curso]["notas_practicas"][i]), step=0.5)
            rend = st.checkbox(f"¿Práctica {i+1} rendida?", value=datos[perfil][curso]["rendidas"]["practicas"][i], key=f"p{i}")
            notas_practicas.append(val)
            rendidas_practicas.append(rend)
        
        datos[perfil][curso].update({
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
        
        st.write(f"Promedio actual acumulado: **{puntos_acumulados:.2f} / 20**")
        
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
