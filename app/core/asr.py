# core/asr.py
import os
import tempfile
import logging
from typing import Optional, Dict, Any

from app import config

logger = logging.getLogger(__name__)

class WhisperASR:
    """
    Implementación de reconocimiento automático de voz utilizando Whisper localmente.
    """
    
    def __init__(self, model_size: str = None):
        """
        Inicializa el sistema ASR de Whisper.
        
        Args:
            model_size (str, optional): Tamaño del modelo Whisper a usar ('tiny', 'base', 'small', 
                                       'medium', 'large', 'turbo'). Por defecto, el definido en config.
        """
        self.model_size = model_size or config.WHISPER_MODEL_SIZE
        
        # Modelo de Whisper
        self.model = None
        
        # Inicializar modelo
        self._initialize_model()
    
    def _initialize_model(self):
        """
        Inicializa el modelo Whisper localmente.
        """
        try:
            import whisper
            
            logger.info(f"Cargando modelo Whisper {self.model_size}...")
            self.model = whisper.load_model(self.model_size)
            logger.info(f"Modelo Whisper {self.model_size} cargado correctamente")
            
        except ImportError:
            logger.error("La biblioteca 'whisper' no está instalada. Instala con: pip install openai-whisper")
            raise
        except Exception as e:
            logger.error(f"Error al inicializar el modelo Whisper: {str(e)}")
            raise
    
    def transcribe(self, audio_data: bytes, language: str = "es") -> Dict[str, Any]:
        """
        Transcribe audio a texto utilizando Whisper.
        
        Args:
            audio_data (bytes): Datos de audio en formato compatible
            language (str): Código de idioma para la transcripción
            
        Returns:
            Dict[str, Any]: Resultado de la transcripción con el texto y metadatos
        """
        if not self.model:
            error_msg = "Modelo Whisper no inicializado"
            logger.error(error_msg)
            return {"error": error_msg, "text": "", "success": False}
        
        # Crear un archivo temporal para guardar los datos de audio
        temp_file_path = None
        
        try:
            # Guardar el audio en un archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            # Opciones de transcripción
            options = {
                "language": language,
                "task": "transcribe"
            }
            
            # Realizar la transcripción
            result = self.model.transcribe(temp_file_path, **options)
            
            # Construir respuesta
            response = {
                "text": result["text"],
                "model": f"whisper-{self.model_size}",
                "language": language,
                "segments": result.get("segments", []),
                "success": True
            }
            
            logger.info(f"Transcripción exitosa: {response['text'][:50]}...")
            return response
            
        except Exception as e:
            error_msg = f"Error al transcribir audio: {str(e)}"
            logger.error(error_msg)
            return {
                "error": error_msg,
                "text": "",
                "success": False
            }
            
        finally:
            # Limpiar el archivo temporal
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"No se pudo eliminar el archivo temporal: {str(e)}")