import streamlit as st
from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_groq import ChatGroq

# Configuración inicial de la ventana
st.set_page_config(
    page_title="NYC PostGIS Spatial AI Engine",
    page_icon="🗺️",
    layout="wide"
)

# Estilos CSS avanzados para una interfaz SIG estilizada
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .main .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2rem;
        max-width: 1050px;
    }

    .hero-badge {
        background: linear-gradient(90deg, #1e3a8a 0%, #0284c7 100%);
        color: #e0f2fe;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        padding: 4px 12px;
        border-radius: 20px;
        display: inline-block;
        margin-bottom: 10px;
        box-shadow: 0 2px 8px rgba(2, 132, 199, 0.25);
    }
    
    .title-tech {
        font-size: 2.1rem;
        font-weight: 700;
        color: #0f172a;
        letter-spacing: -0.025em;
        margin-bottom: 4px;
    }
    
    .subtitle-tech {
        font-size: 0.95rem;
        color: #64748b;
        margin-bottom: 1.5rem;
    }

    .stCard {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.03);
    }
    .stCard h4 { margin-top: 0; color: #0284c7; font-weight: 600; font-size: 0.95rem; }
    .stCard p { color: #475569; font-size: 0.85rem; margin-bottom: 0; }

    .assistant-response-box {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-left: 4px solid #0284c7;
        border-radius: 8px;
        padding: 16px 18px;
        color: #0f172a;
        font-size: 0.93rem;
        line-height: 1.6;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.04);
    }

    [data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }
    </style>
""", unsafe_allow_html=True)

# Carga de credenciales desde el entorno / secrets de Streamlit
DATABASE_URL = st.secrets.get(
    "DATABASE_URL", 
    "postgresql://neondb_owner:npg_GDoHi7IUaE8m@ep-bitter-mud-aylkic0b-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require"
)
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", None)

PREFIX_PROMPT = """Eres un asistente analítico especializado en la base de datos geoespacial de la ciudad de Nueva York (PostGIS).
Responde a las preguntas del usuario generando consultas SQL geoespaciales eficientes en PostGIS y explicando brevemente los resultados en español."""

@st.cache_resource
def get_db_connection(url):
    if "sslmode=" not in url:
        connector = "&" if "?" in url else "?"
        url += f"{connector}sslmode=require&keepalives=1&keepalives_idle=30"
    
    engine = create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_timeout=30
    )
    return SQLDatabase(engine)

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

@st.dialog("🗺️ Centro de Control Geoespacial — NYC PostGIS")
def modal_bienvenida():
    st.write("Entorno analítico para la ejecución de consultas espacio-temporales sobre PostgreSQL/PostGIS.")
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="stCard">
            <h4>Capa Vectorial y Tabular</h4>
            <p>Acceso a datos de límites de barrios, bloques censales, red vial y registros delictivos de NYC.</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="stCard">
            <h4>Procesamiento Espacial</h4>
            <p>Evaluación de predicados y funciones (ST_Contains, ST_Distance, ST_Intersects, ST_Buffer).</p>
        </div>
        """, unsafe_allow_html=True)
        
    st.divider()
    if st.button("🚀 Iniciar Panel de Análisis", type="primary", use_container_width=True):
        st.session_state.bienvenida_mostrada = True
        st.rerun()

if "bienvenida_mostrada" not in st.session_state:
    modal_bienvenida()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar simplificado (sin pedir API Key)
with st.sidebar:
    st.title("⚙️ Sistema")
    
    st.caption("INFRAESTRUCTURA DE DATOS")
    st.text("BD: Neon PostgreSQL")
    st.text("Motor Espacial: PostGIS 3.x")
    st.text("LLM: openai/gpt-oss-20b")
    st.text("Estado: En línea 🟢")
        
    st.divider()
    
    if st.button("🧹 Limpiar historial", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    if st.button("📖 Guía de uso", use_container_width=True):
        modal_bienvenida()

# Encabezado
st.markdown('<div class="hero-badge">POSTGIS ENGINE // NYC SPATIAL DATA</div>', unsafe_allow_html=True)
st.markdown('<div class="title-tech">Asistente de Analítica Espacial NYC</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle-tech">Traducción de consultas complejas en lenguaje natural a consultas SQL con PostGIS</div>', unsafe_allow_html=True)

# Botones de sugerencias
col_a, col_b, col_c = st.columns(3)

prompt_sugerido = None
with col_a:
    if st.button("📊 Homicidios en NYC", use_container_width=True):
        prompt_sugerido = "¿Cuántos homicidios hay registrados en la base de datos de NYC?"
with col_b:
    if st.button("🏘️ Barrios de Brooklyn", use_container_width=True):
        prompt_sugerido = "¿Cuáles son los barrios ubicados en Brooklyn?"
with col_c:
    if st.button("🗽 Vecindarios por Borough", use_container_width=True):
        prompt_sugerido = "Muestra 5 barrios aleatorios con su respectivo condado (borough)"

st.divider()

# Historial de Chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            st.markdown(f'<div class="assistant-response-box">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.write(msg["content"])

prompt = st.chat_input("Escribe tu consulta espacial (ej: ¿Qué barrios limitan con Manhattan?)...") or prompt_sugerido

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    if not GROQ_API_KEY:
        resp = "Error de servidor: No se ha configurado la variable GROQ_API_KEY en los Secrets de Streamlit Cloud."
        st.session_state.messages.append({"role": "assistant", "content": resp})
        with st.chat_message("assistant"):
            st.error(resp)
    else:
        if not es_consulta_valida(prompt):
            respuesta_fuera_de_tema = (
                "Consulta no procesada: Este sistema está restringido al análisis geoespacial "
                "y tabular de la ciudad de Nueva York (PostGIS). Ajusta tu consulta para incluir términos "
                "relacionados con barrios, geografía, vialidad o crímenes en NYC."
            )
            st.session_state.messages.append({"role": "assistant", "content": respuesta_fuera_de_tema})
            with st.chat_message("assistant"):
                st.markdown(f'<div class="assistant-response-box">{respuesta_fuera_de_tema}</div>', unsafe_allow_html=True)
        else:
            try:
                db = get_db_connection(DATABASE_URL)
                
                llm = ChatGroq(
                    model="openai/gpt-oss-20b",
                    groq_api_key=GROQ_API_KEY,
                    temperature=0
                )
                
                agent_executor = create_sql_agent(
                    llm, 
                    db=db, 
                    agent_type="tool-calling", 
                    prefix=PREFIX_PROMPT,
                    verbose=False
                )
                
                with st.spinner("⚡ Procesando consulta con GPT-OSS 20B e interactuando con PostGIS..."):
                    result = agent_executor.invoke({"input": prompt})
                    response = result["output"]
                
                st.session_state.messages.append({"role": "assistant", "content": response})
                with st.chat_message("assistant"):
                    st.markdown(f'<div class="assistant-response-box">{response}</div>', unsafe_allow_html=True)
                    
            except Exception as e:
                st.error(f"Error al procesar la consulta espacial: {e}")
