Conversation Models
====================

The conversation module provides data models for representing conversations and messages between the system and leads.

Classes Overview
-----------------

.. autoclass:: app.models.conversation.Message
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: app.models.conversation.Conversation
   :members:
   :undoc-members:
   :show-inheritance:

Message Class
-------------

The ``Message`` class represents individual messages within a conversation, supporting both text and audio content.

### Attributes

- **role**: Identifies the message sender ('user' or 'assistant')
- **content**: The message text content
- **timestamp**: When the message was sent (defaults to creation time)
- **audio_file_path**: Optional path to an audio file for this message
- **transcription**: Optional text transcription for audio messages
- **id**: Database-generated ID (optional)
- **conversation_id**: Reference to parent conversation (optional)

### Methods

#### **`to_dict`**
.. automethod:: app.models.conversation.Message.to_dict

#### **`from_dict`**
.. automethod:: app.models.conversation.Message.from_dict

Conversation Class
------------------

The ``Conversation`` class represents a complete conversation with a lead, including messages and metadata.

### Attributes

- **id**: Unique identifier (UUID), automatically generated
- **lead_id**: Reference to the associated lead
- **messages**: List of Message objects in the conversation
- **created_at**: Timestamp when the conversation was created
- **updated_at**: Timestamp of the last update
- **ended_at**: Optional timestamp when the conversation was ended
- **summary**: Optional conversation summary
- **lead_info_extracted**: Dictionary with information extracted from the conversation

### Methods

#### **`add_message`**
.. automethod:: app.models.conversation.Conversation.add_message

#### **`end_conversation`**
.. automethod:: app.models.conversation.Conversation.end_conversation

#### **`to_dict`**
.. automethod:: app.models.conversation.Conversation.to_dict

#### **`from_dict`**
.. automethod:: app.models.conversation.Conversation.from_dict

Serialization
--------------

Both classes support serialization to and from dictionaries, handling:

- Conversion between Python objects and JSON-compatible dictionaries
- Proper datetime formatting (ISO 8601)
- Nested object conversion (messages within conversations)

Usage Examples
---------------

Creating and managing a conversation:

.. code-block:: python

    # Create a new conversation
    conversation = Conversation(lead_id="lead123")
    
    # Add messages
    conversation.add_message(role="user", content="Hello, I need information about your products")
    conversation.add_message(role="assistant", content="Hi! I'd be happy to help. What specific products are you interested in?")
    
    # Add a message with audio
    conversation.add_message(
        role="user", 
        content="I'm interested in your CRM solution", 
        audio_file_path="uploads/message123.mp3",
        transcription="I'm interested in your CRM solution"
    )
    
    # End the conversation
    conversation.end_conversation()
    
    # Serialize to dictionary
    data = conversation.to_dict()
    
    # Deserialize from dictionary
    restored_conversation = Conversation.from_dict(data)