import streamlit as st
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_groq import ChatGroq


# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

st.set_page_config(
    page_title="NYC PostGIS Spatial Engine",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# ESTILOS CSS
# =========================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html,
body,
[class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}


/* CONTENEDOR PRINCIPAL */

.main .block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1100px;
}


/* TÍTULO */

.title-tech {
    font-size: 1.75rem;
    font-weight: 700;
    color: #0f172a;
    letter-spacing: -0.02em;
    margin-bottom: 2px;
}


/* SUBTÍTULO */

.subtitle-tech {
    font-size: 0.95rem;
    color: #64748b;
    margin-bottom: 1.25rem;
}


/* TARJETAS */

.stCard {
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 14px;
    margin-bottom: 10px;
}


.stCard h4 {
    margin-top: 0;
    color: #1e293b;
    font-weight: 600;
    font-size: 0.95rem;
}


.stCard p {
    color: #475569;
    font-size: 0.85rem;
    margin-bottom: 0;
}


/* RESPUESTA DEL ASISTENTE */

.assistant-response-box {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-left: 3px solid #2563eb;
    border-radius: 6px;
    padding: 14px 16px;
    color: #1e293b;
    font-size: 0.92rem;
    line-height: 1.6;
}


/* BADGE */

.badge-tech {
    background-color: #eff6ff;
    color: #1d4ed8;
    border: 1px solid #bfdbfe;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    font-family: monospace;
    display: inline-block;
    margin-bottom: 8px;
}


/* AJUSTES PARA CELULAR */

@media (max-width: 768px) {

    .main .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
        padding-top: 1rem;
    }

    .title-tech {
        font-size: 1.4rem;
    }

    .subtitle-tech {
        font-size: 0.85rem;
    }

    .assistant-response-box {
        font-size: 0.88rem;
        padding: 12px;
    }

}

</style>
""", unsafe_allow_html=True)


# =========================================================
# CONFIGURACIÓN DE BASE DE DATOS
# =========================================================

try:
    DATABASE_URL = st.secrets["DATABASE_URL"]

except Exception:
    DATABASE_URL = None


# =========================================================
# PROMPT DEL SISTEMA
# =========================================================

PREFIX_PROMPT = """
Eres un asistente especializado en análisis geoespacial de la
ciudad de Nueva York utilizando PostgreSQL y PostGIS.

Tu función es ayudar al usuario a consultar exclusivamente la base
de datos disponible.

Debes:

1. Analizar la pregunta del usuario.
2. Identificar las tablas relevantes.
3. Utilizar las herramientas SQL disponibles.
4. Generar consultas eficientes compatibles con PostgreSQL/PostGIS.
5. Ejecutar las consultas necesarias.
6. Responder en español.
7. Explicar los resultados de forma clara y concisa.

REGLAS IMPORTANTES:

- No inventes tablas, columnas ni datos.
- Antes de realizar una consulta compleja, inspecciona la estructura
  de las tablas disponibles.
- Utiliza únicamente información realmente obtenida desde la base
  de datos.
- No ejecutes consultas destructivas.
- Nunca uses:
    DROP
    DELETE
    UPDATE
    INSERT
    ALTER
    TRUNCATE
    CREATE
- Si no existe información suficiente en la base de datos, indícalo.
- Para consultas geoespaciales utiliza funciones PostGIS cuando
  corresponda.
- Ejemplos de funciones disponibles:
    ST_Intersects
    ST_Contains
    ST_Within
    ST_Distance
    ST_Buffer
    ST_Touches
    ST_Centroid

