OpenAILLM - OpenAI API Integration
==================================

The ``OpenAILLM`` class provides an implementation of the ``BaseLLM`` interface that uses OpenAI's API to generate text responses and extract structured information from conversations.

Class Overview
--------------

.. autoclass:: app.core.llm.openai_llm.OpenAILLM
   :members:
   :undoc-members:
   :show-inheritance:

Features
--------

- **Simple Text Generation**: Generate responses from a single prompt.
- **Conversation Support**: Maintain conversation history for contextual responses.
- **Information Extraction**: Extract structured data from conversations.
- **Configurable Parameters**: Customize model, temperature, and API settings.
- **Error Handling**: Robust error handling for API communication.

Methods
-------

### **`__init__`**
.. automethod:: app.core.llm.openai_llm.OpenAILLM.__init__

### **`_initialize_client`**
.. automethod:: app.core.llm.openai_llm.OpenAILLM._initialize_client

### **`generate`**
.. automethod:: app.core.llm.openai_llm.OpenAILLM.generate

### **`generate_with_history`**
.. automethod:: app.core.llm.openai_llm.OpenAILLM.generate_with_history

### **`extract_info`**
.. automethod:: app.core.llm.openai_llm.OpenAILLM.extract_info

System Prompt
------------

By default, the OpenAILLM uses a system prompt that defines the assistant as a sales-oriented virtual assistant (LeadBot) with specific information collection objectives:

- Prospect's full name
- Company name
- Role or position
- Needs or challenges
- Available budget (when appropriate)
- Timelines for implementing solutions

The assistant maintains a professional but friendly tone, asks open-ended questions, and aims to keep the conversation natural.

Error Handling
-------------

The ``OpenAILLM`` class handles various potential errors:

- **Client Initialization Errors**: When the OpenAI API client cannot be initialized.
- **Missing API Key**: When no API key is provided.
- **Response Generation Errors**: When the API call fails.
- **JSON Parsing Errors**: When extracting structured information.

All errors are properly logged using the application's logging system.

Dependencies
-----------

The ``OpenAILLM`` class depends on:

- **OpenAI Python Library**: Install with `pip install openai`.
- **Valid API Key**: A valid OpenAI API key must be provided.

Configuration
------------

The class uses several configuration parameters that can be set directly or through the application config:

- **OPENAI_API_KEY**: API key for authentication.
- **OPENAI_MODEL**: The model to use (e.g., "gpt-4", "gpt-3.5-turbo").
- **OPENAI_TEMPERATURE**: Controls randomness in responses (0.0 to 1.0).