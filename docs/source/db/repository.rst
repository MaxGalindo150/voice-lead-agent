Repository Classes - Data Access Layer
===================================

The repository module provides classes for data access and manipulation in the database. It contains implementations for managing leads and conversations.

Classes Overview
---------------

.. autoclass:: app.db.repository.LeadRepository
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: app.db.repository.ConversationRepository
   :members:
   :undoc-members:
   :show-inheritance:

LeadRepository Features
---------------------

- **CRUD Operations**: Complete set of create, read, update, and delete operations for leads
- **Data Serialization**: Handles conversion between database records and Lead objects
- **JSON Handling**: Converts complex data types to and from JSON for storage
- **Date Handling**: Manages datetime conversions between Python objects and database storage

LeadRepository Methods
--------------------

### **`__init__`**
.. automethod:: app.db.repository.LeadRepository.__init__

### **`save_lead`**
.. automethod:: app.db.repository.LeadRepository.save_lead

### **`get_lead`**
.. automethod:: app.db.repository.LeadRepository.get_lead

### **`update_lead`**
.. automethod:: app.db.repository.LeadRepository.update_lead

### **`get_all_leads`**
.. automethod:: app.db.repository.LeadRepository.get_all_leads

### **`delete_lead`**
.. automethod:: app.db.repository.LeadRepository.delete_lead

ConversationRepository Features
----------------------------

- **Hierarchical Data Management**: Handles conversations and their associated messages
- **Transaction Support**: Manages database transactions for data integrity
- **Complex Object Mapping**: Maps between database records and complex domain objects
- **Relationship Management**: Maintains relationships between conversations and leads

ConversationRepository Methods
---------------------------

### **`__init__`**
.. automethod:: app.db.repository.ConversationRepository.__init__

### **`save_conversation`**
.. automethod:: app.db.repository.ConversationRepository.save_conversation

### **`get_conversation`**
.. automethod:: app.db.repository.ConversationRepository.get_conversation

### **`get_conversations_by_lead`**
.. automethod:: app.db.repository.ConversationRepository.get_conversations_by_lead

### **`delete_conversation`**
.. automethod:: app.db.repository.ConversationRepository.delete_conversation

### **`get_all_conversations`**
.. automethod:: app.db.repository.ConversationRepository.get_all_conversations

Error Handling
-------------

Both repository classes include comprehensive error handling:

- **Database Connection Errors**: Handled with appropriate logging
- **Query Execution Errors**: Managed with transaction rollback when needed
- **Data Serialization Errors**: Gracefully handled with fallback options
- **Record Not Found**: Returns None or empty lists rather than raising exceptions

Usage Examples
------------

Using the LeadRepository:

.. code-block:: python

    # Create repository
    lead_repo = LeadRepository()
    
    # Create and save a new lead
    new_lead = Lead(
        id="lead123",
        nombre="John Doe",
        empresa="ACME Corp"
    )
    lead_id = lead_repo.save_lead(new_lead)
    
    # Retrieve a lead
    lead = lead_repo.get_lead(lead_id)
    
    # Update a lead
    lead_repo.update_lead(lead_id, {"presupuesto": "$10,000"})
    
    # Delete a lead
    lead_repo.delete_lead(lead_id)

Using the ConversationRepository:

.. code-block:: python

    # Create repository
    conv_repo = ConversationRepository()
    
    # Create and save a conversation
    new_conv = Conversation(
        id="conv123",
        lead_id="lead123"
    )
    new_conv.messages = [
        Message(role="user", content="Hello", timestamp=datetime.now()),
        Message(role="assistant", content="Hi there!", timestamp=datetime.now())
    ]
    conv_id = conv_repo.save_conversation(new_conv)
    
    # Get conversations for a lead
    lead_conversations = conv_repo.get_conversations_by_lead("lead123")