Responde siempre en español.
"""


# =========================================================
# CONEXIÓN A LA BASE DE DATOS
# =========================================================

@st.cache_resource
def get_db_connection(database_url):

    return SQLDatabase.from_uri(
        database_url,
        sample_rows_in_table_info=3
    )


# =========================================================
# VALIDACIÓN DE CONSULTAS
# =========================================================

def es_consulta_valida(prompt: str) -> bool:

    palabras_clave = [

        "barrio",
        "barrios",
        "nyc",
        "nueva york",
        "new york",

        "distrito",
        "distritos",

        "crimen",
        "crímenes",
        "crimenes",

        "homicidio",
        "homicidios",

        "calle",
        "calles",

        "polígono",
        "poligono",

        "ubicación",
        "ubicacion",

        "postgis",

        "coordenada",
        "coordenadas",

        "borough",

        "manhattan",
        "brooklyn",
        "queens",
        "bronx",
        "staten island",

        "vecindario",
        "vecindarios",

        "espacial",
        "geografía",
        "geografia",

        "mapa",

        "bloque",
        "bloques",

        "censal",

        "límite",
        "limite",
        "limitan",

        "distancia",

        "intersecta",
        "intersección",
        "interseccion"
    ]

    prompt_lower = prompt.lower()

    return any(
        palabra in prompt_lower
        for palabra in palabras_clave
    )


# =========================================================
# VALIDACIÓN DE SEGURIDAD
# =========================================================

def contiene_operacion_prohibida(texto: str) -> bool:

    operaciones_prohibidas = [

        "drop ",
        "delete ",
        "update ",
        "insert ",
        "alter ",
        "truncate ",
        "create "
    ]

    texto_lower = texto.lower()

    return any(
        operacion in texto_lower
        for operacion in operaciones_prohibidas
    )


# =========================================================
# MODAL DE BIENVENIDA
# =========================================================

@st.dialog("Centro de Control Geoespacial — NYC PostGIS")
def modal_bienvenida():

    st.write(
        "Entorno analítico para la ejecución de consultas "
        "espaciales y tabulares sobre PostgreSQL/PostGIS."
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("""
        <div class="stCard">

            <h4>Capa Vectorial y Tabular</h4>

            <p>
            Acceso a datos de límites de barrios, bloques censales,
            red vial y registros disponibles en la base de datos.
            </p>

        </div>
        """, unsafe_allow_html=True)


    with col2:

        st.markdown("""
        <div class="stCard">

            <h4>Procesamiento Espacial</h4>

            <p>
            Evaluación de funciones espaciales como ST_Contains,
            ST_Distance, ST_Intersects y ST_Buffer.
            </p>

        </div>
        """, unsafe_allow_html=True)


    st.divider()


    if st.button(
        "Iniciar Panel de Análisis",
        type="primary",
        use_container_width=True
    ):

        st.session_state.bienvenida_mostrada = True

        st.rerun()


# =========================================================
# ESTADO DE LA SESIÓN
# =========================================================

if "bienvenida_mostrada" not in st.session_state:

    st.session_state.bienvenida_mostrada = False


if "messages" not in st.session_state:

    st.session_state.messages = []


if "groq_api_key" not in st.session_state:

    st.session_state.groq_api_key = ""


# =========================================================
# MOSTRAR BIENVENIDA
# =========================================================

if not st.session_state.bienvenida_mostrada:

    modal_bienvenida()


# =========================================================
# PANEL LATERAL
# =========================================================

with st.sidebar:

    st.title("Parámetros")


    groq_api_key = st.text_input(
        "Groq API Key",
        value=st.session_state.groq_api_key,
        type="password",
        help="Ingresa tu clave de Groq que comienza con gsk_..."
    )


    # Guardar temporalmente durante la sesión

    st.session_state.groq_api_key = groq_api_key


    st.divider()


    st.caption("INFRAESTRUCTURA DE DATOS")

    st.text("BD: Neon PostgreSQL")

    st.text("Motor espacial: PostGIS")


    if DATABASE_URL:

        st.success("Base de datos configurada")

    else:

        st.error("DATABASE_URL no configurada")


    if groq_api_key:

        st.success("API Key cargada correctamente")

    else:

        st.warning("Se requiere API Key")


    st.divider()


    # BOTÓN PARA LIMPIAR CHAT

    if st.button(
        "🧹 Limpiar historial",
        use_container_width=True
    ):

        st.session_state.messages = []

        st.rerun()


    # GUÍA

    if st.button(
        "Guía de uso",
        use_container_width=True
    ):

        modal_bienvenida()


# =========================================================
# ENCABEZADO PRINCIPAL
# =========================================================

st.markdown(
    '<div class="badge-tech">'
    'POSTGIS ENGINE // NYC SPATIAL DATA'
    '</div>',
    unsafe_allow_html=True
)


st.markdown(
    '<div class="title-tech">'
    'Asistente de Analítica Espacial NYC'
    '</div>',
    unsafe_allow_html=True
)


st.markdown(
    '<div class="subtitle-tech">'
    'Traducción de consultas en lenguaje natural '
    'a consultas SQL utilizando PostGIS'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# SUGERENCIAS RÁPIDAS
# =========================================================

col_a, col_b, col_c = st.columns(3)


prompt_sugerido = None


with col_a:

    if st.button(
        "Homicidios en NYC",
        use_container_width=True
    ):

        prompt_sugerido = (
            "¿Cuántos homicidios hay registrados "
            "en la base de datos de NYC?"
        )


with col_b:

    if st.button(
        "Barrios de Brooklyn",
        use_container_width=True
    ):

        prompt_sugerido = (
            "¿Cuáles son los barrios ubicados "
            "en Brooklyn?"
        )


with col_c:

    if st.button(
        "Vecindarios por Borough",
        use_container_width=True
    ):

        prompt_sugerido = (
            "Muestra 5 barrios aleatorios "
            "con su respectivo borough"
        )


# =========================================================
# HISTORIAL DEL CHAT
# =========================================================

for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):

        if msg["role"] == "assistant":

            st.markdown(
                f"""
                <div class="assistant-response-box">
                    {msg["content"]}
                </div>
                """,
                unsafe_allow_html=True
            )

        else:

            st.write(msg["content"])


# =========================================================
# ENTRADA DEL USUARIO
# =========================================================

prompt = (
    st.chat_input(
        "Escribe tu consulta espacial..."
    )
    or prompt_sugerido
)


# =========================================================
# PROCESAMIENTO DE CONSULTA
# =========================================================

if prompt:


    # MOSTRAR CONSULTA DEL USUARIO

    st.session_state.messages.append({

        "role": "user",

        "content": prompt

    })


    with st.chat_message("user"):

        st.write(prompt)


    # =====================================================
    # VALIDAR API KEY
    # =====================================================

    if not groq_api_key:


        respuesta = (
            "Por favor, ingresa tu Groq API Key "
            "en el panel lateral para ejecutar la consulta."
        )


        st.session_state.messages.append({

            "role": "assistant",

            "content": respuesta

        })


        with st.chat_message("assistant"):

            st.warning(respuesta)


    # =====================================================
    # VALIDAR BASE DE DATOS
    # =====================================================

    elif not DATABASE_URL:


        respuesta = (
            "No se encontró la configuración "
            "DATABASE_URL en los secretos de Streamlit."
        )


        st.session_state.messages.append({

            "role": "assistant",

            "content": respuesta

        })


        with st.chat_message("assistant"):

            st.error(respuesta)


    # =====================================================
    # VALIDAR DOMINIO
    # =====================================================

    elif not es_consulta_valida(prompt):


        respuesta = (
            "Consulta no procesada. Este sistema está "
            "especializado en análisis geoespacial y tabular "
            "de la ciudad de Nueva York utilizando PostGIS."
        )


        st.session_state.messages.append({

            "role": "assistant",

            "content": respuesta

        })


        with st.chat_message("assistant"):

            st.markdown(

                f"""
                <div class="assistant-response-box">
                    {respuesta}
                </div>
                """,

                unsafe_allow_html=True
            )


    # =====================================================
    # VALIDAR OPERACIONES PELIGROSAS
    # =====================================================

    elif contiene_operacion_prohibida(prompt):


        respuesta = (
            "La consulta contiene una operación que no está "
            "permitida por motivos de seguridad."
        )


        st.session_state.messages.append({

            "role": "assistant",

            "content": respuesta

        })


        with st.chat_message("assistant"):

            st.error(respuesta)


    # =====================================================
    # EJECUTAR AGENTE
    # =====================================================

    else:


        try:


            # CONECTAR BASE DE DATOS

            db = get_db_connection(DATABASE_URL)


            # MODELO ACTUAL DE GROQ

            llm = ChatGroq(

                model="openai/gpt-oss-20b",

                groq_api_key=groq_api_key,

                temperature=0

            )


            # CREAR AGENTE SQL

            agent_executor = create_sql_agent(

                llm=llm,

                db=db,

                agent_type="tool-calling",

                prefix=PREFIX_PROMPT,

                verbose=False

            )


            # EJECUTAR CONSULTA

            with st.spinner(

                "Procesando consulta e interactuando con PostGIS..."

            ):


                result = agent_executor.invoke({

                    "input": prompt

                })


                response = result["output"]


            # GUARDAR RESPUESTA

            st.session_state.messages.append({

                "role": "assistant",

                "content": response

            })


            # MOSTRAR RESPUESTA

            with st.chat_message("assistant"):


                st.markdown(

                    f"""
                    <div class="assistant-response-box">
                        {response}
                    </div>
                    """,

                    unsafe_allow_html=True
                )


        # =================================================
        # MANEJO DE ERRORES
        # =================================================

        except Exception as e:


            error_text = str(e)


            respuesta_error = (

                "Error al procesar la consulta espacial:\n\n"

                f"{error_text}"

            )


            st.session_state.messages.append({

                "role": "assistant",

                "content": respuesta_error

            })


            with st.chat_message("assistant"):

                st.error(respuesta_error)
