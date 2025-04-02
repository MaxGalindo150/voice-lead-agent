WhisperASR - Automatic Speech Recognition
==========================================

The `WhisperASR` class provides a local implementation of the Whisper Automatic Speech Recognition (ASR) system. It allows you to transcribe audio data into text using a specified Whisper model.

Class Overview
--------------

.. autoclass:: app.core.asr.WhisperASR
   :members:
   :undoc-members:
   :show-inheritance:

Features
--------

- **Model Initialization**: Load a Whisper model of a specified size (e.g., `tiny`, `base`, `small`, etc.).
- **Audio Transcription**: Convert audio data into text with language support.

Methods
-------

### **`__init__`**
.. automethod:: app.core.asr.WhisperASR.__init__

### **`_initialize_model`**
.. automethod:: app.core.asr.WhisperASR._initialize_model

### **`transcribe`**
.. automethod:: app.core.asr.WhisperASR.transcribe

Error Handling
--------------

The `WhisperASR` class provides error handling for common issues, such as:

- Missing Whisper library (`ImportError`).
- Issues during model initialization.
- Errors during audio transcription.

Make sure to check the `success` field in the transcription result to determine if the operation was successful.

Dependencies
------------

The `WhisperASR` class depends on the following:

- **Whisper Library**: Install it using `pip install openai-whisper`.
- **Python 3.10+**: Required for compatibility with the project.
