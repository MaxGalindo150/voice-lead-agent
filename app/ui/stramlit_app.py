# app/ui/streamlit_app.py
import streamlit as st

# Importar páginas
from app.ui.pages.chat import show as show_chat
from app.ui.pages.leads import show as show_leads
# from app.ui.pages.settings import show as show_settings

# Configuración de la página
st.set_page_config(
    page_title="LeadBot - AI Voice Agent",
    page_icon="🤖",
    layout="wide"
)

# Sidebar para navegación
st.sidebar.title("LeadBot")
st.sidebar.markdown("*AI Voice Agent para Nutrición de Leads*")

# Selector de página
page = st.sidebar.radio(
    "Navegación",
    ["Chat", "Leads", "Configuración"]
)

# Mostrar página seleccionada
if page == "Chat":
    show_chat()
elif page == "Leads":
    show_leads()
elif page == "Configuración":
   # show_settings()
   pass

# Información adicional en el sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### Información")
st.sidebar.info(
    "LeadBot es un asistente virtual de voz que utiliza IA "
    "para interactuar con prospectos y recopilar información relevante."
)