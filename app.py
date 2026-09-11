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
    page_title="Asistente PostGIS NYC | GeoSpatial AI",
    page_icon="🗺️",
    layout="wide"
)

# 2. Inyección CSS Estilo Dark / OpenClaw Azul Neón con Malla Animada
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
    
    @keyframes move-background {
        0% { background-position: 0 0; }
        100% { background-position: 96px 96px; }
    }

    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-6px); }
        100% { transform: translateY(0px); }
    }

    @keyframes pulse-blue {
        0% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.4); }
        70% { box-shadow: 0 0 0 12px rgba(59, 130, 246, 0); }
        100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); }
    }

    .stApp {
        background-color: #0b0f19 !important;
        background-image: radial-gradient(rgba(59, 130, 246, 0.45) 3.5px, transparent 3.5px) !important;
        background-size: 48px 48px !important;
        animation: move-background 10s linear infinite !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #f1f5f9 !important;
    }

    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1150px;
    }

    /* SOBREESCRITURA DE BOTONES NATIVOS DE STREAMLIT */
    div.stButton > button {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
        color: #93c5fd !important;
        border: 1px solid #3b82f6 !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
    }

    div.stButton > button:hover {
        background: #2563eb !important;
        color: #ffffff !important;
        border-color: #60a5fa !important;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.6) !important;
        transform: translateY(-2px) !important;
    }

    /* FIX SELECTOR RADIO (NIVEL DE DETALLE) */
    div[data-testid="stRadio"] label {
        color: #94a3b8 !important;
        font-weight: 600 !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] {
        background-color: #111827 !important;
        padding: 8px 16px !important;
        border-radius: 12px !important;
        border: 1px solid #1e293b !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] p {
        color: #60a5fa !important;
    }

    /* FIX CHAT INPUT Y MASCARILLA INFERIOR */
    div[data-testid="stChatInput"] {
        background-color: #111827 !important;
        border: 1px solid #3b82f6 !important;
        border-radius: 14px !important;
        box-shadow: 0 8px 20px rgba(0,0,0,0.5) !important;
    }

    div[data-testid="stChatInput"] textarea {
        color: #f1f5f9 !important;
        background-color: transparent !important;
    }

    div[data-testid="stBottomBlockContainer"] {
        background-color: transparent !important;
    }

    /* NAVBAR SUPERIOR ESTILO CYBER */
    .top-navbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #111827;
        border: 1px solid #1e293b;
        border-radius: 16px;
        padding: 12px 24px;
        margin-bottom: 28px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    }

    .brand-section {
        display: flex;
        align-items: center;
        gap: 14px;
    }

    .brand-icon {
        background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
        color: white;
        width: 44px;
        height: 44px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.5);
        animation: float 4s ease-in-out infinite;
    }

    .brand-title {
        font-weight: 800;
        font-size: 1.2rem;
        color: #ffffff;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .brand-badge {
        background-color: #1e293b;
        color: #60a5fa;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 8px;
        border: 1px solid #3b82f6;
    }

    .brand-subtitle {
        font-size: 0.8rem;
        color: #94a3b8;
        margin: 0;
    }

    .status-indicator {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.82rem;
        font-weight: 600;
        color: #60a5fa;
        background: rgba(30, 58, 138, 0.4);
        padding: 6px 14px;
        border-radius: 20px;
        border: 1px solid #2563eb;
    }

    .status-dot {
        width: 9px;
        height: 9px;
        background-color: #3b82f6;
        border-radius: 50%;
        display: inline-block;
        animation: pulse-blue 2s infinite;
    }

    /* HERO HEADER */
    .hero-container {
        text-align: center;
        margin: 20px 0 35px 0;
    }

    .hero-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #ffffff 0%, #93c5fd 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.03em;
        margin-bottom: 8px;
    }

    .hero-description {
        font-size: 1.05rem;
        color: #94a3b8;
        max-width: 720px;
        margin: 0 auto;
        line-height: 1.6;
    }

    /* CARDS DE ACCESO RÁPIDO */
    .action-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 18px;
        padding: 20px;
        min-height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
    }

    .card-info h3 {
        color: #ffffff;
        font-size: 1rem;
        font-weight: 700;
        margin: 0 0 6px 0;
    }

    .card-info p {
        color: #94a3b8;
        font-size: 0.82rem;
        margin: 0;
        line-height: 1.4;
    }

    /* TARJETA DE RESPUESTA EN CHAT */
    .assistant-response-card {
        background: #111827;
        border: 1px solid #1e293b;
        border-left: 5px solid #3b82f6;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 15px;
        color: #e2e8f0;
        font-size: 0.95rem;
        line-height: 1.6;
        box-shadow: 0 8px 20px rgba(0,0,0,0.4);
    }

    .footer-credits {
        text-align: center;
        font-size: 0.8rem;
        color: #64748b;
        margin-top: 50px;
        padding-top: 20px;
        border-top: 1px solid #1e293b;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Credenciales
DATABASE_URL = st.secrets.get(
    "DATABASE_URL", 
    "postgresql://neondb_owner:npg_GDoHi7IUaE8m@ep-bitter-mud-aylkic0b-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require"
)
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", None)

PREFIX_PROMPT = """Eres un asistente analítico especializado en la base de datos geoespacial de la ciudad de Nueva York (PostGIS).

INSTRUCCIONES DE SALIDA:
1. Tu respuesta final DEBE SER SIEMPRE una respuesta redactada en lenguaje natural en español explicando detalladamente los hallazgos o datos encontrados.
2. Si la consulta involucra la representación de mapas, barrios o puntos, utiliza ST_Y(ST_Centroid(geom)), ST_X(ST_Centroid(geom)) o descriptores espaciales. EVITA devolver geometrías completas en texto masivo.
3. NUNCA respondas devolviendo únicamente la sentencia SQL ni estructures tu respuesta final como un bloque de código.
4. Utiliza la información retornada por las herramientas SQL para redactar tu informe con claridad técnica.
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
        <div class="brand-icon">🌐</div>
        <div>
            <div class="brand-title">Bases de Datos Espaciales <span class="brand-badge">PostGIS 3.x</span></div>
            <div class="brand-subtitle">Motor Inteligente de Consultas Espaciales & Visor Geográfico</div>
        </div>
    </div>
    <div class="status-indicator">
        <span class="status-dot"></span> Motor Activo
    </div>
</div>
""", unsafe_allow_html=True)

