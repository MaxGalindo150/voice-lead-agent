# app/ui/pages/leads.py
import streamlit as st
import pandas as pd
import logging
from datetime import datetime
import sys
import os

# Asegurar que podemos importar desde el directorio raíz
try:
    from app.db.repository import LeadRepository, ConversationRepository
    from app.models.lead import Lead
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
    from app.db.repository import LeadRepository
    from app.models.lead import Lead

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def show():
    """Función principal que muestra la página de gestión de leads."""
    st.title("🧑‍💼 Gestión de Leads")
    
    # Inicializar repositorios
    if 'lead_repo' not in st.session_state:
        st.session_state.lead_repo = LeadRepository()
    
    if 'conversation_repo' not in st.session_state:
        st.session_state.conversation_repo = ConversationRepository()
    
    # Crear tabs para organizar el contenido
    tab1, tab2 = st.tabs(["📋 Lista de Leads", "📊 Detalle de Lead"])
    
    with tab1:
        mostrar_lista_leads()
    
    with tab2:
        mostrar_detalle_lead()
        
    
def mostrar_lista_leads():
    """Muestra la lista de todos los leads con filtros y búsqueda."""
    # Obtener todos los leads
    leads = st.session_state.lead_repo.get_all_leads()
    
    # Barra de búsqueda y filtros
    col1, col2 = st.columns([3, 1])
    with col1:
        busqueda = st.text_input("🔍 Buscar por nombre, empresa o email", key="busqueda_lead")
    
    with col2:
        opciones_etapa = ["Todas", "Introducción", "Recopilación", "Identificación", "Presentación", "Cierre"]
        etapa_seleccionada = st.selectbox("Etapa", opciones_etapa, key="filtro_etapa")
    
    # Convertir a DataFrame para facilitar manipulación
    if leads:
        datos_leads = []
        for lead in leads:
            datos_leads.append({
                "id": lead.id,
                "nombre": lead.nombre or "Sin nombre",
                "empresa": lead.empresa or "Sin empresa",
                "email": lead.email or "Sin email",
                "etapa": lead.conversation_stage or "introduccion",
                "actualizado": lead.updated_at.strftime("%d/%m/%Y %H:%M") if lead.updated_at else "Desconocido"
            })
        
        df_leads = pd.DataFrame(datos_leads)
        
        # Aplicar filtros
        if busqueda:
            mask = df_leads['nombre'].str.contains(busqueda, case=False, na=False)
            mask |= df_leads['empresa'].str.contains(busqueda, case=False, na=False)
            mask |= df_leads['email'].str.contains(busqueda, case=False, na=False)
            df_leads = df_leads[mask]
        
        if etapa_seleccionada != "Todas":
            # Mapear nombre amigable a valor interno
            mapping = {
                "Introducción": "introduccion",
                "Recopilación": "recopilacion_info",
                "Identificación": "identificacion_necesidades",
                "Presentación": "presentacion_solucion",
                "Cierre": "cierre"
            }
            if etapa_seleccionada in mapping:
                df_leads = df_leads[df_leads['etapa'] == mapping[etapa_seleccionada]]
        
        # Mostrar tabla con leads
        if not df_leads.empty:
            st.dataframe(
                df_leads[["nombre", "empresa", "email", "etapa", "actualizado"]],
                column_config={
                    "nombre": "Nombre",
                    "empresa": "Empresa",
                    "email": "Email",
                    "etapa": "Etapa",
                    "actualizado": "Última Actualización"
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Selección de lead para ver detalles
            selected_index = st.selectbox(
                "Selecciona un lead para ver detalles",
                options=list(range(len(df_leads))),
                format_func=lambda i: f"{df_leads.iloc[i]['nombre']} - {df_leads.iloc[i]['empresa']}",
                key="selected_lead_index"
            )
            
            if st.button("Ver Detalles", key="btn_ver_detalles"):
                lead_id = df_leads.iloc[selected_index]['id']
                st.session_state.selected_lead_id = lead_id
                st.session_state.active_tab = "detalle"
                st.rerun()
        else:
            st.info("No se encontraron leads que coincidan con los criterios de búsqueda.")
    else:
        st.info("No hay leads registrados en el sistema. Inicia una conversación desde la página de chat para crear un lead.")
        
def mostrar_detalle_lead():
    """Muestra la información detallada de un lead y sus conversaciones."""
    # Verificar si hay un lead seleccionado
    if 'selected_lead_id' not in st.session_state:
        st.info("Selecciona un lead de la lista para ver sus detalles.")
        return
    
    lead_id = st.session_state.selected_lead_id
    lead = st.session_state.lead_repo.get_lead(lead_id)
    
    if not lead:
        st.error("No se pudo cargar la información del lead.")
        return
    
    # Mostrar información del lead
    st.subheader(f"📌 {lead.nombre or 'Lead sin nombre'}")
    
    # Información principal en columnas
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Información de contacto")
        st.markdown(f"**Empresa:** {lead.empresa or 'No especificada'}")
        st.markdown(f"**Cargo:** {lead.cargo or 'No especificado'}")
        st.markdown(f"**Email:** {lead.email or 'No especificado'}")
        st.markdown(f"**Teléfono:** {lead.telefono or 'No especificado'}")
    
    with col2:
        st.markdown("#### Cualificación")
        # Mapear etapa a nombre amigable
        etapas = {
            "introduccion": "Introducción",
            "recopilacion_info": "Recopilación de información",
            "identificacion_necesidades": "Identificación de necesidades",
            "presentacion_solucion": "Presentación de solución",
            "manejo_objeciones": "Manejo de objeciones",
            "cierre": "Cierre",
            "seguimiento": "Seguimiento"
        }
        etapa = etapas.get(lead.conversation_stage, lead.conversation_stage)
        
        st.markdown(f"**Etapa actual:** {etapa}")
        st.markdown(f"**Necesidades:** {lead.necesidades or 'No especificadas'}")
        st.markdown(f"**Presupuesto:** {lead.presupuesto or 'No especificado'}")
        st.markdown(f"**Plazo:** {lead.plazo or 'No especificado'}")
        st.markdown(f"**Punto de dolor:** {lead.punto_dolor or 'No especificado'}")
    
    # Mostrar conversaciones
    st.markdown("### Historial de conversaciones")
    
    # Obtener conversaciones del lead
    try:
        conversaciones = st.session_state.conversation_repo.get_conversations_by_lead(lead_id)
        
        if not conversaciones:
            st.info("No hay conversaciones registradas para este lead.")
        else:
            opciones_conv = []
            for i, conv in enumerate(conversaciones):
                if hasattr(conv, 'created_at') and isinstance(conv.created_at, datetime):
                    fecha_str = conv.created_at.strftime("%d/%m/%Y %H:%M")
                else:
                    fecha_str = str(conv.created_at) if hasattr(conv, 'created_at') else "Desconocida"
                    
                opciones_conv.append(f"Conversación {i+1} ({fecha_str})")
            # Selector de conversación
            opciones_conv = [f"Conversación {i+1} ({conv.created_at.strftime('%d/%m/%Y %H:%M')})" 
                            for i, conv in enumerate(conversaciones)]
            
            conv_seleccionada = st.selectbox(
                "Selecciona una conversación:",
                options=list(range(len(opciones_conv))),
                format_func=lambda i: opciones_conv[i],
                key="selected_conversation_index"
            )
            
            if conv_seleccionada is not None:
                conv = conversaciones[conv_seleccionada]
                
                
                if hasattr(conv, 'created_at'):
                    if isinstance(conv.created_at, datetime):
                        st.markdown(f"**Fecha:** {conv.created_at.strftime('%d/%m/%Y %H:%M')}")
                    else:
                        st.markdown(f"**Fecha:** {str(conv.created_at)}")
                
                if hasattr(conv, 'ended_at') and conv.ended_at:
                    if isinstance(conv.ended_at, datetime):
                        st.markdown(f"**Finalizada:** {conv.ended_at.strftime('%d/%m/%Y %H:%M')}")
                    else:
                        st.markdown(f"**Finalizada:** {str(conv.ended_at)}")
                # Mostrar detalles de la conversación
                st.markdown(f"**Fecha:** {conv.created_at.strftime('%d/%m/%Y %H:%M')}")
                if conv.ended_at:
                    st.markdown(f"**Finalizada:** {conv.ended_at.strftime('%d/%m/%Y %H:%M')}")
                
                if conv.summary:
                    with st.expander("Resumen de la conversación", expanded=False):
                        st.markdown(conv.summary)
                
                # Mostrar mensajes
                st.markdown("#### Mensajes")
                
                for msg in conv.messages:
                    # Color según el remitente
                    
                    timestamp_str = ""
                    if hasattr(msg, 'timestamp'):
                        if isinstance(msg.timestamp, datetime):
                            timestamp_str = msg.timestamp.strftime("%H:%M:%S")
                        else:
                            timestamp_str = str(msg.timestamp)
                            
                    color = "#454545" if msg.role == "user" else "#054640"
                    align = "right" if msg.role == "user" else "left"
                    
                    st.markdown(
                        f"""
                        <div style="
                            background-color: {color}; 
                            padding: 10px; 
                            border-radius: 10px; 
                            margin: 5px 0;
                            text-align: {align};
                        ">
                            <strong>{"Usuario" if msg.role == "user" else "LeadBot"}:</strong> {msg.content}
                            <div style="font-size: 0.8em; color: gray;">
                                {timestamp_str}
                            </div>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                
                # Botón para continuar la conversación
                if st.button("Continuar esta conversación", key="btn_continuar_conv"):
                    st.session_state.redirect_to_chat = True
                    st.session_state.conversation_id = conv.id
                    st.session_state.lead_id = lead_id
                    st.session_state.page = "Chat"
                    st.rerun()
    except Exception as e:
        st.error(f"Error al cargar las conversaciones: {str(e)}")
    
    # Botones de acción
    st.divider()
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📝 Editar Lead", key="btn_editar", use_container_width=True):
            st.session_state.edit_lead = True
            st.rerun()
    
    with col2:
        if st.button("❌ Eliminar Lead", key="btn_eliminar", use_container_width=True):
            st.session_state.confirm_delete = True
            st.rerun()
    
    # Modal de confirmación de eliminación
    if 'confirm_delete' in st.session_state and st.session_state.confirm_delete:
        st.warning(f"¿Estás seguro de que deseas eliminar el lead {lead.nombre}? Esta acción no se puede deshacer.")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Sí, eliminar", key="btn_confirm_delete"):
                if st.session_state.lead_repo.delete_lead(lead_id):
                    st.success("Lead eliminado correctamente.")
                    # Limpiar estado
                    if 'selected_lead_id' in st.session_state:
                        del st.session_state.selected_lead_id
                    if 'confirm_delete' in st.session_state:
                        del st.session_state.confirm_delete
                    st.rerun()
                else:
                    st.error("Error al eliminar el lead.")
        
        with col2:
            if st.button("No, cancelar", key="btn_cancel_delete"):
                del st.session_state.confirm_delete
                st.rerun()
    
    # Modal de edición
    if 'edit_lead' in st.session_state and st.session_state.edit_lead:
        mostrar_formulario_edicion(lead)
        
def mostrar_formulario_edicion(lead):
    """Muestra un formulario para editar la información de un lead."""
    st.subheader("✏️ Editar Lead")
    
    with st.form("form_editar_lead"):
        # Información básica
        nombre = st.text_input("Nombre", value=lead.nombre or "")
        empresa = st.text_input("Empresa", value=lead.empresa or "")
        
        col1, col2 = st.columns(2)
        with col1:
            cargo = st.text_input("Cargo", value=lead.cargo or "")
        with col2:
            email = st.text_input("Email", value=lead.email or "")
        
        telefono = st.text_input("Teléfono", value=lead.telefono or "")
        
        # Información de cualificación
        st.subheader("Información de cualificación")
        
        necesidades = st.text_area("Necesidades", value=lead.necesidades or "")
        
        col1, col2 = st.columns(2)
        with col1:
            presupuesto = st.text_input("Presupuesto", value=lead.presupuesto or "")
        with col2:
            plazo = st.text_input("Plazo", value=lead.plazo or "")
        
        punto_dolor = st.text_area("Punto de dolor", value=lead.punto_dolor or "")
        
        # Etapa de conversación
        etapas = {
            "introduccion": "Introducción",
            "recopilacion_info": "Recopilación de información",
            "identificacion_necesidades": "Identificación de necesidades",
            "presentacion_solucion": "Presentación de solución",
            "manejo_objeciones": "Manejo de objeciones",
            "cierre": "Cierre",
            "seguimiento": "Seguimiento"
        }
        
        # Obtener el índice de la etapa actual
        etapa_actual = lead.conversation_stage or "introduccion"
        etapas_list = list(etapas.keys())
        etapa_idx = etapas_list.index(etapa_actual) if etapa_actual in etapas_list else 0
        
        # Selector de etapa
        etapa = st.selectbox(
            "Etapa de conversación",
            options=etapas_list,
            format_func=lambda x: etapas.get(x, x),
            index=etapa_idx
        )
        
        # Botones de acción
        submitted = st.form_submit_button("Guardar cambios")
        
        if submitted:
            # Preparar datos actualizados
            updates = {
                "nombre": nombre,
                "empresa": empresa,
                "cargo": cargo,
                "email": email,
                "telefono": telefono,
                "necesidades": necesidades,
                "presupuesto": presupuesto,
                "plazo": plazo,
                "punto_dolor": punto_dolor,
                "conversation_stage": etapa,
                "updated_at": datetime.now()
            }
            
            # Actualizar lead
            if st.session_state.lead_repo.update_lead(lead.id, updates):
                st.success("Lead actualizado correctamente.")
                # Limpiar estado
                if 'edit_lead' in st.session_state:
                    del st.session_state.edit_lead
                st.rerun()
            else:
                st.error("Error al actualizar el lead.")
    
    # Botón para cancelar
    if st.button("Cancelar", key="btn_cancel_edit"):
        del st.session_state.edit_lead
        st.rerun()

# Función principal para ejecutar esta página de forma independiente
# if __name__ == "__main__":
#     show()