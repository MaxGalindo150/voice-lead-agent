# scripts/test_conversation_flow.py
import os
import argparse
import wave
import pyaudio
import time
import signal
import logging
import subprocess
import tempfile
from threading import Thread, Event

from app.core.llm.factory import create_llm
from app.core.asr import WhisperASR
from app.core.tts import TTSProcessor
from app.core.conversation import ConversationManager

# Configuración de logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuración de grabación de audio
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
MAX_RECORDING_SECONDS = 30
TEMP_AUDIO_FILE = "temp_user_input.wav"

def preprocess_audio_with_ffmpeg(input_file, output_file):
    """
    Pre-procesa el archivo de audio con FFmpeg para asegurar compatibilidad con Whisper.
    
    Args:
        input_file: Ruta al archivo de audio de entrada
        output_file: Ruta al archivo de audio de salida
        
    Returns:
        bool: True si el proceso fue exitoso, False en caso contrario
    """
    try:
        # La opción -y sobreescribe el archivo de salida si ya existe
        # Convertimos a 16kHz, 16bit, mono WAV
        cmd = [
            'ffmpeg', '-y', '-i', input_file, 
            '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le', 
            '-f', 'wav', output_file
        ]
        
        logger.info(f"Ejecutando FFmpeg: {' '.join(cmd)}")
        
        # Ejecutamos FFmpeg con captura de salida
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False  # No lanzar excepción si falla
        )
        
        # Verificar si el proceso fue exitoso
        if process.returncode != 0:
            logger.error(f"Error en FFmpeg: {process.stderr}")
            return False
        
        logger.info(f"Audio convertido correctamente: {output_file}")
        return True
    except Exception as e:
        logger.error(f"Error al pre-procesar audio: {e}")
        return False

