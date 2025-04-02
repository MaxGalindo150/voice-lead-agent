import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock

# Import the class to test
from app.core.tts import TTSProcessor

class TestTTSProcessor:
    
    def test_initialization_with_defaults(self):
        """Test initialization with default parameters"""
        with patch('app.core.tts.config') as mock_config:
            mock_config.TTS_LANGUAGE = 'es'
            with patch('app.core.tts.TTSProcessor._check_dependencies'):
                processor = TTSProcessor()
                assert processor.language == 'es'
                assert processor.slow is False
    
    def test_initialization_with_custom_params(self):
        """Test initialization with custom parameters"""
        with patch('app.core.tts.TTSProcessor._check_dependencies'):
            processor = TTSProcessor(language='en', slow=True)
            assert processor.language == 'en'
            assert processor.slow is True
    
    def test_check_dependencies_success(self):
        """Test dependency check when gTTS is available"""
        with patch('importlib.import_module') as mock_import:
            processor = TTSProcessor()
            # If no exception is raised, the test passes

    

    