import streamlit as st
import psycopg2
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_groq import ChatGroq

# Configuración de página con favicon y layout amplio
st.set_page_config(
    page_title="NYC Spatial AI Agent | PostGIS",
    page_icon="🗺️",
    layout="wide"
)

# Estilos CSS avanzados para modernizar la interfaz (Azul Tech & Sombras Glassmorphism)
st.markdown("""
    <style>
    /* Gradient de encabezado */
    .stAppHeader {
        background: rgba(255, 255, 255, 0.8);
    }
    
    /* Contenedor principal */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 950px;
    }

    /* Estilo para los títulos principales */
    .main-title {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #1e3a8a, #2563eb, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    
    .sub-title {
        color: #475569;
        font-size: 1.05rem;
        margin-bottom: 25px;
    }

    /* Tarjetas personalizadas de diálogo/modal */
    .stCard {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border: 1px solid #bae6fd;
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(14, 165, 233, 0.08);
    }
    .stCard h4 { margin-top: 0; color: #0369a1; font-weight: 700; }
    .stCard p { color: #334155; font-size: 0.92em; margin-bottom: 0; }

    /* Respuesta destacada del asistente con marco azul brillante */
    .assistant-response-box {
        background-color: #f8fafc;
        border-left: 5px solid #2563eb;
        border-radius: 8px;
        padding: 18px;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.08);
        margin-top: 10px;
        color: #0f172a;
    }
    
    /* Badge decorativo */
    .badge-postgis {
        background-color: #dbeafe;
        color: #1e40af;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

DATABASE_URL = "postgresql://neondb_owner:npg_GDoHi7IUaE8m@ep-bitter-mud-aylkic0b-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require"

# System Prompt para delimitar el alcance del agente
PREFIX_PROMPT = """Eres un asistente especializado única y exclusivamente en la base de datos geoespacial de la ciudad de Nueva York (PostGIS).

Si la pregunta del usuario no está relacionada con la base de datos de Nueva York, análisis espacial, barrios, datos demográficos, bloques censales o criminalidad de NYC, responde amablemente indicando:
"Este es un asistente especializado exclusivamente en información y análisis geoespacial de la ciudad de Nueva York (PostGIS). Por favor, realiza una consulta relacionada con barrios, geografía o datos espaciales de NYC."
"""

# Diálogo / Modal de bienvenida
@st.dialog("🏛️ Centro de Control Geoespacial — NYC PostGIS")
def modal_bienvenida():
    st.write("**Bienvenido al sistema inteligente de analítica espacial para la ciudad de Nueva York.**")
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="stCard">
            <h4>🌐 Cobertura de Datos</h4>
            <p>Acceso directo a capas raster y vectoriales: barrios, bloques censales, calles y crímenes registrados en NYC.</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="stCard">
            <h4>⚡ Motor IA + SQL Espacial</h4>
            <p>Transforma preguntas en español a consultas PostGIS complejas (ST_Contains, ST_Distance, ST_Buffer, etc.).</p>
        </div>
        """, unsafe_allow_html=True)
        
    st.divider()
    if st.button("🚀 Iniciar Sesión de Análisis", type="primary", use_container_width=True):
        st.session_state.bienvenida_mostrada = True
        st.rerun()

if "bienvenida_mostrada" not in st.session_state:
    modal_bienvenida()

# Barra lateral estilizada con métricas
with st.sidebar:
    st.image("https://img.icons8.com/isometric-folders/100/map-marker.png", width=65)
    st.header("⚙️ Panel de Control")
    
    groq_api_key = st.text_input("🔑 Groq API Key", type="password", help="Pega aquí tu clave gsk_...")
    
    st.divider()
    st.subheader("📡 Estado del Sistema")
    st.metric(label="Base de Datos", value="Neon PostgreSQL", delta="PostGIS 3.x", delta_color="normal")
    
    if groq_api_key:
        st.success("API Key cargada", icon="✅")
    else:
        st.warning("Falta API Key", icon="⚠️")
        
    st.divider()
    if st.button("📖 Ver Guía de Inicio", use_container_width=True):
        modal_bienvenida()

# Encabezado Principal
st.markdown('<div class="badge-postgis">📍 PostGIS Spatial Engine Enabled</div>', unsafe_allow_html=True)
st.markdown('<h1 class="main-title">Asistente Analítico PostGIS NYC</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Generación de consultas geoespaciales avanzadas en lenguaje natural</p>', unsafe_allow_html=True)

# Sugerencias rápidas (Quick Prompts)
st.write("💡 **Consultas rápidas de ejemplo:**")
col_a, col_b, col_c = st.columns([1, 1, 1])

prompt_sugerido = None
with col_a:
    if st.button("📊 Homicidios en NYC", use_container_width=True):
        prompt_sugerido = "¿Cuántos homicidios hay registrados en la base de datos de NYC?"
with col_b:
    if st.button("🏘️ Barrios de Brooklyn", use_container_width=True):
        prompt_sugerido = "¿Cuáles son los barrios ubicados en Brooklyn?"
with col_c:
    if st.button("🗽 Vecindarios destacados", use_container_width=True):
        prompt_sugerido = "Muestra 5 barrios aleatorios con su respectivo condado (borough)"

# Historial de Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            st.markdown(f'<div class="assistant-response-box">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.write(msg["content"])

# Captura de entrada (chat o sugerencia)
prompt = st.chat_input("Escribe tu consulta espacial (ej: ¿Qué barrios limitan con Manhattan?)...") or prompt_sugerido

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    if not groq_api_key:
        resp = "⚠️ **Atención:** Por favor, ingresa tu **Groq API Key** en el panel lateral para ejecutar la consulta."
        st.session_state.messages.append({"role": "assistant", "content": resp})
        with st.chat_message("assistant"):
            st.warning(resp)
    else:
        try:
            db = SQLDatabase.from_uri(DATABASE_URL)
            llm = ChatGroq(
                model="llama3-70b-8192",
                groq_api_key=groq_api_key,
                temperature=0
            )
            agent_executor = create_sql_agent(
                llm, 
                db=db, 
                agent_type="tool-calling", 
                prefix=PREFIX_PROMPT,
                verbose=False
            )
            
            with st.spinner("🔍 Analizando consulta e interactuando con PostGIS..."):
                result = agent_executor.invoke({"input": prompt})
                response = result["output"]
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.markdown(f'<div class="assistant-response-box">🔹 <b>Resultado del Análisis:</b><br><br>{response}</div>', unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"❌ Error al procesar la consulta espacial: {e}")