class AudioRecorder:
    """Grabador de audio simple."""
    
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.frames = []
        self.is_recording = False
        self.thread = None
        self.stop_event = Event()
    
    def start_recording(self):
        """Inicia la grabación de audio."""
        self.is_recording = True
        self.frames = []
        self.stop_event.clear()
        self.thread = Thread(target=self._record)
        self.thread.daemon = True
        self.thread.start()
        logger.info("Grabación iniciada.")
    
    def stop_recording(self):
        """Detiene la grabación de audio."""
        if self.is_recording:
            self.is_recording = False
            self.stop_event.set()
            if self.thread:
                self.thread.join(timeout=2)
            logger.info("Grabación detenida.")
    
    def _record(self):
        """Función interna para grabar audio."""
        try:
            stream = self.p.open(format=FORMAT,
                                channels=CHANNELS,
                                rate=RATE,
                                input=True,
                                frames_per_buffer=CHUNK)
            
            while self.is_recording and not self.stop_event.is_set():
                data = stream.read(CHUNK, exception_on_overflow=False)
                self.frames.append(data)
            
            stream.stop_stream()
            stream.close()
        except Exception as e:
            logger.error(f"Error en grabación: {e}")
            self.is_recording = False
    
    def save_audio(self, filename):
        """Guarda el audio grabado en un archivo WAV."""
        if not self.frames:
            logger.warning("No hay audio para guardar")
            return None
        
        try:
            # Verificar que los frames no estén vacíos
            audio_data = b''.join(self.frames)
            if len(audio_data) < 100:
                logger.warning("La grabación de audio es demasiado corta")
                return None
                
            wf = wave.open(filename, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(self.p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(audio_data)
            wf.close()
            
            # Verificar que el archivo se creó correctamente
            if os.path.exists(filename) and os.path.getsize(filename) > 1000:  # Al menos 1KB
                logger.info(f"Audio guardado: {filename} ({os.path.getsize(filename)} bytes)")
                return audio_data
            else:
                logger.warning(f"El archivo guardado es demasiado pequeño: {os.path.getsize(filename)} bytes")
                return None
        except Exception as e:
            logger.error(f"Error al guardar el audio: {e}")
            return None
    
    def close(self):
        """Libera recursos."""
        self.stop_recording()
        self.p.terminate()
        logger.info("Recursos de audio liberados.")

def play_audio(audio_data):
    """Reproduce audio desde bytes, detectando automáticamente si es MP3 o WAV."""
    if not audio_data:
        logger.warning("No hay audio para reproducir")
        return
        
    # Guardar en archivo temporal con extensión .tmp para poder detectar el tipo
    with tempfile.NamedTemporaryFile(suffix='.tmp', delete=False) as temp_file:
        temp_filename = temp_file.name
        temp_file.write(audio_data)
    
    try:
        # Detectar el formato basado en los primeros bytes
        if audio_data.startswith(b'ID3') or audio_data.startswith(b'\xff\xfb'):
            # Es un archivo MP3
            logger.info("Detectado formato MP3")
            # Usar ffplay para reproducir MP3
            subprocess.run(
                ['ffplay', '-autoexit', '-nodisp', temp_filename], 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
            logger.info("Audio MP3 reproducido correctamente")
        elif audio_data.startswith(b'RIFF'):
            # Es un archivo WAV
            logger.info("Detectado formato WAV")
            # Reproducir usando pyaudio
            p = pyaudio.PyAudio()
            wf = wave.open(temp_filename, 'rb')
            stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                            channels=wf.getnchannels(),
                            rate=wf.getframerate(),
                            output=True)
            
            data = wf.readframes(CHUNK)
            while len(data) > 0:
                stream.write(data)
                data = wf.readframes(CHUNK)
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            logger.info("Audio WAV reproducido correctamente")
        else:
            # Formato desconocido, intentar con ffplay genérico
            logger.warning("Formato de audio desconocido, intentando con ffplay")
            subprocess.run(
                ['ffplay', '-autoexit', '-nodisp', temp_filename], 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
            logger.info("Audio reproducido correctamente")
    except Exception as e:
        logger.error(f"Error reproduciendo audio: {e}")
    finally:
        # Limpiar archivo temporal
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
            

def signal_handler(sig, frame):
    """Manejador de señales para Ctrl+C"""
    global recorder_instance, recording_active
    if recording_active and recorder_instance:
        logger.info("Detención de grabación solicitada por el usuario (Ctrl+C)")
        recorder_instance.stop_recording()
        recording_active = False
    else:
        logger.info("Saliendo del programa (Ctrl+C)")
        if recorder_instance:
            recorder_instance.close()
        
        # Limpieza de archivos temporales
        for file in [TEMP_AUDIO_FILE, "temp_processed.wav"]:
            if os.path.exists(file) and os.path.isfile(file):
                os.remove(file)
        exit(0)

def main():
    global recorder_instance, recording_active
    
    parser = argparse.ArgumentParser(description='Probar el flujo de conversación completo')
    parser.add_argument('--model', default='base', 
                        choices=['tiny', 'base', 'small', 'medium', 'large', 'turbo'],
                        help='Tamaño del modelo Whisper (default: base)')
    parser.add_argument('--max-time', type=int, default=30,
                       help='Tiempo máximo de grabación en segundos (default: 30)')
    parser.add_argument('--debug', action='store_true',
                       help='Activar modo debug con más información')
    parser.add_argument('--no-ffmpeg', action='store_true',
                       help='No usar FFmpeg para pre-procesar el audio')
    
    args = parser.parse_args()
    
    # Configurar nivel de logging
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Configurar manejador de señales para Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Inicializar componentes
    logger.info("Inicializando componentes...")
    try:
        llm = create_llm("openai")
        asr = WhisperASR(model_size=args.model)
        tts = TTSProcessor()
        
        # Crear gestor de conversaciones
        conversation_manager = ConversationManager(llm=llm, asr=asr, tts=tts)
        
        # Iniciar conversación
        conversation_id = conversation_manager.start_conversation()
        logger.info(f"Conversación iniciada con ID: {conversation_id}")
        
        # Crear recorder
        recorder_instance = AudioRecorder()
        recording_active = False
        
        # Mensaje inicial del asistente
        initial_message = "Hola, soy LeadBot, tu asistente virtual. ¿Con quién tengo el gusto de hablar?"
        print(f"\nAsistente: {initial_message}")
        
        # Loop de conversación
        while True:
            # Grabar audio
            print("\nPresiona Enter para empezar a hablar...")
            input()
            
            recording_active = True
            recorder_instance.start_recording()
            
            # Esperar a que el usuario detenga la grabación con Ctrl+C o timeout
            print(f"Grabando... (presiona Ctrl+C cuando termines de hablar, máx. {args.max_time} segundos)")
            recording_start_time = time.time()
            
            # Esperar a que el usuario detenga la grabación o timeout
            while recording_active and (time.time() - recording_start_time) < args.max_time:
                time.sleep(0.2)
                
            # Si no se detuvo manualmente, detener la grabación después del tiempo máximo
            if recording_active:
                print(f"\nTiempo máximo de grabación alcanzado ({args.max_time} segundos)")
                recorder_instance.stop_recording()
                recording_active = False
            
            # Guardar y procesar el audio
            print("Procesando audio...")
            audio_data = recorder_instance.save_audio(TEMP_AUDIO_FILE)
            
            # Solo procesar si el audio es válido
            if audio_data and len(audio_data) > 1000:  # Al menos 1KB
                try:
                    # Crear un archivo temporal para el audio procesado si estamos usando FFmpeg
                    audio_file_to_process = TEMP_AUDIO_FILE
                    
                    # Pre-procesar el audio con FFmpeg si está activado
                    if not args.no_ffmpeg:
                        processed_file = "temp_processed.wav"
                        if preprocess_audio_with_ffmpeg(TEMP_AUDIO_FILE, processed_file):
                            audio_file_to_process = processed_file
                            # Leer el archivo procesado
                            with open(processed_file, 'rb') as f:
                                audio_data = f.read()
                        else:
                            print("No se pudo pre-procesar el audio. Intentando con el archivo original...")
                    
                    # Procesar mensaje de audio
                    result = conversation_manager.process_audio_message(conversation_id, audio_data)
                    
                    # Verificar si hubo error en la transcripción
                    if "error" in result:
                        print(f"\nError: {result['error']}")
                        if "details" in result:
                            print(f"Detalles: {result['details']}")
                            
                        # Si hay un error específico con FFmpeg, intentar con el archivo original
                        if "ffmpeg" in str(result.get('details', '')).lower() and not args.no_ffmpeg:
                            print("\nIntentando un enfoque alternativo...")
                            
                            # Intentar con otra estrategia: cargar directamente el archivo con Whisper
                            try:
                                # Modificar el comportamiento para leer directamente del archivo
                                direct_result = asr._model.transcribe(audio_file_to_process)
                                text = direct_result["text"].strip()
                                
                                if text:
                                    print(f"\nTranscripción alternativa: {text}")
                                    # Procesar el texto transcrito manualmente
                                    text_result = conversation_manager.process_text_message(conversation_id, text)
                                    print(f"\nAsistente: {text_result['assistant_response']}")
                                    
                                    # Reproducir respuesta
                                    if text_result.get('audio_response'):
                                        print("Reproduciendo respuesta...")
                                        play_audio(text_result['audio_response'])
                                    
                                    # Mostrar información del lead (para debug)
                                    if text_result.get('lead_info'):
                                        print("\nInformación del lead:")
                                        for key, value in text_result['lead_info'].items():
                                            print(f"  {key}: {value}")
                                    
                                    print(f"\nEtapa actual: {text_result.get('stage', 'desconocida')}")
                                else:
                                    print("No se pudo obtener transcripción alternativa.")
                            except Exception as e:
                                logger.error(f"Error en transcripción alternativa: {e}", exc_info=True)
                                print(f"Error en enfoque alternativo: {e}")
                        
                        continue
                    
                    # Mostrar transcripción
                    if "transcription" in result and "text" in result["transcription"]:
                        print(f"\nTranscripción: {result['transcription']['text']}")
                    else:
                        print("\nNo se pudo obtener la transcripción del audio.")
                        continue
                    
                    # Mostrar respuesta del asistente
                    if "assistant_response" in result:
                        print(f"\nAsistente: {result['assistant_response']}")
                    else:
                        print("\nNo se obtuvo respuesta del asistente.")
                        continue
                    
                    # Reproducir respuesta
                    if result.get('audio_response'):
                        print("Reproduciendo respuesta...")
                        play_audio(result['audio_response'])
                    
                    # Mostrar información del lead (para debug)
                    if result.get('lead_info'):
                        print("\nInformación del lead:")
                        for key, value in result['lead_info'].items():
                            print(f"  {key}: {value}")
                    
                    print(f"\nEtapa actual: {result.get('stage', 'desconocida')}")
                    
                except Exception as e:
                    logger.error(f"Error al procesar el mensaje de audio: {e}", exc_info=True)
                    print(f"\nError inesperado al procesar el audio: {e}")
                finally:
                    # Limpiar archivos temporales de procesamiento
                    if os.path.exists("temp_processed.wav"):
                        os.remove("temp_processed.wav")
            else:
                print("No se pudo procesar el audio. Por favor, intenta de nuevo y habla más claramente.")
                continue
            
            # Preguntar si quiere continuar
            print("\n¿Continuar conversación? (s/n)")
            choice = input().lower()
            if choice != 's' and choice != 'si' and choice != 'yes':
                break
    
    except Exception as e:
        logger.error(f"Error inesperado: {e}", exc_info=True)
        print(f"Error inesperado: {e}")
    
    finally:
        # Limpiar recursos
        logger.info("Limpiando recursos...")
        if recorder_instance:
            recorder_instance.close()
        
        # Limpiar archivos temporales
        for file in [TEMP_AUDIO_FILE, "temp_processed.wav"]:
            if os.path.exists(file) and os.path.isfile(file):
                try:
                    os.remove(file)
                except:
                    pass
        
        # Finalizar conversación
        try:
            if 'conversation_manager' in locals() and 'conversation_id' in locals():
                conversation_manager.end_conversation(conversation_id)
                logger.info("Conversación finalizada.")
        except Exception as e:
            logger.error(f"Error al finalizar la conversación: {e}")
        
        print("Programa finalizado.")

if __name__ == "__main__":
    # Variables globales para el manejador de señales
    recorder_instance = None
    recording_active = False
    
    main()