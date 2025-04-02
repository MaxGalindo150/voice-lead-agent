ConversationOrchestrator - Langchain Integration
==========================================

The ``ConversationOrchestrator`` class provides a structured way to manage conversations with leads using Langchain. It maintains conversation context and guides the flow through different stages of the sales process.

Class Overview
--------------

.. autoclass:: app.core.langchain_integration.ConversationOrchestrator
   :members:
   :undoc-members:
   :show-inheritance:

Features
--------

- **Conversation Stage Management**: Progress through introduction, needs identification, qualification, proposal, and closing.
- **Context Tracking**: Maintain information about the lead throughout the conversation.
- **Automated Information Extraction**: Extract key details from user messages.
- **Optimized Response Generation**: Generate contextually appropriate responses for each stage.
- **Smart Stage Advancement**: Automatically determine when to advance to the next conversation stage.

Methods
-------

### **`__init__`**
.. automethod:: app.core.langchain_integration.ConversationOrchestrator.__init__

### **`get_stage_prompt`**
.. automethod:: app.core.langchain_integration.ConversationOrchestrator.get_stage_prompt

### **`_get_ending_prompt`**
.. automethod:: app.core.langchain_integration.ConversationOrchestrator._get_ending_prompt

### **`_is_stuck_in_stage`**
.. automethod:: app.core.langchain_integration.ConversationOrchestrator._is_stuck_in_stage

### **`advance_stage`**
.. automethod:: app.core.langchain_integration.ConversationOrchestrator.advance_stage

### **`start_ending_sequence`**
.. automethod:: app.core.langchain_integration.ConversationOrchestrator.start_ending_sequence

### **`should_advance_stage`**
.. automethod:: app.core.langchain_integration.ConversationOrchestrator.should_advance_stage

### **`_should_end_conversation`**
.. automethod:: app.core.langchain_integration.ConversationOrchestrator._should_end_conversation

### **`_extract_direct_info`**
.. automethod:: app.core.langchain_integration.ConversationOrchestrator._extract_direct_info

### **`process_message`**
.. automethod:: app.core.langchain_integration.ConversationOrchestrator.process_message

### **`_update_lead_info_safely`**
.. automethod:: app.core.langchain_integration.ConversationOrchestrator._update_lead_info_safely

Conversation Stages
------------------

The orchestrator guides the conversation through five distinct stages:

1. **Introduction**: Gather basic information about the lead and their company.
2. **Needs Identification**: Understand the lead's needs and pain points.
3. **Qualification**: Determine the lead's budget and timeframe.
4. **Proposal**: Present solutions tailored to the lead's needs.
5. **Closing**: Secure next steps and conclude the conversation.

Each stage has specific goals and essential information to collect before advancing.

Error Handling
--------------

The ``ConversationOrchestrator`` includes error handling for:

- Stagnant conversations with repetitive content
- Missing essential information
- Premature conversation endings

Dependencies
------------

The ``ConversationOrchestrator`` class depends on the following:

- **Langchain**: For conversation structure and memory management.
- **BaseLLM**: Custom LLM integration for response generation and information extraction.
- **Logging**: For tracking conversation flow and debugging.