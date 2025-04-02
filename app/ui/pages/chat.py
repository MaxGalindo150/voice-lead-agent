# app/ui/pages/chat.py
import streamlit as st
import pyaudio
import logging
import sys
import wave
import tempfile
import os
import time
import numpy as np
from io import BytesIO
import threading
import uuid


# Configurar logging básico
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

try:
    from app.core.conversation import ConversationManager
    from app.core.llm.factory import create_llm
    from app.core.asr import WhisperASR
    from app.core.tts import TTSProcessor
    from app.db.repository import LeadRepository
    from app.db.repository import ConversationRepository
    from app.utils.audio import StreamlitAudioRecorder
except ImportError:
    # Intentar añadir la raíz del proyecto al path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
    from app.core.conversation import ConversationManager
    from app.core.llm.factory import create_llm
    from app.core.asr import WhisperASR
    from app.core.tts import TTSProcessor
    from app.db.repository import LeadRepository
    from app.db.repository import ConversationRepository
    from app.utils.audio import StreamlitAudioRecorder

# Configuraciones de audio
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
MAX_RECORDING_SECONDS = 15

def init_chat_page():
    # Inicializar componentes si no están en caché
    if 'conversation_manager' not in st.session_state:
        with st.spinner("Inicializando componentes..."):
            llm = create_llm("openai")  # O el modelo que uses
            asr = WhisperASR(model_size="turbo")
            tts = TTSProcessor()
            st.session_state.conversation_manager = ConversationManager(
                llm=llm, asr=asr, tts=tts
            )
            st.session_state.lead_repo = LeadRepository()
            st.session_state.conversation_repo = ConversationRepository()
    
    # Inicializar estado de la conversación
    if 'conversation_id' not in st.session_state:
        st.session_state.conversation_id = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'recording' not in st.session_state:
        st.session_state.recording = False
    if 'lead_info' not in st.session_state:
        st.session_state.lead_info = {}
    if 'pyaudio_instance' not in st.session_state:
        st.session_state.pyaudio_instance = pyaudio.PyAudio()
    if 'audio_recorder' not in st.session_state:
        st.session_state.audio_recorder = StreamlitAudioRecorder()
    
    # Aseguramos que el audio_recorder esté correctamente inicializado
    if st.session_state.recording and st.session_state.audio_recorder.stream is None:
        st.session_state.recording = False

    if 'redirect_to_chat' in st.session_state and st.session_state.redirect_to_chat:
        # Cargar la conversación existente
        if st.session_state.conversation_id:
            try:
                # Obtener la conversación y sus mensajes
                conversation = st.session_state.conversation_repo.get_conversation(
                    st.session_state.conversation_id
                )
                
                # Si hay mensajes existentes, cargarlos
                if conversation and hasattr(conversation, 'messages'):
                    st.session_state.messages = []
                    for msg in conversation.messages:
                        st.session_state.messages.append({
                            "role": msg.role,
                            "content": msg.content
                        })
                
                # Si hay información de lead, cargarla
                if 'lead_id' in st.session_state and st.session_state.lead_id:
                    lead = st.session_state.lead_repo.get_lead(st.session_state.lead_id)
                    if lead:
                        st.session_state.lead_info = lead.__dict__
            except Exception as e:
                st.error(f"Error al cargar la conversación: {str(e)}")
            
        # Limpiar el estado de redirección para evitar recargas
        st.session_state.redirect_to_chat = False
    
def send_text_message():
    """Envía un mensaje de texto al asistente"""
    if st.session_state.user_input and st.session_state.user_input.strip():
        user_text = st.session_state.user_input
        st.session_state.user_input = ""  # Limpiar el campo
        
        # Iniciar conversación si es la primera interacción
        if not st.session_state.conversation_id:
            st.session_state.conversation_id = st.session_state.conversation_manager.start_conversation()
        
        # Añadir mensaje del usuario al historial
        st.session_state.messages.append({
            "role": "user",
            "content": user_text
        })
        
        # Procesar mensaje de texto
        with st.spinner("Procesando mensaje..."):
            try:
                result = st.session_state.conversation_manager.process_text_message(
                    st.session_state.conversation_id, user_text
                )
                
                # Mostrar respuesta del asistente
                if result.get("assistant_response"):
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result["assistant_response"]
                    })
                
                # Reproducir respuesta de audio si está disponible
                if result.get("audio_response"):
                    st.audio(result["audio_response"], format="audio/mp3", autoplay=True)
                
                # Actualizar información del lead
                if result.get("lead_info"):
                    st.session_state.lead_info.update(result["lead_info"])
                
            except Exception as e:
                st.error(f"Error al procesar el mensaje: {str(e)}")

