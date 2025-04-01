# core/tts.py
import os
import tempfile
import logging
from typing import Optional

from app import config

logger = logging.getLogger(__name__)

class TTSProcessor:
    """
    Procesador de síntesis de voz (Text-to-Speech) usando Google TTS.
    """
    
    def __init__(self, language: str = None, slow: bool = False):
        """
        Inicializa el procesador TTS con Google TTS.
        
        Args:
            language (str, optional): Código de idioma (ej: 'es', 'en', 'es-es')
            slow (bool): Si True, habla más lentamente
        """
        self.language = language or config.TTS_LANGUAGE or 'es'
        self.slow = slow
        
        # Verificar que la biblioteca está disponible
        self._check_dependencies()
    
    def _check_dependencies(self):
        """
        Verifica que la biblioteca gTTS esté instalada.
        """
        try:
            import gtts
            logger.info(f"gTTS inicializado con idioma: {self.language}")
        except ImportError:
            logger.error("La biblioteca 'gTTS' no está instalada. Instala con: pip install gtts")
            raise ImportError("Se requiere la biblioteca 'gTTS'")
    
    def synthesize(self, text: str) -> bytes:
        """
        Sintetiza texto a voz.
        
        Args:
            text (str): Texto a convertir en voz
            
        Returns:
            bytes: Datos de audio generados en formato MP3
        """
        # Archivo temporal para guardar el audio
        temp_file_path = None
        
        try:
            from gtts import gTTS
            
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                temp_file_path = temp_file.name
            
            # Crear objeto gTTS y guardar en archivo
            tts = gTTS(text=text, lang=self.language, slow=self.slow)
            tts.save(temp_file_path)
            
            # Leer archivo como bytes
            with open(temp_file_path, "rb") as audio_file:
                audio_data = audio_file.read()
            
            logger.info(f"Audio generado correctamente: {len(audio_data)} bytes")
            return audio_data
            
        except Exception as e:
            logger.error(f"Error al sintetizar voz: {str(e)}")
            raise
            
        finally:
            # Limpiar archivo temporal
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"No se pudo eliminar el archivo temporal: {str(e)}")