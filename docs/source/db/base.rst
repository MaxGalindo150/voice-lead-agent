Database - SQLite Database Interface
====================================

The ``Database`` class provides a base implementation for interacting with SQLite databases in the application. It handles connection management and schema initialization.

Class Overview
-------------

.. autoclass:: app.db.base.Database
   :members:
   :undoc-members:
   :show-inheritance:

Features
--------

- **Connection Management**: Establish and maintain SQLite database connections
- **Schema Initialization**: Automatically create required tables if they don't exist
- **Row Factory**: Return query results as dictionary-like objects
- **Directory Creation**: Create database directories if they don't exist

Methods
-------

### **`__init__`**
.. automethod:: app.db.base.Database.__init__

### **`_init_tables`**
.. automethod:: app.db.base.Database._init_tables

Database Schema
--------------

The database schema includes three main tables:

**Leads Table**
  Stores lead information with the following fields:
  
  - ``id``: Unique identifier (Primary Key)
  - ``nombre``: Lead's name
  - ``empresa``: Company name
  - ``cargo``: Position/role
  - ``email``: Email address
  - ``telefono``: Phone number
  - ``necesidades``: Identified needs
  - ``presupuesto``: Budget information
  - ``plazo``: Timeframe
  - ``punto_dolor``: Pain points
  - ``producto_interes``: Products of interest
  - ``conversation_stage``: Current stage in the sales process
  - ``created_at``: Creation timestamp
  - ``updated_at``: Last update timestamp
  - ``conversation_ids``: Related conversation IDs

**Conversations Table**
  Tracks conversations with leads:
  
  - ``id``: Unique identifier (Primary Key)
  - ``lead_id``: Reference to the associated lead
  - ``created_at``: Creation timestamp
  - ``updated_at``: Last update timestamp
  - ``ended_at``: Conversation end timestamp
  - ``summary``: Conversation summary
  - ``lead_info_extracted``: Information extracted from the conversation

**Messages Table**
  Stores individual messages within conversations:
  
  - ``id``: Auto-incremented ID (Primary Key)
  - ``conversation_id``: Reference to the associated conversation
  - ``role``: Message sender role (user/assistant)
  - ``content``: Message content
  - ``timestamp``: Message timestamp
  - ``audio_file_path``: Path to audio file (if any)
  - ``transcription``: Audio transcription (if applicable)

Error Handling
-------------

The ``Database`` class includes error handling for:

- Database initialization failures
- Table creation errors
- Directory creation issues

All errors are logged using the application's logging system.

Usage Example
-----------

.. code-block:: python

    # Create a database instance with default path
    db = Database()
    
    # Or specify a custom path
    custom_db = Database(db_path='data/custom_leads.db')
    
    # The database tables are automatically initialized