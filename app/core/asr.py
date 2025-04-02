import os
import tempfile
import logging
from typing import Optional, Dict, Any
import whisper


from app import config

logger = logging.getLogger(__name__)

class WhisperASR:
    """
    Local implementation of the Whisper ASR system.
    """
    
    def __init__(self, model_size: str = None):
        """
            Initializes the Whisper ASR system.

            This method sets up the Whisper Automatic Speech Recognition (ASR) system by loading the specified model size.

            Args:
                model_size (str, optional): 
                    The size of the Whisper model to use. Options include:
                    - 'tiny'
                    - 'base'
                    - 'small'
                    - 'medium'
                    - 'large'
                    - 'turbo'
                    
                    If not provided, the default value from `config.ASR_MODEL_SIZE` will be used.

            Raises:
                ImportError: If the `whisper` library is not installed.
                Exception: If there is an error initializing the Whisper model.
            """
        self.model_size = model_size or config.ASR_MODEL_SIZE
        
        # Modelo de Whisper
        self.model = None
        
        # Inicializar modelo
        self._initialize_model()
    
    def _initialize_model(self):
        """
        Inicializa el modelo Whisper localmente.
        """
        try:
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
        Transcribe audio to text using Whisper.

        Args:
            audio_data (bytes): Audio data in a compatible format.
            language (str): Language code for transcription (default is "es").

        Returns:
            Dict[str, Any]: A dictionary containing the transcription result, including:
                - **text** (str): The transcribed text.
                - **model** (str): The Whisper model used.
                - **language** (str): The language of the transcription.
                - **segments** (list): Segments of the transcription (if available).
                - **success** (bool): Whether the transcription was successful.
                - **error** (str, optional): Error message if the transcription failed.
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