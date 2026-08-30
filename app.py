import streamlit as st
from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_groq import ChatGroq

# 1. Configuración de la página
st.set_page_config(
    page_title="Asistente PostGIS NYC",
    page_icon="🗺️",
    layout="wide"
)

# 2. Inyección CSS con patrón de CÍRCULOS (Dot Grid) y paleta Verde Esmeralda / Azul Noche
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* FONDO GLOBAL: Patrón de Círculos / Puntos tenue (Dot Grid) */
    .stApp {
        background-color: #f8fafc;
        background-image: radial-gradient(rgba(148, 163, 184, 0.35) 1.5px, transparent 1.5px);
        background-size: 24px 24px;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .main .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1100px;
    }

    /* NAV BAR SUPERIOR COMPACTA */
    .top-navbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 10px 20px;
        margin-bottom: 24px;
        box-shadow: 0 4px 15px -2px rgba(15, 23, 42, 0.04);
    }

    .brand-section {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .brand-icon {
        background: linear-gradient(135deg, #059669 0%, #0d9488 100%);
        color: white;
        width: 38px;
        height: 38px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        box-shadow: 0 4px 10px rgba(5, 150, 105, 0.25);
    }

    .brand-title {
        font-weight: 700;
        font-size: 1.1rem;
        color: #0f172a;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .brand-badge {
        background-color: #f1f5f9;
        color: #475569;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 6px;
        border: 1px solid #cbd5e1;
    }

    .brand-subtitle {
        font-size: 0.78rem;
        color: #64748b;
        margin: 0;
    }

    .status-indicator {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        color: #059669;
        background: #ecfdf5;
        padding: 4px 12px;
        border-radius: 20px;
        border: 1px solid #a7f3d0;
    }

    .status-dot {
        width: 8px;
        height: 8px;
        background-color: #10b981;
        border-radius: 50%;
        display: inline-block;
    }

    /* HEADER CENTRADO HERO */
    .hero-container {
        text-align: center;
        margin: 15px 0 25px 0;
    }

    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: -0.03em;
        margin-bottom: 6px;
    }

    .hero-description {
        font-size: 0.98rem;
        color: #475569;
        max-width: 680px;
        margin: 0 auto;
        line-height: 1.5;
    }

    /* CARDS DE ACCESO RÁPIDO */
    .cards-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
        margin-bottom: 25px;
    }

    .action-card-1 {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
        color: white;
        border-radius: 16px;
        padding: 18px 22px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 8px 20px -4px rgba(49, 46, 129, 0.25);
    }

    .action-card-2 {
        background: linear-gradient(135deg, #064e3b 0%, #047857 100%);
        color: white;
        border-radius: 16px;
        padding: 18px 22px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 8px 20px -4px rgba(4, 120, 87, 0.25);
    }

    .card-info h3 {
        color: #ffffff;
        font-size: 1.05rem;
        font-weight: 700;
        margin: 0 0 4px 0;
    }

    .card-info p {
        color: rgba(255, 255, 255, 0.8);
        font-size: 0.82rem;
        margin: 0;
    }

    .card-action-btn {
        background: rgba(255, 255, 255, 0.15);
        color: white;
        border-radius: 8px;
        padding: 6px 14px;
        font-size: 0.8rem;
        font-weight: 600;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }

    /* TARJETA DE RESPUESTA EN CHAT */
    .assistant-response-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 5px solid #059669;
        border-radius: 14px;
        padding: 18px 22px;
        margin-bottom: 15px;
        box-shadow: 0 8px 20px -4px rgba(15, 23, 42, 0.04);
        color: #1e293b;
        font-size: 0.94rem;
        line-height: 1.6;
    }

    /* FOOTER DISCRETO */
    .footer-credits {
        text-align: center;
        font-size: 0.78rem;
        color: #94a3b8;
        margin-top: 40px;
        padding-top: 20px;
        border-top: 1px solid #e2e8f0;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Credenciales de la base de datos y API
DATABASE_URL = st.secrets.get(
    "DATABASE_URL", 
    "postgresql://neondb_owner:npg_GDoHi7IUaE8m@ep-bitter-mud-aylkic0b-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require"
)
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", None)

PREFIX_PROMPT = """Eres un asistente analítico especializado en la base de datos geoespacial de la ciudad de Nueva York (PostGIS).

INSTRUCCIONES DE SALIDA:
1. Tu respuesta final DEBE SER SIEMPRE una respuesta redactada en lenguaje natural en español explicando detalladamente los hallazgos o datos encontrados.
2. NUNCA respondas devolviendo únicamente la sentencia SQL ni estructures tu respuesta final como un bloque de código o plantilla de "Resultado esperado".
3. Utiliza la información retornada por las herramientas SQL para redactar tu informe o respuesta final con claridad técnica.
"""

@st.cache_resource
def get_db_connection(url):
    if "sslmode=" not in url:
        connector = "&" if "?" in url else "?"
        url += f"{connector}sslmode=require&keepalives=1&keepalives_idle=30"
    
    engine = create_engine(url, pool_pre_ping=True, pool_recycle=300, pool_timeout=30)
    return SQLDatabase(engine)

def es_consulta_valida(prompt: str) -> bool:
    return len(prompt.lower().strip()) >= 3

# --- BARRA SUPERIOR (NAVBAR) ---
st.markdown("""
<div class="top-navbar">
    <div class="brand-section">
        <div class="brand-icon">🗺️</div>
        <div>
            <div class="brand-title">Asistente PostGIS NYC <span class="brand-badge">PostGIS 3.x</span></div>
            <div class="brand-subtitle">Motor Inteligente de Consultas Espaciales & Análisis de Geo-Datos</div>
        </div>
    </div>
    <div class="status-indicator">
        <span class="status-dot"></span> En línea
    </div>
</div>
""", unsafe_allow_html=True)

# --- HEADER CENTRADO HERO ---
st.markdown("""
<div class="hero-container">
    <div class="hero-title">Asistente PostGIS NYC</div>
    <div class="hero-description">
        Herramienta interactiva para estudiantes, ingenieros catastrales, geodesias y analistas urbanos para explorar la base de datos espacio-temporal de Nueva York.
    </div>
</div>
""", unsafe_allow_html=True)

# --- CARDS DE ACCESO RÁPIDO ---
st.markdown("""
<div class="cards-grid">
    <div class="action-card-1">
        <div class="card-info">
            <h3>📊 Casos Prácticos & Delitos</h3>
            <p>Conteo de homicidios, distribución por barrio y densidad delictiva.</p>
        </div>
        <div class="card-action-btn">Ver →</div>
    </div>
    <div class="action-card-2">
        <div class="card-info">
            <h3>🎓 Modo Aprendizaje PostGIS</h3>
            <p>Consultas espaciales con ST_Contains, ST_Intersects y distancias.</p>
        </div>
        <div class="card-action-btn">Iniciar →</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- SELECTOR DE NIVEL DE RESPUESTA ---
st.caption("⚙️ **Nivel de detalle de la respuesta:**")
nivel = st.radio(
    "Nivel de detalle",
    ["📖 Básico", "🎓 Académico", "⚙️ Técnico SQL", "⚖️ Análisis Urbano"],
    index=1,
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("<br>", unsafe_allow_html=True)

# --- BOTONES DE SUGERENCIAS RÁPIDAS ---
col_s1, col_s2, col_s3 = st.columns(3)
prompt_sugerido = None

with col_s1:
    if st.button("📊 Homicidios en Boerum Hill", use_container_width=True):
        prompt_sugerido = "¿Cuántos homicidios hay registrados en el barrio Boerum Hill?"
with col_s2:
    if st.button("🏘️ Barrios de Brooklyn", use_container_width=True):
        prompt_sugerido = "¿Cuáles son los barrios ubicados en Brooklyn?"
with col_s3:
    if st.button("🗽 Vecindarios de Manhattan", use_container_width=True):
        prompt_sugerido = "Muestra 5 barrios aleatorios del condado de Manhattan"

# --- HISTORIAL DE CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            st.markdown(f'<div class="assistant-response-card">{msg["content"]}</div>', unsafe_allow_html=True)
            if msg.get("sql"):
                with st.expander("🔍 Ver código SQL PostGIS ejecutado"):
                    st.code(msg["sql"], language="sql")
        else:
            st.write(msg["content"])

# --- ENTRADA PRINCIPAL DE CHAT ---
prompt = st.chat_input("Escribe tu consulta espacial (ej: ¿Cuántos homicidios ocurrieron en Boerum Hill?)...") or prompt_sugerido

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    if not GROQ_API_KEY:
        resp = "Error: Configura GROQ_API_KEY en los Secrets de Streamlit."
        st.session_state.messages.append({"role": "assistant", "content": resp, "sql": None})
        with st.chat_message("assistant"):
            st.error(resp)
    else:
        if not es_consulta_valida(prompt):
            resp = "Consulta inválida. Por favor escribe una consulta más detallada."
            st.session_state.messages.append({"role": "assistant", "content": resp, "sql": None})
            with st.chat_message("assistant"):
                st.markdown(f'<div class="assistant-response-card">{resp}</div>', unsafe_allow_html=True)
        else:
            try:
                db = get_db_connection(DATABASE_URL)
                llm = ChatGroq(model="openai/gpt-oss-20b", groq_api_key=GROQ_API_KEY, temperature=0)
                
                agent_executor = create_sql_agent(
                    llm, 
                    db=db, 
                    agent_type="tool-calling", 
                    prefix=PREFIX_PROMPT,
                    verbose=False,
                    return_intermediate_steps=True
                )
                
                with st.spinner("⚡ Procesando análisis geoespacial..."):
                    result = agent_executor.invoke({"input": f"[{nivel}] {prompt}"})
                    response_text = result["output"]
                    
                    sql_query = None
                    if "intermediate_steps" in result and result["intermediate_steps"]:
                        for step in result["intermediate_steps"]:
                            if len(step) > 0 and hasattr(step[0], 'tool_input'):
                                tool_input = step[0].tool_input
                                if isinstance(tool_input, dict) and "query" in tool_input:
                                    sql_query = tool_input["query"]
                                elif isinstance(tool_input, str):
                                    sql_query = tool_input
                
                st.session_state.messages.append({"role": "assistant", "content": response_text, "sql": sql_query})
                
                with st.chat_message("assistant"):
                    st.markdown(f'<div class="assistant-response-card">{response_text}</div>', unsafe_allow_html=True)
                    if sql_query:
                        with st.expander("🔍 Ver código SQL PostGIS ejecutado"):
                            st.code(sql_query, language="sql")
                    
            except Exception as e:
                st.error(f"Error al procesar la consulta espacial: {e}")

# --- FOOTER ---
st.markdown("""
<div class="footer-credits">
    Asistente PostGIS para Catastro y Geodesia • Implementado con Streamlit, PostGIS & Groq LLM
</div>
""", unsafe_allow_html=True)
