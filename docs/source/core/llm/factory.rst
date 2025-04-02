LLM Factory - Language Model Creation
=====================================

The LLM Factory module provides a clean interface for creating and initializing different Large Language Model implementations. It supports multiple LLM providers with automatic fallback options.

Function Overview
----------------

.. autofunction:: app.core.llm.factory.create_llm

Features
--------

- **Multiple LLM Support**: Seamlessly switch between OpenAI and Mistral implementations.
- **Automatic Mode**: Configurable fallback to OpenAI if Mistral isn't available or fails.
- **Configuration-Based**: Uses application configuration for model settings.
- **Dynamic Loading**: Loads model dependencies only when needed.

Usage Examples
-------------

Basic usage with default configuration:

.. code-block:: python

    from app.core.llm.factory import create_llm
    
    # Creates LLM based on config.LLM_MODE
    llm = create_llm()
    
    # Generate a response
    response = llm.generate("Tell me about language models")

Explicitly specify LLM type:

.. code-block:: python

    # Force OpenAI
    openai_llm = create_llm("openai")
    
    # Try to use Mistral
    mistral_llm = create_llm("mistral")
    
    # Try Mistral with OpenAI fallback
    auto_llm = create_llm("auto")

Error Handling
--------------

The factory handles various errors that might occur during LLM initialization:

- **Import Errors**: When required dependencies are missing
- **Initialization Errors**: When the model fails to load properly
- **Invalid LLM Type**: When an unrecognized LLM type is specified

All errors are properly logged using the application's logging system.

Dependencies
------------

The factory depends on the following components:

- **BaseLLM**: Abstract base class for all LLM implementations
- **OpenAILLM**: Implementation for OpenAI models
- **MistralLLM** (optional): Implementation for local Mistral models

Configuration
------------

The factory uses several configuration parameters:

- **LLM_MODE**: Default LLM to use ('openai', 'mistral', or 'auto')
- **OPENAI_API_KEY**: API key for OpenAI
- **OPENAI_MODEL**: Model name for OpenAI
- **OPENAI_TEMPERATURE**: Temperature setting for OpenAI responses
- **MISTRAL_MODEL_PATH**: Path to local Mistral model weights
- **MISTRAL_GPU_LAYERS**: Number of layers to offload to GPU