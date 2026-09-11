import json
import streamlit as st
import folium
from streamlit_folium import st_folium
from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_groq import ChatGroq

# 1. Configuración de la página
st.set_page_config(
    page_title="Geospatial Intelligence System | NYC PostGIS",
    page_icon="🌐",
    layout="wide"
)

# 2. CSS Avanzado: Malla Vectorial + Ondas Radiales HUD
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* Variables Globales */
    :root {
        --bg-dark: #07090e;
        --accent-red: #ff4a36;
        --accent-blue: #3b82f6;
        --border-color: rgba(255, 255, 255, 0.08);
    }

    /* Animación de Ondas Radiales Concéntricas */
    @keyframes radar-ripple {
        0% {
            width: 0px;
            height: 0px;
            opacity: 0.8;
            border-color: rgba(255, 74, 54, 0.6);
        }
        50% {
            opacity: 0.3;
            border-color: rgba(59, 130, 246, 0.4);
        }
        100% {
            width: 1200px;
            height: 1200px;
            opacity: 0;
            border-color: rgba(59, 130, 246, 0);
        }
    }

    /* Fondo Base con Malla Vectorial */
    .stApp {
        background-color: var(--bg-dark) !important;
        background-image: 
            radial-gradient(rgba(255, 74, 54, 0.12) 1.5px, transparent 1.5px),
            radial-gradient(rgba(59, 130, 246, 0.08) 1px, transparent 1px) !important;
        background-size: 32px 32px, 16px 16px !important;
        background-position: 0 0, 8px 8px !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #f1f5f9 !important;
        position: relative;
        overflow-x: hidden;
    }

    /* Contenedor de Ondas Absolutas (Overlay) */
    .stApp::before, .stApp::after {
        content: "";
        position: fixed;
        top: 30%;
        left: 50%;
        transform: translate(-50%, -50%);
        border: 1px solid rgba(255, 74, 54, 0.4);
        border-radius: 50%;
        pointer-events: none;
        z-index: 0;
        animation: radar-ripple 8s cubic-bezier(0.1, 0.8, 0.3, 1) infinite;
    }

    .stApp::after {
        animation-delay: 4s; /* Desfase para ondas continuas */
    }

    .main .block-container {
        position: relative;
        z-index: 1;
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1180px;
    }

    /* Estilización de Botones */
    div.stButton > button {
        background: rgba(15, 23, 42, 0.7) !important;
        color: #e2e8f0 !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        font-size: 0.88rem !important;
        padding: 0.55rem 1rem !important;
        backdrop-filter: blur(8px) !important;
        transition: all 0.25s ease !important;
    }

    div.stButton > button:hover {
        background: rgba(30, 41, 59, 0.9) !important;
        color: #ffffff !important;
        border-color: rgba(255, 74, 54, 0.5) !important;
        box-shadow: 0 0 12px rgba(255, 74, 54, 0.25) !important;
        transform: translateY(-1px) !important;
    }

    /* Custom Radio Controls */
    div[data-testid="stRadio"] div[role="radiogroup"] {
        background-color: rgba(15, 23, 42, 0.6) !important;
        padding: 6px 12px !important;
        border-radius: 10px !important;
        border: 1px solid var(--border-color) !important;
        backdrop-filter: blur(8px) !important;
    }

    /* Componente de ChatInput */
    div[data-testid="stChatInput"] {
        background-color: rgba(15, 23, 42, 0.8) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(12px) !important;
    }

    div[data-testid="stChatInput"]:focus-within {
        border-color: rgba(255, 74, 54, 0.6) !important;
        box-shadow: 0 0 15px rgba(255, 74, 54, 0.15) !important;
    }

    /* Structural Components */
    .top-navbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: rgba(15, 23, 42, 0.65);
        border: 1px solid var(--border-color);
        border-radius: 14px;
        padding: 12px 20px;
        margin-bottom: 24px;
        backdrop-filter: blur(12px);
    }

    .brand-section {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .brand-icon {
        background: rgba(255, 74, 54, 0.15);
        color: var(--accent-red);
        border: 1px solid rgba(255, 74, 54, 0.3);
        width: 38px;
        height: 38px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
    }

    .brand-title {
        font-weight: 700;
        font-size: 1.05rem;
        color: #ffffff;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .brand-badge {
        background-color: rgba(255, 74, 54, 0.1);
        color: var(--accent-red);
        font-size: 0.7rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 6px;
        border: 1px solid rgba(255, 74, 54, 0.25);
    }

    .brand-subtitle {
        font-size: 0.78rem;
        color: #94a3b8;
        margin: 0;
    }

    .status-indicator {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.78rem;
        font-weight: 500;
        color: #94a3b8;
        background: rgba(255, 255, 255, 0.03);
        padding: 5px 12px;
        border-radius: 20px;
        border: 1px solid var(--border-color);
    }

    .status-dot {
        width: 7px;
        height: 7px;
        background-color: #10b981;
        border-radius: 50%;
        display: inline-block;
    }

    .hero-container {
        text-align: center;
        margin: 15px 0 30px 0;
    }

    .hero-title {
        font-size: 2.5rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: #ffffff;
        margin-bottom: 6px;
    }

    .hero-description {
        font-size: 0.98rem;
        color: #94a3b8;
        max-width: 680px;
        margin: 0 auto;
        line-height: 1.5;
    }

    .action-card {
        background: rgba(15, 23, 42, 0.5);
        border: 1px solid var(--border-color);
        border-radius: 14px;
        padding: 18px;
        min-height: 125px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        backdrop-filter: blur(8px);
    }

    .card-info h3 {
        color: #ffffff;
        font-size: 0.95rem;
        font-weight: 600;
        margin: 0 0 4px 0;
    }

    .card-info p {
        color: #94a3b8;
        font-size: 0.8rem;
        margin: 0;
        line-height: 1.4;
    }

    .assistant-response-card {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid var(--border-color);
        border-left: 3px solid var(--accent-red);
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 15px;
        color: #e2e8f0;
        font-size: 0.92rem;
        line-height: 1.6;
        backdrop-filter: blur(8px);
    }

    .footer-credits {
        text-align: center;
        font-size: 0.75rem;
        color: #475569;
        margin-top: 40px;
        padding-top: 15px;
        border-top: 1px solid var(--border-color);
    }
    </style>
""", unsafe_allow_html=True)

# 3. Inicialización de Estado
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None
if "modo_visualizacion_directa" not in st.session_state:
    st.session_state.modo_visualizacion_directa = False

def set_prompt(texto):
    st.session_state.pending_prompt = texto
    st.session_state.modo_visualizacion_directa = False

def activar_modo_directo():
    st.session_state.modo_visualizacion_directa = True
    st.session_state.pending_prompt = None

DATABASE_URL = st.secrets.get("DATABASE_URL", "")
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", None)

# Capa de Mapa Libre de Esri (Sin Token/API Key Exigido)
ESRI_DARK_TILES = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
ESRI_ATTR = "Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ"

PREFIX_PROMPT = """Eres un asistente analítico especializado en la base de datos geoespacial de la ciudad de Nueva York (PostGIS).

INSTRUCCIONES DE SALIDA:
1. Tu respuesta final DEBE SER SIEMPRE una respuesta redactada en lenguaje natural en español explicando detalladamente los hallazgos o datos encontrados.
2. Si la consulta involucra la representación de mapas, barrios o puntos, utiliza ST_Y(ST_Centroid(geom)), ST_X(ST_Centroid(geom)) o descriptores espaciales. EVITA devolver geometrías completas en texto masivo.
3. NUNCA respondas devolviendo únicamente la sentencia SQL ni estructures tu respuesta final como un bloque de código.
4. Utiliza la información retornada por las herramientas SQL para redactar tu informe con claridad técnica.
"""

@st.cache_resource
def get_db_connection(url):
    if not url:
        st.error("DATABASE_URL no configurada en st.secrets.")
        st.stop()
    if "sslmode=" not in url:
        connector = "&" if "?" in url else "?"
        url += f"{connector}sslmode=require&keepalives=1&keepalives_idle=30"
    engine = create_engine(url, pool_pre_ping=True, pool_recycle=300, pool_timeout=30)
    return SQLDatabase(engine)

def es_consulta_valida(prompt: str) -> bool:
    return len(prompt.lower().strip()) >= 3

# UI Layout
st.markdown("""
<div class="top-navbar">
    <div class="brand-section">
        <div class="brand-icon">⌘</div>
        <div>
            <div class="brand-title">PostGIS Analytics <span class="brand-badge">Engine 3.x</span></div>
            <div class="brand-subtitle">Infraestructura Espacial & Plataforma de Análisis Urbano</div>
        </div>
    </div>
    <div class="status-indicator">
        <span class="status-dot"></span> Cluster Online
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero-container">
    <div class="hero-title">Spatial Data Assistant</div>
    <div class="hero-description">
        Motor analítico para consultas topológicas, análisis de redes vectoriales y densidad delictiva en Nueva York.
    </div>
</div>
""", unsafe_allow_html=True)

col_card1, col_card2, col_card3 = st.columns(3)

with col_card1:
    st.markdown("""
    <div class="action-card">
        <div class="card-info">
            <h3>📊 Análisis de Delitos</h3>
            <p>Distribución espacial e indicadores delictivos concentrados por barrio.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.button("Explorar →", key="btn_explorar_card", use_container_width=True, 
              on_click=set_prompt, args=("¿Cuál es la distribución de homicidios por barrio en Nueva York y los barrios con mayor concentración delictiva?",))

with col_card2:
    st.markdown("""
    <div class="action-card">
        <div class="card-info">
            <h3>🗺️ Relaciones Topológicas</h3>
            <p>Evaluación de contención espacial e intersección con ST_Contains.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.button("Ejecutar →", key="btn_ejecutar_card", use_container_width=True, 
              on_click=set_prompt, args=("Muestra una consulta con la función espacial ST_Contains para analizar barrios dentro de un área específica.",))

with col_card3:
    st.markdown("""
    <div class="action-card">
        <div class="card-info">
            <h3>📍 Visor de Capas Vectoriales</h3>
            <p>Despliegue directo del mapa interactivo con entidades geoespaciales.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.button("Visualizar →", key="btn_visualizar_card", use_container_width=True, on_click=activar_modo_directo)

st.markdown("<br>", unsafe_allow_html=True)

nivel = st.radio(
    "Nivel de detalle",
    ["📖 Básico", "🎓 Académico", "⚙️ Técnico SQL", "⚖️ Análisis Urbano"],
    index=1,
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("<br>", unsafe_allow_html=True)

col_s1, col_s2, col_s3 = st.columns(3)
with col_s1:
    st.button("📊 Homicidios en Boerum Hill", use_container_width=True, 
              on_click=set_prompt, args=("¿Cuántos homicidios hay registrados en el barrio Boerum Hill y muestra su ubicación en el mapa?",))
with col_s2:
    st.button("🏘️ Barrios de Brooklyn", use_container_width=True, 
              on_click=set_prompt, args=("¿Cuáles son los barrios ubicados en Brooklyn y muestra el mapa de Nueva York?",))
with col_s3:
    st.button("🗽 Vecindarios de Manhattan", use_container_width=True, 
              on_click=set_prompt, args=("Muestra barrios del condado de Manhattan en la base de datos",))

prompt_user = st.chat_input("Escribe tu consulta espacial...")
if prompt_user:
    st.session_state.pending_prompt = prompt_user
    st.session_state.modo_visualizacion_directa = False

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            st.markdown(f'<div class="assistant-response-card">{msg["content"]}</div>', unsafe_allow_html=True)
            if msg.get("sql"):
                with st.expander("🔍 Ver código SQL PostGIS ejecutado"):
                    st.code(msg["sql"], language="sql")
        else:
            st.write(msg["content"])

# Renderizado de Mapa Directo
if st.session_state.modo_visualizacion_directa:
    st.subheader("🗺️ Visor Geográfico Interactivo Directo (NYC)")
    st.info("Cargando capas interactivas y puntos principales de la base de datos...")
    
    m_direct = folium.Map(location=[40.7128, -74.0060], zoom_start=11, tiles=ESRI_DARK_TILES, attr=ESRI_ATTR)
    puntos_interes = [
        {"nombre": "Boerum Hill", "lat": 40.6862, "lng": -73.9882, "borough": "Brooklyn", "color": "blue"},
        {"nombre": "Financial District", "lat": 40.7075, "lng": -74.0089, "borough": "Manhattan", "color": "purple"},
        {"nombre": "Midtown Manhattan", "lat": 40.7549, "lng": -73.9840, "borough": "Manhattan", "color": "purple"},
        {"nombre": "Astoria", "lat": 40.7644, "lng": -73.9235, "borough": "Queens", "color": "green"},
    ]
    for p in puntos_interes:
        folium.Marker(
            [p["lat"], p["lng"]],
            popup=f"<b>Barrio: {p['nombre']}</b><br>Borough: {p['borough']}",
            tooltip=p["nombre"],
            icon=folium.Icon(color=p["color"], icon="info-sign")
        ).add_to(m_direct)
        
    map_data_direct = st_folium(m_direct, use_container_width=True, height=480, key="folium_direct_map")
    if map_data_direct and map_data_direct.get("last_clicked"):
        click_lat = map_data_direct["last_clicked"]["lat"]
        click_lng = map_data_direct["last_clicked"]["lng"]
        st.info(f"📍 **Coordenada seleccionada:** Latitud `{click_lat:.5f}`, Longitud `{click_lng:.5f}`")

# Ejecución de Agente LLM + Mapa Integrado
elif st.session_state.pending_prompt:
    prompt_actual = st.session_state.pending_prompt
    st.session_state.pending_prompt = None

    st.session_state.messages.append({"role": "user", "content": prompt_actual})
    with st.chat_message("user"):
        st.write(prompt_actual)

    if not GROQ_API_KEY:
        resp = "Error: Configura GROQ_API_KEY en los Secrets de Streamlit."
        st.session_state.messages.append({"role": "assistant", "content": resp, "sql": None})
        with st.chat_message("assistant"):
            st.error(resp)
    else:
        if not es_consulta_valida(prompt_actual):
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
                    result = agent_executor.invoke({"input": f"[{nivel}] {prompt_actual}"})
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
                    
                    st.subheader("🗺️ Visor de Mapa Espacial Interactivo (NYC)")
                    m = folium.Map(location=[40.7128, -74.0060], zoom_start=11, tiles=ESRI_DARK_TILES, attr=ESRI_ATTR)
                    
                    prompt_lower = prompt_actual.lower()
                    if "boerum hill" in prompt_lower:
                        map_center = [40.6862, -73.9882]
                        m.location = map_center
                        m.zoom_start = 14
                        folium.Marker(
                            map_center,
                            popup=folium.Popup("<b>Barrio: Boerum Hill</b><br>Borough: Brooklyn<br>Atributo: Área bajo análisis", max_width=250),
                            tooltip="Haz clic para ver más información",
                            icon=folium.Icon(color="blue", icon="info-sign")
                        ).add_to(m)
                        folium.Circle(
                            radius=600,
                            location=map_center,
                            color="#ff4a36",
                            fill=True,
                            fill_color="#ff4a36",
                            fill_opacity=0.25,
                            popup="Área de Influencia / Buffer Espacial"
                        ).add_to(m)

                    elif "brooklyn" in prompt_lower:
                        m.location = [40.6782, -73.9442]
                        m.zoom_start = 12
                        folium.Marker(
                            [40.6782, -73.9442],
                            popup="<b>Borough: Brooklyn</b><br>Datos vectoriales cargados desde la BD",
                            tooltip="Condado de Brooklyn",
                            icon=folium.Icon(color="blue", icon="globe")
                        ).add_to(m)

                    elif "manhattan" in prompt_lower:
                        m.location = [40.7831, -73.9712]
                        m.zoom_start = 12
                        folium.Marker(
                            [40.7831, -73.9712],
                            popup="<b>Borough: Manhattan</b><br>Datos de vecindarios PostGIS",
                            tooltip="Condado de Manhattan",
                            icon=folium.Icon(color="purple", icon="star")
                        ).add_to(m)

                    map_data = st_folium(m, use_container_width=True, height=450, key="folium_agent_map")

                    if map_data and map_data.get("last_clicked"):
                        click_lat = map_data["last_clicked"]["lat"]
                        click_lng = map_data["last_clicked"]["lng"]
                        st.info(f"📍 **Coordenada seleccionada en el mapa:** Latitud `{click_lat:.5f}`, Longitud `{click_lng:.5f}`")

                    if sql_query:
                        with st.expander("🔍 Ver código SQL PostGIS ejecutado"):
                            st.code(sql_query, language="sql")
                    
            except Exception as e:
                st.error(f"Error al procesar la consulta espacial: {e}")

st.markdown("""
<div class="footer-credits">
    Plataforma de Inteligencia Espacial PostGIS • Universidad Distrital Francisco José de Caldas
</div>
""", unsafe_allow_html=True)
