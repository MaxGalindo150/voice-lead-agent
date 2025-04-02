import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
import json
from datetime import datetime

from app.db.repository import ConversationRepository, LeadRepository
from app.models.conversation import Conversation, Message
from app.models.lead import Lead
from app.db.base import Database

class TestConversationRepository:
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path"""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        os.unlink(path)
    
    @pytest.fixture
    def db(self, temp_db_path):
        """Create a database instance"""
        return Database(db_path=temp_db_path)
    
    @pytest.fixture
    def repository(self, db):
        """Create a conversation repository instance"""
        return ConversationRepository(db=db)
    
    @pytest.fixture
    def lead_repository(self, db):
        """Create a lead repository instance"""
        return LeadRepository(db=db)
    
    @pytest.fixture
    def sample_lead(self, lead_repository):
        """Create and save a sample lead"""
        lead = Lead(
            id="lead123",
            nombre="John Doe",
            empresa="Acme Inc",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        lead_repository.save_lead(lead)
        return lead
    
    @pytest.fixture
    def sample_conversation(self, sample_lead):
        """Create a sample conversation"""
        conversation = Conversation(
            id="conv123",
            lead_id=sample_lead.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            summary="Test conversation summary",
            lead_info_extracted={"nombre": "John Doe", "necesidades": "Automation"}
        )
        
        # Add some messages
        conversation.messages = [
            Message(
                role="user",
                content="Hello, I need help with automation",
                timestamp=datetime.now()
            ),
            Message(
                role="assistant",
                content="I can help you with that. What kind of automation are you looking for?",
                timestamp=datetime.now()
            )
        ]
        
        return conversation
    
    def test_save_conversation(self, repository, sample_conversation):
        """Test saving a conversation"""
        # Save the conversation
        conv_id = repository.save_conversation(sample_conversation)
        
        # Check the conversation ID is returned
        assert conv_id == sample_conversation.id
        
        # Retrieve the conversation from the database to verify it was saved
        saved_conv = repository.get_conversation(conv_id)
        assert saved_conv is not None
        assert saved_conv.id == sample_conversation.id
        assert saved_conv.lead_id == sample_conversation.lead_id
        assert saved_conv.summary == sample_conversation.summary
        
        # Check messages were saved
        assert len(saved_conv.messages) == 2
        assert saved_conv.messages[0].role == "user"
        assert saved_conv.messages[1].role == "assistant"
    
    def test_get_conversation_not_found(self, repository):
        """Test getting a non-existent conversation"""
        conversation = repository.get_conversation("non_existent_id")
        assert conversation is None
    
    def test_get_conversations_by_lead(self, repository, sample_lead, sample_conversation):
        """Test getting conversations by lead"""
        # Save a conversation
        repository.save_conversation(sample_conversation)
        
        # Create and save another conversation for the same lead
        second_conv = Conversation(
            id="conv456",
            lead_id=sample_lead.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            summary="Second test conversation",
            lead_info_extracted={}
        )
        second_conv.messages = [
            Message(
                role="user",
                content="I have another question",
                timestamp=datetime.now()
            )
        ]
        repository.save_conversation(second_conv)
        
        # Get conversations for the lead
        conversations = repository.get_conversations_by_lead(sample_lead.id)
        
        # Check we have the two conversations
        assert len(conversations) == 2
        
        # Check the conversations are in the list
        conv_ids = [conv.id for conv in conversations]
        assert sample_conversation.id in conv_ids
        assert second_conv.id in conv_ids
    
    def test_delete_conversation(self, repository, sample_conversation):
        """Test deleting a conversation"""
        # Save a conversation
        repository.save_conversation(sample_conversation)
        
        # Delete the conversation
        result = repository.delete_conversation(sample_conversation.id)
        assert result is True
        
        # Verify the conversation is gone
        conv = repository.get_conversation(sample_conversation.id)
        assert conv is None
    
    def test_delete_conversation_not_found(self, repository):
        """Test deleting a non-existent conversation"""
        result = repository.delete_conversation("non_existent_id")
        assert result is False
    
    def test_get_all_conversations(self, repository, sample_conversation):
        """Test getting all conversations"""
        # Save a conversation
        repository.save_conversation(sample_conversation)
        
        # Create and save another conversation
        second_conv = Conversation(
            id="conv456",
            lead_id=sample_conversation.lead_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            summary="Second test conversation",
            lead_info_extracted={}
        )
        repository.save_conversation(second_conv)
        
        # Get all conversations
        conversations = repository.get_all_conversations()
        
        # Check we have at least the two conversations we saved
        assert len(conversations) >= 2
        
        # Check the conversations are in the list
        conv_ids = [conv.id for conv in conversations]
        assert sample_conversation.id in conv_ids
        assert second_conv.id in conv_ids