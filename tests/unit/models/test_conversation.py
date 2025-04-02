import pytest
from datetime import datetime, timedelta
import json

from app.models.conversation import Message, Conversation

class TestMessage:
    
    def test_message_creation(self):
        """Test creating a message with default values"""
        message = Message(role="user", content="Hello")
        
        assert message.role == "user"
        assert message.content == "Hello"
        assert isinstance(message.timestamp, datetime)
        assert message.audio_file_path is None
        assert message.transcription is None
    
    def test_message_with_audio(self):
        """Test creating a message with audio data"""
        message = Message(
            role="user",
            content="Hello",
            audio_file_path="/path/to/audio.mp3",
            transcription="Hello there"
        )
        
        assert message.audio_file_path == "/path/to/audio.mp3"
        assert message.transcription == "Hello there"
    
    def test_message_to_dict(self):
        """Test converting a message to dictionary"""
        # Create a message with a fixed timestamp for easier testing
        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        message = Message(
            role="assistant",
            content="How can I help you?",
            timestamp=timestamp
        )
        
        # Convert to dictionary
        message_dict = message.to_dict()
        
        assert message_dict["role"] == "assistant"
        assert message_dict["content"] == "How can I help you?"
        assert message_dict["timestamp"] == timestamp.isoformat()
    
    def test_message_from_dict(self):
        """Test creating a message from dictionary"""
        message_dict = {
            "role": "user",
            "content": "I need help",
            "timestamp": "2023-01-01T12:00:00",
            "audio_file_path": "/path/to/audio.mp3"
        }
        
        message = Message.from_dict(message_dict)
        
        assert message.role == "user"
        assert message.content == "I need help"
        assert message.timestamp == datetime(2023, 1, 1, 12, 0, 0)
        assert message.audio_file_path == "/path/to/audio.mp3"

class TestConversation:
    
    def test_conversation_creation(self):
        """Test creating a conversation with default values"""
        conversation = Conversation(lead_id="lead123")
        
        assert conversation.lead_id == "lead123"
        assert isinstance(conversation.id, str)
        assert len(conversation.id) > 0
        assert isinstance(conversation.created_at, datetime)
        assert isinstance(conversation.updated_at, datetime)
        assert conversation.ended_at is None
        assert conversation.messages == []
        assert conversation.summary is None
        assert conversation.lead_info_extracted == {}
    
    def test_add_message(self):
        """Test adding a message to a conversation"""
        conversation = Conversation(lead_id="lead123")
        
        # Add a message
        conversation.add_message(role="user", content="Hello")
        
        # Check message was added
        assert len(conversation.messages) == 1
        assert conversation.messages[0].role == "user"
        assert conversation.messages[0].content == "Hello"
        
        # Add another message with audio
        conversation.add_message(
            role="assistant",
            content="How can I help?",
            audio_file_path="/path/to/response.mp3"
        )
        
        # Check second message
        assert len(conversation.messages) == 2
        assert conversation.messages[1].role == "assistant"
        assert conversation.messages[1].audio_file_path == "/path/to/response.mp3"
    
    def test_end_conversation(self):
        """Test ending a conversation"""
        conversation = Conversation()
        
        # Initially the conversation is not ended
        assert conversation.ended_at is None
        
        # End the conversation
        conversation.end_conversation()
        
        # Check it's now ended
        assert conversation.ended_at is not None
        assert isinstance(conversation.ended_at, datetime)
    
    def test_conversation_to_dict(self):
        """Test converting a conversation to dictionary"""
        # Create a conversation with fixed timestamps
        created = datetime(2023, 1, 1, 12, 0, 0)
        updated = datetime(2023, 1, 1, 12, 30, 0)
        
        conversation = Conversation(
            id="conv123",
            lead_id="lead456",
            created_at=created,
            updated_at=updated,
            summary="Test conversation summary",
            lead_info_extracted={"name": "John", "interest": "Product A"}
        )
        
        # Add messages
        conversation.messages = [
            Message(role="user", content="Hello", timestamp=created),
            Message(role="assistant", content="Hi there", timestamp=updated)
        ]
        
        # Convert to dictionary
        conv_dict = conversation.to_dict()
        
        assert conv_dict["id"] == "conv123"
        assert conv_dict["lead_id"] == "lead456"
        assert conv_dict["created_at"] == created.isoformat()
        assert conv_dict["updated_at"] == updated.isoformat()
        assert conv_dict["summary"] == "Test conversation summary"
        assert conv_dict["lead_info_extracted"] == {"name": "John", "interest": "Product A"}
        assert len(conv_dict["messages"]) == 2
        assert conv_dict["messages"][0]["role"] == "user"
        assert conv_dict["messages"][1]["role"] == "assistant"
    
    def test_conversation_from_dict(self):
        """Test creating a conversation from dictionary"""
        created_str = "2023-01-01T12:00:00"
        updated_str = "2023-01-01T12:30:00"
        ended_str = "2023-01-01T13:00:00"
        
        conv_dict = {
            "id": "conv123",
            "lead_id": "lead456",
            "created_at": created_str,
            "updated_at": updated_str,
            "ended_at": ended_str,
            "summary": "Test summary",
            "lead_info_extracted": {"name": "John"},
            "messages": [
                {
                    "role": "user",
                    "content": "Hello",
                    "timestamp": created_str
                },
                {
                    "role": "assistant",
                    "content": "Hi there",
                    "timestamp": updated_str
                }
            ]
        }
        
        conversation = Conversation.from_dict(conv_dict)
        
        assert conversation.id == "conv123"
        assert conversation.lead_id == "lead456"
        assert conversation.created_at == datetime.fromisoformat(created_str)
        assert conversation.updated_at == datetime.fromisoformat(updated_str)
        assert conversation.ended_at == datetime.fromisoformat(ended_str)
        assert conversation.summary == "Test summary"
        assert conversation.lead_info_extracted == {"name": "John"}
        assert len(conversation.messages) == 2
        assert conversation.messages[0].role == "user"
        assert conversation.messages[0].content == "Hello"
        assert conversation.messages[1].role == "assistant"
        assert conversation.messages[1].content == "Hi there"