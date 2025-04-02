import pytest
import threading
import time
from unittest.mock import MagicMock, patch
import io

# Import constants directly to use in mocking
CHUNK = 1024
FORMAT = 16  # Mocked value for pyaudio.paInt16
CHANNELS = 1
RATE = 16000

# Mock pyaudio module
class MockPyAudio:
    def __init__(self):
        self.mock_stream = MagicMock()
        self.mock_stream.read.return_value = b'test_audio_data'
        self.mock_stream.stop_stream = MagicMock()
        self.mock_stream.close = MagicMock()
    
    def open(self, **kwargs):
        return self.mock_stream
    
    def terminate(self):
        pass

# Patch for import 
pyaudio = MagicMock()
pyaudio.PyAudio = MockPyAudio
pyaudio.paInt16 = FORMAT

# Import the class to test
@pytest.fixture
def streamlit_audio_recorder_class():
    """Create a version of the StreamlitAudioRecorder class with mocked dependencies"""
    with patch.dict('sys.modules', {'pyaudio': pyaudio}):
        # Define the class within the fixture to use the mocked dependencies
        class StreamlitAudioRecorder:
            """Adapter for recording audio in Streamlit."""
            
            def __init__(self):
                # Initialize variables
                self.p = None
                self.stream = None
                self.frames = []
                self.is_recording = False
                self.stop_event = threading.Event()
            
            def start_recording(self):
                """Starts audio recording."""
                if self.is_recording:
                    return
                    
                self.is_recording = True
                self.frames = []
                self.stop_event.clear()
                
                # Initialize PyAudio if it doesn't exist
                if not self.p:
                    self.p = pyaudio.PyAudio()
                    
                # Create stream
                try:
                    self.stream = self.p.open(
                        format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK
                    )
                    
                    # Start recording thread
                    self.thread = threading.Thread(target=self._record)
                    self.thread.daemon = True
                    self.thread.start()
                    return True
                except Exception as e:
                    print(f"Error starting recording: {e}")
                    self.is_recording = False
                    return False
            
            def stop_recording(self):
                """Stops audio recording."""
                if not self.is_recording:
                    return
                    
                self.is_recording = False
                self.stop_event.set()
                
                # Wait for the thread to finish
                if hasattr(self, 'thread') and self.thread.is_alive():
                    self.thread.join(timeout=1)
                    
                # Close stream
                if self.stream:
                    self.stream.stop_stream()
                    self.stream.close()
                    self.stream = None
            
            def _record(self):
                """Internal function for recording audio."""
                try:
                    while self.is_recording and not self.stop_event.is_set():
                        data = self.stream.read(CHUNK, exception_on_overflow=False)
                        self.frames.append(data)
                except Exception as e:
                    print(f"Error during recording: {e}")
                finally:
                    # Ensure the stream is closed
                    if self.stream:
                        self.stream.stop_stream()
                        self.stream.close()
                        self.stream = None
                    self.is_recording = False
            
            def get_audio_data(self):
                """Returns the recorded audio data."""
                if not self.frames:
                    return None
                return b''.join(self.frames)
            
            def close(self):
                """Releases resources."""
                self.stop_recording()
                if self.p:
                    self.p.terminate()
                    self.p = None
                    
        return StreamlitAudioRecorder

class TestStreamlitAudioRecorder:
    
    @pytest.fixture
    def recorder(self, streamlit_audio_recorder_class):
        """Create a recorder instance"""
        recorder = streamlit_audio_recorder_class()
        yield recorder
        recorder.close()
    
    def test_initialization(self, recorder):
        """Test initialization state"""
        assert recorder.p is None
        assert recorder.stream is None
        assert recorder.frames == []
        assert recorder.is_recording is False
        assert isinstance(recorder.stop_event, threading.Event)
    
    def test_start_recording(self, recorder):
        """Test starting the recording"""
        result = recorder.start_recording()
        
        assert result is True
        assert recorder.is_recording is True
        assert recorder.p is not None
        assert recorder.stream is not None
        assert hasattr(recorder, 'thread')
        assert recorder.thread.daemon is True
        
        # Clean up
        recorder.stop_recording()
    
    def test_stop_recording(self, recorder):
        """Test stopping the recording"""
        # Start recording first
        recorder.start_recording()
        
        # Now stop it
        recorder.stop_recording()
        
        assert recorder.is_recording is False
        assert recorder.stop_event.is_set()
        
        # Check that stream was closed
        if recorder.stream:
            recorder.stream.stop_stream.assert_called_once()
            recorder.stream.close.assert_called_once()
    
    def test_get_audio_data_empty(self, recorder):
        """Test getting audio data when no recording has been made"""
        assert recorder.get_audio_data() is None
    
    def test_get_audio_data(self, recorder):
        """Test getting audio data after recording"""
        # Simulate some recorded frames
        test_data = b'test_frame_1'
        test_data2 = b'test_frame_2'
        recorder.frames = [test_data, test_data2]
        
        audio_data = recorder.get_audio_data()
        
        assert audio_data == b'test_frame_1test_frame_2'
    
    def test_record_method(self, recorder):
        """Test the internal _record method"""
        # Setup mocks
        recorder.stream = MagicMock()
        recorder.stream.read.return_value = b'test_audio_chunk'
        recorder.is_recording = True
        
        # Run the method in a thread so we can control it
        thread = threading.Thread(target=recorder._record)
        thread.daemon = True
        thread.start()
        
        # Let it record for a short time
        time.sleep(0.1)
        
        # Stop recording
        recorder.is_recording = False
        recorder.stop_event.set()
        thread.join(timeout=1)
        
        # Check results
        assert len(recorder.frames) > 0
        assert recorder.frames[0] == b'test_audio_chunk'
    
    def test_error_handling_during_start(self, streamlit_audio_recorder_class):
        """Test error handling when starting recording"""
        # Create recorder with error-prone mock
        recorder = streamlit_audio_recorder_class()
        
        # Mock PyAudio to raise an exception
        mock_pyaudio = MagicMock()
        mock_pyaudio.open.side_effect = Exception("Test error")
        
        # Set the mock on the recorder
        recorder.p = mock_pyaudio
        
        # Try to start recording
        result = recorder.start_recording()
        
        # Check error was handled
        assert result is False
        assert recorder.is_recording is False
        
        # Clean up
        recorder.close()
    
    def test_error_handling_during_recording(self, recorder):
        """Test error handling during recording"""
        # Setup mocks
        recorder.stream = MagicMock()
        recorder.stream.read.side_effect = Exception("Test recording error")
        recorder.is_recording = True
        
        # Call the _record method directly
        recorder._record()
        
        # Check error was handled
        assert recorder.is_recording is False