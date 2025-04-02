BaseLLM - Language Model Abstract Interface
=========================================

The ``BaseLLM`` class serves as an abstract base class defining the interface that all language model implementations must follow. It establishes a consistent API for text generation and information extraction across different LLM providers.

Class Overview
-------------

.. autoclass:: app.core.llm.base.BaseLLM
   :members:
   :undoc-members:
   :show-inheritance:

Core Abstract Methods
--------------------

These methods must be implemented by all concrete LLM classes:

### **`generate`**
.. automethod:: app.core.llm.base.BaseLLM.generate

### **`generate_with_history`**
.. automethod:: app.core.llm.base.BaseLLM.generate_with_history

### **`extract_info`**
.. automethod:: app.core.llm.base.BaseLLM.extract_info

Concrete Methods
--------------

The base class also provides some concrete implementations:

### **`get_system_prompt`**
.. automethod:: app.core.llm.base.BaseLLM.get_system_prompt

### **`set_system_prompt`**
.. automethod:: app.core.llm.base.BaseLLM.set_system_prompt

Implementation Guide
------------------

When implementing a concrete LLM class:

1. Inherit from ``BaseLLM``
2. Implement all abstract methods
3. Initialize model-specific clients and configurations
4. Provide appropriate error handling

Example Implementation Skeleton
------------------------------

.. code-block:: python

    class MyCustomLLM(BaseLLM):
        def __init__(self, model_path, **kwargs):
            self.model = load_my_model(model_path)
            self.system_prompt = "Default system prompt for this model"
            
        def generate(self, prompt):
            # Implementation details
            return generated_text
            
        def generate_with_history(self, history, user_input):
            # Implementation details
            return generated_text
            
        def extract_info(self, conversation_text):
            # Implementation details
            return extracted_data

Available Implementations
------------------------

The following concrete LLM implementations are available:

- **OpenAILLM**: Uses OpenAI's API (GPT models)
- **MistralLLM**: Uses local Mistral models

Dependencies
-----------

The ``BaseLLM`` base class itself has minimal dependencies:

- **Python 3.7+**: For ABC and typing support
- **Implementation-specific**: Each concrete implementation will have its own dependencies