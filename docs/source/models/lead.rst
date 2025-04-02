Lead Model
==========

The Lead model provides a data structure for representing and managing sales prospects in the system.

Class Overview
-------------

.. autoclass:: app.models.lead.Lead
   :members:
   :undoc-members:
   :show-inheritance:

Attributes
---------

The ``Lead`` class contains the following attributes:

**Basic Information**
  - ``id``: Unique identifier (UUID), automatically generated
  - ``nombre``: Lead's name
  - ``empresa``: Company name
  - ``cargo``: Position/role
  - ``email``: Email address
  - ``telefono``: Phone number

**Qualification Information**
  - ``necesidades``: Identified needs
  - ``presupuesto``: Budget information
  - ``plazo``: Timeframe
  - ``punto_dolor``: Pain points
  - ``producto_interes``: Products of interest

**Sales Process**
  - ``conversation_stage``: Current stage in the sales process (default: "introduccion")

**Metadata**
  - ``created_at``: Creation timestamp
  - ``updated_at``: Last update timestamp
  - ``conversation_ids``: List of associated conversation IDs

Methods
------

### **`to_dict`**
.. automethod:: app.models.lead.Lead.to_dict

### **`from_dict`**
.. automethod:: app.models.lead.Lead.from_dict

### **`update`**
.. automethod:: app.models.lead.Lead.update

### **`add_conversation`**
.. automethod:: app.models.lead.Lead.add_conversation

Serialization
------------

The ``Lead`` class supports serialization to and from dictionaries:

- Converts Python objects to JSON-compatible dictionaries
- Properly handles datetime formatting (ISO 8601)
- Provides convenient methods for database persistence

Usage Examples
------------

Creating and managing a lead:

.. code-block:: python

    # Create a new lead
    lead = Lead(
        nombre="John Doe",
        empresa="ACME Corp",
        email="john@acme.com"
    )
    
    # Update lead information
    lead.update({
        "cargo": "CTO",
        "presupuesto": "$10,000",
        "plazo": "3 months"
    })
    
    # Associate with a conversation
    lead.add_conversation("conversation_id_123")
    
    # Serialize to dictionary
    lead_dict = lead.to_dict()
    
    # Deserialize from dictionary
    restored_lead = Lead.from_dict(lead_dict)

Integration with Repository Layer
-------------------------------

The Lead model is designed to work seamlessly with the LeadRepository class, which handles database operations:

- Converting between Lead objects and database records
- Managing relationships with conversations
- Handling serialization/deserialization of complex types
- Maintaining proper datetime conversions