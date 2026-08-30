import streamlit as st
import psycopg2
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_groq import ChatGroq

# Configuración de página
st.set_page_config(
    page_title="NYC Spatial AI Agent | PostGIS",
    page_icon="🗺️",
    layout="wide"
)

# Estilos CSS ligeros y enfocados exclusivamente en componentes personalizados
st.markdown("""
    <style>
    /* Estilos para tarjetas informativas */
    .stCard {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 10px;
    }
    .stCard h4 { margin-top: 0; color: #38bdf8; font-weight: 700; }
    .stCard p { color: #cbd5e1; font-size: 0.9em; margin-bottom: 0; }

    /* Estilo para las respuestas del asistente */
    .assistant-response-box {
        background-color: #0f172a;
        border-left: 4px solid #0284c7;
        border-radius: 6px;
        padding: 16px;
        margin-top: 8px;
        color: #f8fafc;
    }
    
    /* Badge superior */
    .badge-postgis {
        background-color: #1e3a8a;
        color: #93c5fd;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# Recuperar URL desde secrets si está disponible, o usar fallback
DATABASE_URL = st.secrets.get(
    "DATABASE_URL", 
    "postgresql://neondb_owner:npg_GDoHi7IUaE8m@ep-bitter-mud-aylkic0b-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require"
)

# System Prompt
PREFIX_PROMPT = """Eres un asistente analítico especializado en la base de datos geoespacial de la ciudad de Nueva York (PostGIS).
Responde a las preguntas del usuario generando consultas SQL geoespaciales eficientes en PostGIS y explicando brevemente los resultados en español."""

@st.cache_resource
def get_db_connection(url):
    return SQLDatabase.from_uri(url)

def es_consulta_valida(prompt: str) -> bool:
    palabras_clave = [
        "barrio", "barrios", "nyc", "nueva york", "new york", "distrito", "crimen", 
        "homicidio", "homicidios", "calle", "calles", "polígono", "poligono", 
        "ubicación", "ubicacion", "postgis", "coordenada", "coordenadas", "borough", 
        "manhattan", "brooklyn", "queens", "bronx", "staten", "vecindario", 
        "vecindarios", "espacial", "geografía", "geografia", "mapa", "bloque", "censal"
    ]
    prompt_lower = prompt.lower()
    return any(palabra in prompt_lower for palabra in palabras_clave)

# Modal de bienvenida
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

if "messages" not in st.session_state:
    st.session_state.messages = []

# Panel Lateral
with st.sidebar:
    st.header("🗺️ Panel de Control")
    
    groq_api_key = st.text_input("🔑 Groq API Key", type="password", help="Pega aquí tu clave gsk_...")
    
    st.divider()
    st.subheader("📡 Estado del Sistema")
    st.metric(label="Base de Datos", value="Neon PostgreSQL", delta="PostGIS 3.x", delta_color="normal")
    
    if groq_api_key:
        st.success("API Key cargada", icon="✅")
    else:
        st.warning("Falta API Key", icon="⚠️")
        
    st.divider()
    
    if st.button("🗑️ Limpiar Conversación", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    if st.button("📖 Ver Guía de Inicio", use_container_width=True):
        modal_bienvenida()

# Encabezado Principal
st.markdown('<div class="badge-postgis">📍 PostGIS Spatial Engine Enabled</div>', unsafe_allow_html=True)
st.title("Asistente Analítico PostGIS NYC")
st.caption("Generación de consultas geoespaciales avanzadas en lenguaje natural")

st.divider()

# Sugerencias rápidas
st.write("💡 **Consultas rápidas de ejemplo:**")
col_a, col_b, col_c = st.columns(3)

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
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            st.markdown(f'<div class="assistant-response-box">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.write(msg["content"])

# Entrada de consulta
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
        if not es_consulta_valida(prompt):
            respuesta_fuera_de_tema = (
                "Este es un asistente especializado exclusivamente en información y análisis geoespacial "
                "de la ciudad de Nueva York (PostGIS). Por favor, realiza una consulta relacionada con barrios, "
                "geografía, criminalidad o datos espaciales de NYC."
            )
            st.session_state.messages.append({"role": "assistant", "content": respuesta_fuera_de_tema})
            with st.chat_message("assistant"):
                st.markdown(f'<div class="assistant-response-box">{respuesta_fuera_de_tema}</div>', unsafe_allow_html=True)
        else:
            try:
                db = get_db_connection(DATABASE_URL)
                
                llm = ChatGroq(
                    model="llama-3.3-70b-versatile",
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
