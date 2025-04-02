StreamlitAudioRecorder - Audio Recording Component
===================================================

The ``StreamlitAudioRecorder`` class provides an adapter for recording audio in Streamlit applications.

Class Overview
---------------

.. autoclass:: app.utils.audio.StreamlitAudioRecorder
   :members:
   :undoc-members:
   :show-inheritance:

Features
--------

- **Thread-Based Recording**: Non-blocking audio capture using background threads
- **Safe Resource Management**: Proper initialization and cleanup of PyAudio resources
- **Simple API**: Easy-to-use methods for recording control
- **Raw Audio Access**: Direct access to recorded audio data

Audio Configuration
-------------------

The recorder uses the following default audio settings:

- **Format**: 16-bit signed integer PCM (pyaudio.paInt16)
- **Channels**: 1 (Mono)
- **Sample Rate**: 16000 Hz
- **Chunk Size**: 1024 samples
- **Maximum Recording Duration**: 15 seconds

Methods
-------

### **`__init__`**
.. automethod:: app.utils.audio_recorder.StreamlitAudioRecorder.__init__

### **`start_recording`**
.. automethod:: app.utils.audio_recorder.StreamlitAudioRecorder.start_recording

### **`stop_recording`**
.. automethod:: app.utils.audio_recorder.StreamlitAudioRecorder.stop_recording

### **`get_audio_data`**
.. automethod:: app.utils.audio_recorder.StreamlitAudioRecorder.get_audio_data

### **`close`**
.. automethod:: app.utils.audio_recorder.StreamlitAudioRecorder.close

### **`_record`**
.. automethod:: app.utils.audio_recorder.StreamlitAudioRecorder._record

Error Handling
---------------

The ``StreamlitAudioRecorder`` includes error handling for:

- Stream initialization failures
- Recording interruptions
- Resource cleanup issues

All errors are properly logged to standard output.

Dependencies
-------------

- **PyAudio**: For audio capture functionality
- **threading**: For non-blocking recording operations

Usage Example
--------------

.. code-block:: python

    # Create recorder
    recorder = StreamlitAudioRecorder()
    
    # Start recording when button is clicked
    if st.button("Start Recording"):
        recorder.start_recording()
    
    # Stop recording when button is clicked
    if st.button("Stop Recording"):
        recorder.stop_recording()
        
        # Get audio data
        audio_data = recorder.get_audio_data()
        
        if audio_data:
            # Save to file
            with open("recording.wav", "wb") as f:
                # Add WAV header
                # ... (code to create WAV header)
                f.write(audio_data)
    
    # Clean up when app exits
    def on_exit():
        recorder.close()
    
    st.on_session_end(on_exit)