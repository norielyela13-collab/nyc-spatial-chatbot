import streamlit as st
import psycopg2
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_groq import ChatGroq

st.set_page_config(page_title="Asistente PostGIS NYC", page_icon="🗺️", layout="centered")

# Inyección de estilos CSS personalizados
st.markdown("""
    <style>
    .main { max-width: 800px; margin: 0 auto; }
    .stCard {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .stCard h4 { margin-top: 0; color: #1e293b; }
    .stCard p { color: #64748b; font-size: 0.9em; margin-bottom: 0; }
    </style>
""", unsafe_allow_html=True)

DATABASE_URL = "postgresql://neondb_owner:npg_GDoHi7IUaE8m@ep-bitter-mud-aylkic0b-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require"

# Diálogo / Modal de bienvenida
@st.dialog("🏛️ Guía de Bienvenida — Asistente PostGIS NYC")
def modal_bienvenida():
    st.write("**Soy tu asistente analítico especializado en la base de datos espacial de Nueva York (PostGIS).**")
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="stCard">
            <h4>🌐 ¿Qué es?</h4>
            <p>Herramienta de consulta geoespacial sobre barrios, bloques censales y criminalidad en NYC.</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="stCard">
            <h4>❓ ¿Qué preguntar?</h4>
            <p>Consultas topológicas, conteos espaciales, análisis por barrios o áreas de cobertura.</p>
        </div>
        """, unsafe_allow_html=True)
        
    st.divider()
    if st.button("Comenzar a explorar", type="primary", use_container_width=True):
        st.session_state.bienvenida_mostrada = True
        st.rerun()

if "bienvenida_mostrada" not in st.session_state:
    modal_bienvenida()

# Barra lateral
with st.sidebar:
    st.header("⚙️ Configuración")
    groq_api_key = st.text_input("Groq API Key", type="password")
    if st.button("Revisar Guía de Inicio"):
        modal_bienvenida()

st.title("🗺️ Asistente Espacial PostGIS")
st.caption("Consulta espacial en lenguaje natural conectada a Neon PostgreSQL")

# Sugerencias rápidas (Quick Prompts)
st.write("**¿Por dónde deseas comenzar?**")
col_a, col_b = st.columns(2)

prompt_sugerido = None
with col_a:
    if st.button("📊 Contar homicidios en NYC", use_container_width=True):
        prompt_sugerido = "¿Cuántos homicidios hay registrados en la base de datos de NYC?"
with col_b:
    if st.button("🏘️ Listar barrios de Brooklyn", use_container_width=True):
        prompt_sugerido = "¿Cuáles son los barrios ubicados en Brooklyn?"

# Historial de Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Captura de entrada (chat o sugerencia)
prompt = st.chat_input("Escribe tu consulta espacial aquí...") or prompt_sugerido

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    if not groq_api_key:
        resp = "Ingresa tu Groq API Key en la barra lateral para procesar la consulta."
        st.session_state.messages.append({"role": "assistant", "content": resp})
        st.chat_message("assistant").write(resp)
    else:
        try:
            db = SQLDatabase.from_uri(DATABASE_URL)
            llm = ChatGroq(
                model="llama-3.1-70b-versatile",
                groq_api_key=groq_api_key,
                temperature=0
            )
            agent_executor = create_sql_agent(
                llm, 
                db=db, 
                agent_type="tool-calling", 
                verbose=False
            )
            
            with st.spinner("Ejecutando consulta PostGIS..."):
                result = agent_executor.invoke({"input": prompt})
                response = result["output"]
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.chat_message("assistant").write(response)
        except Exception as e:
            st.error(f"Error en la consulta: {e}")