# --- HEADER CENTRADO HERO ---
st.markdown("""
<div class="hero-container">
    <div class="hero-title">Asistente Geográfico PostGIS</div>
    <div class="hero-description">
        Explora relaciones topológicas, mapas vectoriales y analítica espacial sobre la base de datos de Nueva York.
    </div>
</div>
""", unsafe_allow_html=True)

prompt_sugerido = None
modo_visualizacion_directa = False

# --- CARDS DE ACCESO RÁPIDO EN TRES COLUMNAS ---
col_card1, col_card2, col_card3 = st.columns(3)

with col_card1:
    st.markdown("""
    <div class="action-card">
        <div class="card-info">
            <h3>📊 Análisis de Delitos & Densidad</h3>
            <p>Conteo de homicidios, distribución por barrio y densidad delictiva en NYC.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Explorar →", key="btn_explorar_card", use_container_width=True):
        prompt_sugerido = "¿Cuál es la distribución de homicidios por barrio en Nueva York y los barrios con mayor concentración delictiva?"

with col_card2:
    st.markdown("""
    <div class="action-card">
        <div class="card-info">
            <h3>🗺️ Funciones Espaciales PostGIS</h3>
            <p>Consultas espaciales topológicas con ST_Contains, ST_Intersects y buffers.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Ejecutar →", key="btn_ejecutar_card", use_container_width=True):
        prompt_sugerido = "Muestra una consulta con la función espacial ST_Contains para analizar barrios dentro de un área específica."

with col_card3:
    st.markdown("""
    <div class="action-card">
        <div class="card-info">
            <h3>📍 Mapeo Vectorial Interactivo</h3>
            <p>Abre directamente el visor gráfico interactivo con capas clave y puntos de interés.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Visualizar →", key="btn_visualizar_card", use_container_width=True):
        modo_visualizacion_directa = True

st.markdown("<br>", unsafe_allow_html=True)

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

with col_s1:
    if st.button("📊 Homicidios en Boerum Hill", use_container_width=True):
        prompt_sugerido = "¿Cuántos homicidios hay registrados en el barrio Boerum Hill y muestra su ubicación en el mapa?"
with col_s2:
    if st.button("🏘️ Barrios de Brooklyn", use_container_width=True):
        prompt_sugerido = "¿Cuáles son los barrios ubicados en Brooklyn y muestra el mapa de Nueva York?"
with col_s3:
    if st.button("🗽 Vecindarios de Manhattan", use_container_width=True):
        prompt_sugerido = "Muestra barrios del condado de Manhattan en la base de datos"

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
prompt_user = st.chat_input("Escribe tu consulta espacial (ej: Muestra los barrios de Brooklyn o analiza Boerum Hill)...")
prompt = prompt_user or prompt_sugerido

# --- CASO A: MODO VISUALIZACIÓN DIRECTA (CLIC EN BOTÓN "VISUALIZAR →") ---
if modo_visualizacion_directa:
    st.subheader("🗺️ Visor Geográfico Interactivo Directo (NYC)")
    st.info("Cargando capas interactivas y puntos principales de la base de datos...")
    
    m_direct = folium.Map(location=[40.7128, -74.0060], zoom_start=11, tiles="CartoDB dark_matter")
    
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
        
    map_data_direct = st_folium(m_direct, width=1000, height=450)
    if map_data_direct and map_data_direct.get("last_clicked"):
        click_lat = map_data_direct["last_clicked"]["lat"]
        click_lng = map_data_direct["last_clicked"]["lng"]
        st.info(f"📍 **Coordenada seleccionada:** Latitud `{click_lat:.5f}`, Longitud `{click_lng:.5f}`")

# --- CASO B: PROCESAMIENTO CON AGENTE LLM Y POSTGIS ---
elif prompt:
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
                    
                    # VISOR DE MAPA ESPACIAL INTERACTIVO (FOLIUM)
                    st.subheader("🗺️ Visor de Mapa Espacial Interactivo (NYC)")
                    m = folium.Map(location=[40.7128, -74.0060], zoom_start=11, tiles="CartoDB dark_matter")
                    
                    # Evaluación de contexto geoespacial para renderizado dinámico
                    prompt_lower = prompt.lower()
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
                            color="#3b82f6",
                            fill=True,
                            fill_color="#2563eb",
                            fill_opacity=0.35,
                            popup="Área de Influencia / Buffer Espacial"
                        ).add_to(m)

                    elif "brooklyn" in prompt_lower:
                        m.location = [40.6782, -73.9442]
                        m.zoom_start = 12
                        folium.Marker(
                            [40.6782, -73.9442],
                            popup="<b>Borough: Brooklyn</b><br>Datos vectoriales cargados desde la BD",
                            tooltip="Condado de Brooklyn",
                            icon=folium.Icon(color="cyan", icon="globe")
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

                    # Evento interactivo st_folium: captura clics e interacción en el mapa
                    map_data = st_folium(m, width=1000, height=420)

                    # Si el usuario hace clic en el mapa, muestra las coordenadas seleccionadas
                    if map_data and map_data.get("last_clicked"):
                        click_lat = map_data["last_clicked"]["lat"]
                        click_lng = map_data["last_clicked"]["lng"]
                        st.info(f"📍 **Coordenada seleccionada en el mapa:** Latitud `{click_lat:.5f}`, Longitud `{click_lng:.5f}`")

                    if sql_query:
                        with st.expander("🔍 Ver código SQL PostGIS ejecutado"):
                            st.code(sql_query, language="sql")
                    
            except Exception as e:
                st.error(f"Error al procesar la consulta espacial: {e}")

# --- FOOTER ---
st.markdown("""
<div class="footer-credits">
    Asistente PostGIS para Catastro y Geodesia • Universidad Distrital Francisco José de Caldas
</div>
""", unsafe_allow_html=True)
