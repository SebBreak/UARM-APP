import streamlit as st
import json
import os

# --- FUNCIONES ---
def cargar_datos():
    if os.path.exists("datos_notas.json"):
        with open("datos_notas.json", "r") as f:
            try: return json.load(f)
            except: return {}
    return {}

def guardar_datos(data):
    with open("datos_notas.json", "w") as f:
        json.dump(data, f, indent=4)

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="App Universitaria", page_icon="🎓", layout="centered")

# --- ESTADO DE SESIÓN (Memoria de navegación) ---
if 'curso_actual' not in st.session_state:
    st.session_state.curso_actual = None

# --- PERFIL Y COLORES ---
perfil = st.sidebar.radio("👤 ¿Quién usa la app?", ["Sebastián", "Dionila"])
color_fondo = "#1A2A3A" if perfil == "Sebastián" else "#F8BBD0"
color_texto = "#FFFFFF" if perfil == "Sebastián" else "#1E1E1E"

st.markdown(f"""<style>.stApp {{ background-color: {color_fondo}; }} h1, h2, h3, p, label {{ color: {color_texto} !important; }}</style>""", unsafe_allow_html=True)

datos = cargar_datos()
if perfil not in datos:
    datos[perfil] = {}
    guardar_datos(datos)

# --- MENÚ ---
menu = st.sidebar.radio("Navegación 🧭", ["Mis Notas", "Malla Curricular", "Asistencias"])

# --- MÓDULO MIS NOTAS ---
if menu == "Mis Notas":
    
    # 1. VISTA DASHBOARD (Si no hay curso seleccionado)
    if st.session_state.curso_actual is None:
        st.header("📊 Resumen General")
        
        # Mostrar cursos guardados
        if datos[perfil]:
            for nombre_curso, info in datos[perfil].items():
                promedio = (info["parcial"]*0.3) + (info["final"]*0.3) + (sum(info["notas_practicas"])/len(info["notas_practicas"])*0.4)
                estado = "✅" if promedio >= 10.5 else "❌"
                if st.button(f"{estado} {nombre_curso} | Promedio: {promedio:.1f}"):
                    st.session_state.curso_actual = nombre_curso
                    st.rerun()
        else:
            st.write("Aún no tienes cursos guardados.")

        st.write("---")
        nuevo_curso = st.text_input("Crear nuevo curso:")
        if st.button("Añadir Curso"):
            if nuevo_curso and nuevo_curso not in datos[perfil]:
                datos[perfil][nuevo_curso] = {"parcial": 0.0, "final": 0.0, "notas_practicas": [0.0, 0.0, 0.0, 0.0]}
                guardar_datos(datos)
                st.rerun()

    # 2. VISTA EDICIÓN (Cuando eliges un curso)
    else:
        curso = st.session_state.curso_actual
        if st.button("⬅️ Volver al Resumen"):
            st.session_state.curso_actual = None
            st.rerun()
            
        st.subheader(f"Editando: {curso}")
        
        # Lógica de notas (La que ya tenías)
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
        
        # Guardar en JSON
        datos[perfil][curso].update({"parcial": parcial, "final": final, "notas_practicas": notas_practicas})
        guardar_datos(datos)
        
        # Cálculos
        promedio_practicas = sum(notas_practicas) / num_practicas
        nota_final = (parcial * 0.3) + (final * 0.3) + (promedio_practicas * 0.4)
        st.markdown(f"### Nota final actual: **{nota_final:.2f} / 20**")
        
       # --- FASE 3: EL BOTÓN MÁGICO (Calculadora Dinámica) ---
        st.write("---")
        st.subheader("🪄 Calculadora de Salvación Dinámica")
        st.write("Deja en **0.0** las notas que aún no has rendido.")
            
        if st.button("Calcular mi salvación"):
                puntos_acumulados = 0.0
                peso_faltante = 0.0
                
                if parcial > 0: puntos_acumulados += parcial * 0.30
                else: peso_faltante += 0.30
                
                if final > 0: puntos_acumulados += final * 0.30
                else: peso_faltante += 0.30
                
                peso_por_practica = 0.40 / num_practicas
                for nota in notas_practicas:
                    if nota > 0: puntos_acumulados += nota * peso_por_practica
                    else: peso_faltante += peso_por_practica
                        
                puntos_necesarios = 10.5 - puntos_acumulados
                
                if puntos_necesarios <= 0:
                    st.success("¡Relájate! Ya estás aprobado matemáticamente. 🎉")
                elif peso_faltante == 0:
                    st.error("Ya ingresaste todas tus notas y no llegaste a 10.5. 💀")
                else:
                    nota_promedio_necesaria = puntos_necesarios / peso_faltante
                    if nota_promedio_necesaria > 20:
                        st.error(f"Necesitas un promedio de {nota_promedio_necesaria:.2f}. ¡Matemáticamente imposible! 💀")
                    else:
                        st.warning(f"Para aprobar, necesitas un promedio de **{nota_promedio_necesaria:.2f} / 20** en lo que falta.")


elif menu == "Malla Curricular": st.write("Módulo en construcción...")
elif menu == "Asistencias": st.write("Módulo en construcción...")