def render_chat_messages():
    """Renderiza los mensajes del chat con mejor estilo"""
    if not st.session_state.messages:
        st.info("🤖 Bienvenido al asistente virtual LeadBot. ¿En qué puedo ayudarte hoy?")
        return
    
    # Contenedor para los mensajes
    messages_container = st.container()
    
    with messages_container:
        for i, msg in enumerate(st.session_state.messages):
            if msg["role"] == "user":
                # Estilo para mensajes del usuario
                col1, col2 = st.columns([6, 1])
                with col1:
                    st.markdown(
                        f"""
                        <div style="background-color: #054640; 
                                    border-radius: 10px; 
                                    padding: 10px; 
                                    margin-bottom: 10px;
                                    margin-left: 50px;
                                    position: relative;">
                            <span style="font-weight: bold;">Tú:</span><br>
                            {msg['content']}
                            <span style="font-size: 0.8em; 
                                        color: #ffff; 
                                        position: absolute; 
                                        bottom: 5px; 
                                        right: 10px;">
                                {time.strftime('%H:%M')}
                            </span>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
            else:
                # Estilo para mensajes del asistente
                col1, col2 = st.columns([1, 6])
                with col2:
                    st.markdown(
                        f"""
                        <div style="background-color: #454545; 
                                    border-radius: 10px; 
                                    padding: 10px; 
                                    margin-bottom: 10px;
                                    margin-right: 50px;
                                    position: relative;">
                            <span style="font-weight: bold;">LeadBot:</span><br>
                            {msg['content']}
                            <span style="font-size: 0.8em; 
                                        color: #ffff; 
                                        position: absolute; 
                                        bottom: 5px; 
                                        right: 10px;">
                                {time.strftime('%H:%M')}
                            </span>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
    
    # Desplazar automáticamente al último mensaje
    st.markdown(
        """
        <script>
            var element = document.getElementsByClassName('stChatInputContainer')[0];
            element.scrollIntoView({behavior: "smooth"});
        </script>
        """,
        unsafe_allow_html=True
    )

def render_lead_info():
    """Renderiza la información del lead con mejor estilo"""
    if not st.session_state.lead_info:
        return
    
    st.divider()
    st.subheader("📊 Información del Lead")
    
    with st.expander("Ver detalles del lead", expanded=True):
        col1, col2 = st.columns(2)
        
        # Columna 1: Información básica
        with col1:
            st.markdown("**👤 Información de contacto:**")
            for field, label in [
                ("nombre", "Nombre"), 
                ("empresa", "Empresa"), 
                ("cargo", "Cargo"), 
                ("email", "Email"), 
                ("telefono", "Teléfono")
            ]:
                if field in st.session_state.lead_info and st.session_state.lead_info[field]:
                    st.markdown(f"- **{label}:** {st.session_state.lead_info[field]}")
        
        # Columna 2: Información de cualificación
        with col2:
            st.markdown("**🎯 Información de cualificación:**")
            for field, label in [
                ("necesidades", "Necesidades"), 
                ("presupuesto", "Presupuesto"), 
                ("plazo", "Plazo"), 
                ("punto_dolor", "Puntos de dolor"), 
                ("producto_interes", "Productos de interés")
            ]:
                if field in st.session_state.lead_info and st.session_state.lead_info[field]:
                    st.markdown(f"- **{label}:** {st.session_state.lead_info[field]}")
        
        # Etapa de la conversación
        if "conversation_stage" in st.session_state.lead_info:
            stage = st.session_state.lead_info['conversation_stage']
            stage_colors = {
                "introduccion": "blue",
                "recopilacion_info": "green",
                "identificacion_necesidades": "orange",
                "presentacion_solucion": "purple",
                "manejo_objeciones": "red",
                "cierre": "teal",
                "seguimiento": "violet"
            }
            color = stage_colors.get(stage, "gray")
            
            st.markdown(f"""
                <div style="background-color: {color}; 
                            color: white; 
                            padding: 5px 10px; 
                            border-radius: 5px; 
                            display: inline-block;
                            margin-top: 10px;">
                    Etapa actual: {stage.capitalize()}
                </div>
                """, 
                unsafe_allow_html=True
            )


def reproduce_audio(audio_bytes):
    """Reproduce el audio recibido"""
    if audio_bytes:
        st.audio(audio_bytes, format="audio/mp3", autoplay=True)

def reset_conversation():
    """Reinicia la conversación actual"""
    # Finalizar la conversación anterior si existe
    if st.session_state.conversation_id:
        try:
            st.session_state.conversation_manager.end_conversation(
                st.session_state.conversation_id
            )
        except:
            pass
    
    # Reiniciar estados
    st.session_state.conversation_id = None
    st.session_state.messages = []
    st.session_state.lead_info = {}
    
    # Detener grabación si está activa
    if st.session_state.recording:
        stop_recording()
    
    # Limpiar recursos del grabador
    if 'audio_recorder' in st.session_state:
        st.session_state.audio_recorder.close()
        # Crear un nuevo grabador
        st.session_state.audio_recorder = StreamlitAudioRecorder()
        
def render_chat_page():
    st.title("💬 LeadBot - Asistente Virtual")
    
    # Inicializar página
    init_chat_page()
    
    # Limpiar estados de botones para evitar duplicación
    if 'button_pressed' in st.session_state:
        del st.session_state.button_pressed
    
    # Dividir la página en dos secciones: chat e info
    chat_col, info_col = st.columns([3, 1])
    
    with chat_col:
        # Container para mensajes de chat
        chat_container = st.container(height=500)
        
        with chat_container:
            render_chat_messages()
        
        # Container para controles
        control_container = st.container()
        
        with control_container:
            # Botón de nueva conversación en la esquina superior derecha
            if st.button("🔄 Nueva Conversación"):
                reset_conversation()
                st.rerun()
            
            # Interfaz unificada de texto con micrófono
            input_col1, input_col2, input_col3 = st.columns([5, 1, 1])
            
            with input_col1:
                st.text_input(
                    "Escribe tu mensaje...",
                    key="user_input",
                    on_change=send_text_message
                )
            
            with input_col2:
                # Botón de enviar mensaje de texto
                if st.button("📤", use_container_width=True, help="Enviar mensaje"):
                    send_text_message()
            
            with input_col3:
                # Botón de grabación que cambia según el estado
                # button_key = str(uuid.uuid4())  # Generar una clave única para evitar duplicación de eventos
                
                if not st.session_state.recording:
                    if st.button("🎤", key=f"mic_btn", use_container_width=True, help="Grabar audio"):
                        # Evitar procesamiento duplicado
                        if not ('button_pressed' in st.session_state and st.session_state.button_pressed == 'start_recording'):
                            st.session_state.button_pressed = 'start_recording'
                            start_recording()
                            st.session_state.recording = True
                            st.rerun()
                else:
                    if st.button("⏹️", key=f"stop_btn", use_container_width=True, help="Detener grabación", type="primary"):
                        # Evitar procesamiento duplicado
                        if not ('button_pressed' in st.session_state and st.session_state.button_pressed == 'stop_recording'):
                            st.session_state.button_pressed = 'stop_recording'
                            stop_recording()
                            process_recorded_audio()
                            if 'audio_response' in st.session_state:
                                st.session_state.last_audio_response = st.session_state.audio_response
                            st.session_state.recording = False
                            st.rerun()
                
                if 'last_audio_response' in st.session_state and st.session_state.last_audio_response:
                    st.audio(st.session_state.last_audio_response, format="audio/mp3", autoplay=True)
            
            # Mostrar estado de la grabación
            if st.session_state.recording:
                st.markdown("🔴 **Grabando...**")
                
                # Progreso de grabación
                progress_placeholder = st.empty()
                
                # Calcular el progreso
                elapsed_time = time.time() - st.session_state.recording_start_time
                progress = min(elapsed_time / MAX_RECORDING_SECONDS, 1.0)
                progress_placeholder.progress(progress)
                
                # Detener automáticamente si llega al tiempo máximo
                if elapsed_time >= MAX_RECORDING_SECONDS and not ('processing_audio' in st.session_state and st.session_state.processing_audio):
                    stop_recording()
                    process_recorded_audio()
                    # No usamos st.rerun() aquí para evitar duplicación
    
    # Panel lateral con información del lead
    with info_col:
        render_lead_info()
        
def start_recording():
    """Inicia la grabación de audio"""
    if st.session_state.recording:
        return
    
    # Iniciar grabación
    success = st.session_state.audio_recorder.start_recording()
    
    if success:
        st.session_state.recording = True
        # Inicializar el tiempo de inicio
        st.session_state.recording_start_time = time.time()
    else:
        st.error("Error al iniciar la grabación")

def recording_thread():
    """Función que se ejecuta en un hilo para grabar audio"""
    try:
        st.session_state.frames = []
        while st.session_state.recording and not st.session_state.stop_recording.is_set():
            data = st.session_state.audio_stream.read(CHUNK, exception_on_overflow=False)
            st.session_state.frames.append(data)
    except Exception as e:
        print(f"Error en grabación: {e}")
    finally:
        if st.session_state.audio_stream:
            st.session_state.audio_stream.stop_stream()
            st.session_state.audio_stream.close()
            st.session_state.audio_stream = None

def stop_recording():
    """Detiene la grabación de audio"""
    if not st.session_state.recording:
        return
    
    # Detener grabación
    st.session_state.audio_recorder.stop_recording()
    st.session_state.recording = False
    
    # Limpiar el tiempo de inicio
    if 'recording_start_time' in st.session_state:
        del st.session_state.recording_start_time

    
def process_recorded_audio():
    """Procesa el audio grabado y lo envía al backend"""
    audio_data = st.session_state.audio_recorder.get_audio_data()
    
    if audio_data is None or len(audio_data) < 1000:  # Al menos 1KB
        st.warning("La grabación es demasiado corta para procesar.")
        return
    
    # Guardar temporalmente el audio para procesarlo
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
        temp_filename = temp_file.name
        
        # Guardar como WAV
        wf = wave.open(temp_filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(st.session_state.pyaudio_instance.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(audio_data)
        wf.close()
        
        # Leer el archivo en bytes
        with open(temp_filename, 'rb') as f:
            audio_bytes = f.read()
    
    # Iniciar conversación si es la primera interacción
    if not st.session_state.conversation_id:
        st.session_state.conversation_id = st.session_state.conversation_manager.start_conversation()
    
    # Procesar el audio
    with st.spinner("Procesando audio..."):
        try:
            result = st.session_state.conversation_manager.process_audio_message(
                st.session_state.conversation_id, audio_bytes
            )
            
            # Mostrar transcripción
            if result.get("transcription") and result["transcription"].get("text"):
                transcription = result["transcription"]["text"]
                st.session_state.messages.append({
                    "role": "user",
                    "content": transcription
                })
            
            # Mostrar respuesta del asistente
            if result.get("assistant_response"):
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["assistant_response"]
                })
            
            # Reproducir respuesta de audio
            if result.get("audio_response"):
                st.session_state.audio_response = result["audio_response"]
                st.audio(result["audio_response"], format="audio/mp3", autoplay=True)
            
            # Actualizar información del lead
            if result.get("lead_info"):
                st.session_state.lead_info.update(result["lead_info"])
            
        except Exception as e:
            st.error(f"Error al procesar el audio: {str(e)}")
    
    # Limpiar archivo temporal
    try:
        os.unlink(temp_filename)
    except:
        pass
    
# Función principal que se llama desde la app principal
def show():
    render_chat_page()

# Para pruebas directas de esta página
if __name__ == "__main__":
    show()