import threading
import uuid
import pyaudio

# Audio settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
MAX_RECORDING_SECONDS = 15


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