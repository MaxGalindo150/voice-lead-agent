ConversationManager - Conversation Handling
===========================================

The `ConversationManager` class is responsible for managing conversations with users. It handles tasks such as text and audio processing, managing conversation states, and saving data to the database.

Class Overview
--------------

.. autoclass:: app.core.conversation.ConversationManager
   :members:
   :undoc-members:
   :show-inheritance:

Methods
-------

### **`__init__`**
.. automethod:: app.core.conversation.ConversationManager.__init__

### **`start_conversation`**
.. automethod:: app.core.conversation.ConversationManager.start_conversation

### **`process_text_message`**
.. automethod:: app.core.conversation.ConversationManager.process_text_message

### **`process_audio_message`**
.. automethod:: app.core.conversation.ConversationManager.process_audio_message

### **`end_conversation`**
.. automethod:: app.core.conversation.ConversationManager.end_conversation

### **`get_conversation_history`**
.. automethod:: app.core.conversation.ConversationManager.get_conversation_history

### **`get_lead_info`**
.. automethod:: app.core.conversation.ConversationManager.get_lead_info

### **`_save_audio_file`**
.. automethod:: app.core.conversation.ConversationManager._save_audio_file

Features
--------

- **Conversation Initialization**: Start new conversations and optionally link them to existing leads.
- **Text and Audio Processing**: Handle user messages in both text and audio formats.
- **State Management**: Manage the state of conversations, including stages and extracted lead information.
- **Database Integration**: Save and retrieve conversation and lead data from the database.
- **Audio File Handling**: Save audio files for user and assistant messages.


Dependencies
------------

The `ConversationManager` class depends on the following components:

- **Language Model (LLM)**: Used for generating responses.
- **ASR Processor**: For transcribing audio messages.
- **TTS Processor**: For generating audio responses.
- **Database Repositories**: For storing and retrieving conversation and lead data.
