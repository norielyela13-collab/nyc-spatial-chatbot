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

# Estilos CSS con paleta en tonalidades de azul y negro (Dark Theme)
st.markdown("""
    <style>
    /* Fondo principal en azul muy oscuro / negro */
    .stApp {
        background-color: #0b0f19;
        color: #f1f5f9;
    }
    
    .stAppHeader {
        background: rgba(11, 15, 25, 0.8);
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 950px;
    }

    /* Título principal con gradiente de cian y azul vibrante */
    .main-title {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8, #60a5fa, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }

    .sub-title {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-bottom: 25px;
    }

    /* Tarjetas del modal e información en tonos azul noche */
    .stCard {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    }
    .stCard h4 { margin-top: 0; color: #38bdf8; font-weight: 700; }
    .stCard p { color: #cbd5e1; font-size: 0.92em; margin-bottom: 0; }

    /* Contenedor de respuestas del asistente en azul oscuro resaltado con cian */
    .assistant-response-box {
        background-color: #111827;
        border-left: 4px solid #38bdf8;
        border-radius: 8px;
        padding: 18px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
        margin-top: 10px;
        color: #f3f4f6;
    }

    /* Etiqueta / Badge en tonos azul profundo */
    .badge-postgis {
        background-color: #1e3a8a;
        color: #93c5fd;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 10px;
        border: 1px solid #1d4ed8;
    }

    /* Personalización del Sidebar en tonos más oscuros */
    [data-testid="stSidebar"] {
        background-color: #030712;
        border-right: 1px solid #1f2937;
    }
    </style>
""", unsafe_allow_html=True)

# Recuperar URL desde secrets si está disponible, o usar fallback
DATABASE_URL = st.secrets.get(
    "DATABASE_URL", 
    "postgresql://neondb_owner:npg_GDoHi7IUaE8m@ep-bitter-mud-aylkic0b-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require"
)

# System Prompt enfocado para el Agente SQL
PREFIX_PROMPT = """Eres un asistente analítico especializado en la base de datos geoespacial de la ciudad de Nueva York (PostGIS).
Responde a las preguntas del usuario generando consultas SQL geoespaciales eficientes en PostGIS y explicando brevemente los resultados en español."""

# Optimización: Caché de la conexión a la base de datos
@st.cache_resource
def get_db_connection(url):
    return SQLDatabase.from_uri(url)

# Filtro previo (Guardrail): Valida palabras clave o contexto geoespacial antes de llamar al agente SQL
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

# Inicializar historial de chat si no existe
if "messages" not in st.session_state:
    st.session_state.messages = []

# Barra lateral estilizada con métricas y control de limpieza
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
    
    # Botón para limpiar el chat
    if st.button("🗑️ Limpiar Conversación", use_container_width=True, type="secondary"):
        st.session_state.messages = []
        st.rerun()

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

# Renderizado del Historial de Chat
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
        # VALIDACIÓN PREVIA (Evita gasto inútil de API y llamadas a BD)
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
                # Recuperar o reutilizar conexión en caché
                db = get_db_connection(DATABASE_URL)
                
                # Modelo actualizado a Llama 3.3 Versatile
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
