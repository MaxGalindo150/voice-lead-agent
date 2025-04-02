# core/tts.py
import os
import tempfile
import logging
from typing import Optional

from app import config

logger = logging.getLogger(__name__)

class TTSProcessor:
    """
    Text-to-Speech processor using Google TTS.
    """
    
    def __init__(self, language: str = None, slow: bool = False):
        """
        Initialize the TTS processor with Google TTS.
        
        Args:
            language (str, optional): Language code (e.g.: 'es', 'en', 'es-es')
            slow (bool): If True, speaks more slowly
        """
        self.language = language or config.TTS_LANGUAGE or 'es'
        self.slow = slow
        
        # Verify that the library is available
        self._check_dependencies()
    
    def _check_dependencies(self):
        """
        Verify that the gTTS library is installed.
        """
        try:
            import gtts
            logger.info(f"gTTS initialized with language: {self.language}")
        except ImportError:
            logger.error("The 'gTTS' library is not installed. Install with: pip install gtts")
            raise ImportError("The 'gTTS' library is required")
    
    def synthesize(self, text: str) -> bytes:
        """
        Synthesize text to speech.
        
        Args:
            text (str): Text to convert to speech
            
        Returns:
            bytes: Generated audio data in MP3 format
        """
        # Temporary file to save the audio
        temp_file_path = None
        
        try:
            from gtts import gTTS
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                temp_file_path = temp_file.name
            
            # Create gTTS object and save to file
            tts = gTTS(text=text, lang=self.language, slow=self.slow)
            tts.save(temp_file_path)
            
            # Read file as bytes
            with open(temp_file_path, "rb") as audio_file:
                audio_data = audio_file.read()
            
            logger.info(f"Audio generated successfully: {len(audio_data)} bytes")
            return audio_data
            
        except Exception as e:
            logger.error(f"Error synthesizing speech: {str(e)}")
            raise
            
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"Could not delete temporary file: {str(e)}")