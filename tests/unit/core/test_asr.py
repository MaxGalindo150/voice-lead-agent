import pytest
from unittest.mock import patch, MagicMock
import sys
import tempfile
import os

# Test the WhisperASR class
class TestWhisperASR:
    
    @patch('app.core.asr.whisper', create=True)
    def test_initialization_default_model(self, mock_whisper):
        """Test initialization with default model size"""
        from app.core.asr import WhisperASR

        # Setup mock
        mock_model = MagicMock()
        mock_whisper.load_model.return_value = mock_model

        # Test initialization
        asr = WhisperASR()

        # Assert model was loaded with default size from config
        mock_whisper.load_model.assert_called_once()
        assert asr.model == mock_model
        
    @patch('app.core.asr.whisper', create=True)
    def test_initialization_custom_model(self, mock_whisper):
        """Test initialization with custom model size"""
        from app.core.asr import WhisperASR
        
        # Setup mock
        mock_model = MagicMock()
        mock_whisper.load_model.return_value = mock_model
        custom_size = 'turbo'
        
        # Test initialization
        asr = WhisperASR(model_size=custom_size)
        
        # Assert model was loaded with custom size
        mock_whisper.load_model.assert_called_once_with(custom_size)
        assert asr.model == mock_model
        
    @patch('app.core.asr.whisper', create=True)
    def test_whisper_import_error(self, mock_whisper):
        """Test handling ImportError for whisper library"""
        # Configure the mock to raise ImportError
        mock_whisper.load_model.side_effect = ImportError("No module named 'whisper'")
        
        from app.core.asr import WhisperASR
        
        # Test initialization should raise ImportError
        with pytest.raises(ImportError):
            WhisperASR()
            
    @patch('app.core.asr.whisper', create=True)
    def test_model_initialization_error(self, mock_whisper):
        """Test handling other exceptions during model initialization"""
        # Simulate generic error
        mock_whisper.load_model.side_effect = Exception("Failed to load model")
        
        from app.core.asr import WhisperASR
        
        # Test initialization should raise Exception
        with pytest.raises(Exception):
            WhisperASR()
            
    @patch('app.core.asr.whisper', create=True)
    @patch('tempfile.NamedTemporaryFile')
    def test_transcribe_success(self, mock_temp_file, mock_whisper):
        """Test successful audio transcription"""
        from app.core.asr import WhisperASR
        
        # Setup mocks
        mock_model = MagicMock()
        mock_whisper.load_model.return_value = mock_model
        
        # Mock transcription result
        expected_text = "Esto es una prueba de transcripción"
        mock_model.transcribe.return_value = {
            "text": expected_text,
            "segments": [{"id": 0, "start": 0, "end": 2.5, "text": expected_text}]
        }
        
        # Mock temp file
        mock_file = MagicMock()
        mock_file.name = "temp_audio.wav"
        mock_temp_file.return_value.__enter__.return_value = mock_file
        
        # Test transcription
        asr = WhisperASR(model_size='base')
        audio_data = b'dummy_audio_data'
        result = asr.transcribe(audio_data)
        
        # Assertions
        assert result["success"] is True
        assert result["text"] == expected_text
        assert result["model"] == "whisper-base"
        assert "segments" in result
        
        # Verify temp file was written to
        mock_file.write.assert_called_once_with(audio_data)
        # Verify transcribe was called with temp file
        mock_model.transcribe.assert_called_once()
        assert mock_model.transcribe.call_args[0][0] == "temp_audio.wav"
        
    @patch('app.core.asr.whisper', create=True)
    def test_transcribe_no_model(self, mock_whisper):
        """Test transcribe when model is not initialized"""
        from app.core.asr import WhisperASR
        
        # Setup mock for initialization
        mock_model = MagicMock()
        mock_whisper.load_model.return_value = mock_model
        
        # Create ASR instance
        asr = WhisperASR()
        # Manually set model to None to simulate initialization failure
        asr.model = None
        
        # Test transcription
        result = asr.transcribe(b'dummy_audio_data')
        
        # Assertions
        assert result["success"] is False
        assert result["text"] == ""
        assert "error" in result
        assert "Modelo Whisper no inicializado" in result["error"]
        
    @patch('app.core.asr.whisper', create=True)
    @patch('tempfile.NamedTemporaryFile')
    def test_transcribe_error(self, mock_temp_file, mock_whisper):
        """Test error handling during transcription"""
        from app.core.asr import WhisperASR
        
        # Setup mocks
        mock_model = MagicMock()
        mock_whisper.load_model.return_value = mock_model
        
        # Mock transcription error
        error_message = "Error during transcription"
        mock_model.transcribe.side_effect = Exception(error_message)
        
        # Mock temp file
        mock_file = MagicMock()
        mock_file.name = "temp_audio.wav"
        mock_temp_file.return_value.__enter__.return_value = mock_file
        
        # Test transcription
        asr = WhisperASR()
        result = asr.transcribe(b'dummy_audio_data')
        
        # Assertions
        assert result["success"] is False
        assert result["text"] == ""
        assert "error" in result
        assert error_message in result["error"]
        
    @patch('app.core.asr.whisper', create=True)
    @patch('tempfile.NamedTemporaryFile')
    @patch('os.path.exists')
    @patch('os.unlink')
    def test_temp_file_cleanup(self, mock_unlink, mock_exists, mock_temp_file, mock_whisper):
        """Test temporary file cleanup after transcription"""
        from app.core.asr import WhisperASR
        
        # Setup mocks
        mock_model = MagicMock()
        mock_whisper.load_model.return_value = mock_model
        
        # Mock transcription result
        mock_model.transcribe.return_value = {
            "text": "Test transcription",
            "segments": []
        }
        
        # Mock temp file
        temp_filename = "temp_audio.wav"
        mock_file = MagicMock()
        mock_file.name = temp_filename
        mock_temp_file.return_value.__enter__.return_value = mock_file
        
        # Mock os.path.exists to return True
        mock_exists.return_value = True
        
        # Test transcription
        asr = WhisperASR()
        asr.transcribe(b'dummy_audio_data')
        
        # Verify temp file was deleted
        mock_exists.assert_called_once_with(temp_filename)
        mock_unlink.assert_called_once_with(temp_filename)
        
    @patch('app.core.asr.whisper', create=True)
    @patch('tempfile.NamedTemporaryFile')
    @patch('os.path.exists')
    @patch('os.unlink')
    def test_temp_file_cleanup_error(self, mock_unlink, mock_exists, mock_temp_file, mock_whisper):
        """Test error handling during temporary file cleanup"""
        from app.core.asr import WhisperASR
        
        # Setup mocks
        mock_model = MagicMock()
        mock_whisper.load_model.return_value = mock_model
        
        # Mock transcription result
        mock_model.transcribe.return_value = {
            "text": "Test transcription",
            "segments": []
        }
        
        # Mock temp file
        temp_filename = "temp_audio.wav"
        mock_file = MagicMock()
        mock_file.name = temp_filename
        mock_temp_file.return_value.__enter__.return_value = mock_file
        
        # Mock os.path.exists to return True
        mock_exists.return_value = True
        
        # Mock unlink to raise an exception
        mock_unlink.side_effect = Exception("Permission denied")
        
        # Test transcription
        asr = WhisperASR()
        asr.transcribe(b'dummy_audio_data')
        
        # Verify os.path.exists was called
        mock_exists.assert_called_once_with(temp_filename)
        # Verify unlink was called and exception was handled
        mock_unlink.assert_called_once_with(temp_filename)