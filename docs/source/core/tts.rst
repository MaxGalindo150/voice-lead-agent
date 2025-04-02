TTSProcessor - Text-to-Speech Processing
=====================================

The ``TTSProcessor`` class provides a wrapper for Google's Text-to-Speech service (gTTS). It allows you to convert text into natural-sounding speech in various languages.

Class Overview
--------------

.. autoclass:: app.core.tts.TTSProcessor
   :members:
   :undoc-members:
   :show-inheritance:

Features
--------

- **Multiple Language Support**: Support for various languages and language variants.
- **Speech Rate Control**: Option to slow down speech output for better clarity.
- **Simple API**: Straightforward method to convert text to audio data.
- **Temporary File Management**: Automatic cleanup of temporary files after processing.

Methods
-------

### **`__init__`**
.. automethod:: app.core.tts.TTSProcessor.__init__

### **`_check_dependencies`**
.. automethod:: app.core.tts.TTSProcessor._check_dependencies

### **`synthesize`**
.. automethod:: app.core.tts.TTSProcessor.synthesize

Error Handling
--------------

The ``TTSProcessor`` class provides error handling for common issues, such as:

- Missing gTTS library dependencies (`ImportError`).
- Synthesis errors during text-to-speech conversion.
- Temporary file management errors.

All errors are properly logged using the application's logging system.

Dependencies
------------

The ``TTSProcessor`` class depends on the following:

- **gTTS Library**: Install it using `pip install gtts`.
- **Internet Connection**: Required to access Google's TTS service.
- **Temporary File System Access**: Used to save and read audio data.

Configuration
------------

The language can be configured in several ways:

1. Directly when instantiating the class: `TTSProcessor(language='en')`
2. Via the application configuration: `config.TTS_LANGUAGE`
3. Default fallback to Spanish ('es') if not specified elsewhere