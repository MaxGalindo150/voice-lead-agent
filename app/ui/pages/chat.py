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
except ImportError:
    # Intentar añadir la raíz del proyecto al path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
    from app.core.conversation import ConversationManager
    from app.core.llm.factory import create_llm
    from app.core.asr import WhisperASR
    from app.core.tts import TTSProcessor
    from app.db.repository import LeadRepository

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
            asr = WhisperASR(model_size="base")
            tts = TTSProcessor()
            st.session_state.conversation_manager = ConversationManager(
                llm=llm, asr=asr, tts=tts
            )
            st.session_state.lead_repo = LeadRepository()
    
    # Inicializar estado de la conversación
    if 'conversation_id' not in st.session_state:
        st.session_state.conversation_id = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'recording' not in st.session_state:
        st.session_state.recording = False
    if 'stop_recording' not in st.session_state:
        st.session_state.stop_recording = threading.Event()
    if 'audio_bytes' not in st.session_state:
        st.session_state.audio_bytes = None
    if 'lead_info' not in st.session_state:
        st.session_state.lead_info = {}
    if 'audio_stream' not in st.session_state:
        st.session_state.audio_stream = None
    if 'pyaudio_instance' not in st.session_state:
        st.session_state.pyaudio_instance = pyaudio.PyAudio()
    if 'recorder_thread' not in st.session_state:
        st.session_state.recorder_thread = None
    if 'input_mode' not in st.session_state:
        st.session_state.input_mode = "text"  # "text" o "voice"

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
                    st.audio(result["audio_response"], format="audio/mp3")
                
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
                        <div style="background-color: #dcf8c6; 
                                    border-radius: 10px; 
                                    padding: 10px; 
                                    margin-bottom: 10px;
                                    margin-left: 50px;
                                    position: relative;">
                            <span style="font-weight: bold;">Tú:</span><br>
                            {msg['content']}
                            <span style="font-size: 0.8em; 
                                        color: #888; 
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
                        <div style="background-color: #f1f0f0; 
                                    border-radius: 10px; 
                                    padding: 10px; 
                                    margin-bottom: 10px;
                                    margin-right: 50px;
                                    position: relative;">
                            <span style="font-weight: bold;">LeadBot:</span><br>
                            {msg['content']}
                            <span style="font-size: 0.8em; 
                                        color: #888; 
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

def render_chat_page():
    st.title("💬 LeadBot - Asistente Virtual")
    
    # Inicializar página
    init_chat_page()
    
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
            # Selector de modo de entrada
            mode_col1, mode_col2 = st.columns([3, 2])
            
            with mode_col1:
                st.session_state.input_mode = st.radio(
                    "Modo de entrada:",
                    options=["Texto", "Voz"],
                    horizontal=True,
                    key="input_mode_selector"
                ).lower()
            
            with mode_col2:
                if st.button("🔄 Nueva Conversación"):
                    reset_conversation()
                    st.rerun()
            
            # Interfaz según el modo seleccionado
            if st.session_state.input_mode == "texto":
                # Input de texto estilo WhatsApp
                input_col1, input_col2 = st.columns([6, 1])
                
                with input_col1:
                    st.text_input(
                        "Escribe tu mensaje...",
                        key="user_input",
                        on_change=send_text_message
                    )
                
                with input_col2:
                    if st.button("📤 Enviar", use_container_width=True):
                        send_text_message()
            else:
                # Controles de grabación de voz
                voice_col1, voice_col2, voice_col3 = st.columns([1, 1, 1])
                
                if not st.session_state.recording:
                    if voice_col1.button("🎤 Iniciar Grabación", use_container_width=True):
                        start_recording()
                else:
                    if voice_col1.button("⏹️ Detener Grabación", type="primary", use_container_width=True):
                        stop_recording()
                        process_recorded_audio()
                
                # Mostrar estado de la grabación
                if st.session_state.recording:
                    voice_col2.markdown("🔴 **Grabando...**")
                    
                    # Progreso de grabación
                    progress_placeholder = st.empty()
                    recording_start = time.time()
                    
                    while st.session_state.recording and time.time() - recording_start < MAX_RECORDING_SECONDS:
                        progress = min((time.time() - recording_start) / MAX_RECORDING_SECONDS, 1.0)
                        progress_placeholder.progress(progress)
                        time.sleep(0.1)
                    
                    if st.session_state.recording and time.time() - recording_start >= MAX_RECORDING_SECONDS:
                        stop_recording()
                        process_recorded_audio()
                        progress_placeholder.empty()
    
    # Panel lateral con información del lead
    with info_col:
        render_lead_info()

def start_recording():
    """Inicia la grabación de audio en un hilo separado"""
    if st.session_state.recording:
        return
    
    st.session_state.recording = True
    st.session_state.stop_recording.clear()
    st.session_state.frames = []
    
    # Iniciar PyAudio si no está inicializado
    if not st.session_state.pyaudio_instance:
        st.session_state.pyaudio_instance = pyaudio.PyAudio()
    
    # Crear stream de audio
    st.session_state.audio_stream = st.session_state.pyaudio_instance.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )
    
    # Iniciar hilo de grabación
    st.session_state.recorder_thread = threading.Thread(target=recording_thread)
    st.session_state.recorder_thread.daemon = True
    st.session_state.recorder_thread.start()

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
    
    st.session_state.recording = False
    st.session_state.stop_recording.set()
    
    # Esperar a que el hilo termine
    if st.session_state.recorder_thread and st.session_state.recorder_thread.is_alive():
        st.session_state.recorder_thread.join(timeout=1)
    
    # Cerrar stream si sigue abierto
    if st.session_state.audio_stream:
        st.session_state.audio_stream.stop_stream()
        st.session_state.audio_stream.close()
        st.session_state.audio_stream = None

def process_recorded_audio():
    """Procesa el audio grabado y lo envía al backend"""
    if not hasattr(st.session_state, 'frames') or not st.session_state.frames or len(st.session_state.frames) < 10:
        st.warning("La grabación es demasiado corta para procesar.")
        return
    
    audio_data = b''.join(st.session_state.frames)
    
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
                st.audio(result["audio_response"], format="audio/mp3")
            
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

# Función principal que se llama desde la app principal
def show():
    render_chat_page()

# Para pruebas directas de esta página
if __name__ == "__main__":
    show()