import pytest
from unittest.mock import patch, MagicMock
import os

from app.core.conversation import ConversationManager


class TestConversationManager:
    """Test suite for ConversationManager class"""
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        # Create mocks for dependencies
        self.mock_llm = MagicMock()
        self.mock_asr = MagicMock()
        self.mock_tts = MagicMock()
        self.mock_lead_repo = MagicMock()
        self.mock_conversation_repo = MagicMock()
        
        # Create instance with mocked dependencies
        self.manager = ConversationManager(
            llm=self.mock_llm,
            asr=self.mock_asr,
            tts=self.mock_tts,
            lead_repo=self.mock_lead_repo,
            conversation_repo=self.mock_conversation_repo
        )
    
    def test_initialization(self):
        """Test basic initialization of ConversationManager"""
        # Verify dependencies are set correctly
        assert self.manager.llm == self.mock_llm
        assert self.manager.asr == self.mock_asr
        assert self.manager.tts == self.mock_tts
        assert self.manager.lead_repo == self.mock_lead_repo
        assert self.manager.conversation_repo == self.mock_conversation_repo
        
        # Verify audio directory was created
        assert os.path.exists(self.manager.audio_dir)
    
    def test_start_conversation(self):
        """Test starting a new conversation"""
        # Call the method
        conversation_id = self.manager.start_conversation()
        
        # Verify a conversation ID was returned
        assert conversation_id is not None
        assert isinstance(conversation_id, str)
        
        # Verify conversation was saved
        self.mock_conversation_repo.save_conversation.assert_called_once()
        
        # Verify TTS was called
        self.mock_tts.synthesize.assert_called_once()
        
        # Verify conversation is in active conversations dict
        assert conversation_id in self.manager.active_conversations
    
    @patch('app.core.conversation.ConversationOrchestrator')
    def test_process_text_message(self, mock_orchestrator_class):
        """Test processing a text message"""
        # Setup mock orchestrator
        mock_orchestrator = MagicMock()
        mock_orchestrator_class.return_value = mock_orchestrator
        
        # Setup mock response from orchestrator
        mock_orchestrator.process_message.return_value = {
            "response": "This is a test response",
            "lead_info": {"name": "Test User"},
            "stage": "introduction"
        }
        
        # Create a conversation
        conversation_id = self.manager.start_conversation()
        
        # Reset mocks for clarity
        self.mock_conversation_repo.reset_mock()
        self.mock_tts.reset_mock()
        
        # Call the method
        result = self.manager.process_text_message(conversation_id, "Hello")
        
        # Verify orchestrator was called with the message
        mock_orchestrator.process_message.assert_called_once_with("Hello")
        
        # Verify TTS was called for the response
        self.mock_tts.synthesize.assert_called_once()
        
        # Verify conversation was saved
        self.mock_conversation_repo.save_conversation.assert_called_once()
        
        # Verify basic fields in the response
        assert result["conversation_id"] == conversation_id
        assert result["user_message"] == "Hello"
        assert result["assistant_response"] == "This is a test response"
        assert result["lead_info"] == {"name": "Test User"}
    
    def test_process_audio_message(self):
        """Test processing an audio message"""
        # Setup mock for ASR transcription
        self.mock_asr.transcribe.return_value = {
            "success": True,
            "text": "Hello from audio",
            "segments": []
        }
        
        # Create a conversation
        conversation_id = self.manager.start_conversation()
        
        # Mock _save_audio_file to avoid file operations
        self.manager._save_audio_file = MagicMock(return_value="/tmp/audio.wav")
        
        # Mock process_text_message to isolate the test
        self.manager.process_text_message = MagicMock(return_value={
            "assistant_response": "I heard you"
        })
        
        # Call the method
        audio_data = b"fake_audio_data"
        result = self.manager.process_audio_message(conversation_id, audio_data)
        
        # Verify audio file was saved
        self.manager._save_audio_file.assert_called_once_with(audio_data, conversation_id, "user")
        
        # Verify ASR was called
        self.mock_asr.transcribe.assert_called_once_with(audio_data)
        
        # Verify process_text_message was called with the transcribed text
        self.manager.process_text_message.assert_called_once_with(conversation_id, "Hello from audio")
        
        # Verify transcription is in the result
        assert "transcription" in result
        assert result["transcription"]["text"] == "Hello from audio"
    
    def test_end_conversation(self):
        """Test ending a conversation"""
        # Create a conversation
        conversation_id = self.manager.start_conversation()
        
        # Get the mock conversation object
        conversation = self.mock_conversation_repo.save_conversation.call_args[0][0]
        
        # Reset mocks for clarity
        self.mock_conversation_repo.reset_mock()
        
        # Call the method
        result = self.manager.end_conversation(conversation_id)
        
        # Verify result is True (success)
        assert result is True
        
        # Verify LLM was called to generate a summary
        self.mock_llm.generate.assert_called_once()
        
        # Verify conversation was saved with the summary
        self.mock_conversation_repo.save_conversation.assert_called_once_with(conversation)
        
        # Verify conversation was removed from active conversations
        assert conversation_id not in self.manager.active_conversations
    
    def test_get_conversation_history(self):
        """Test getting conversation history"""
        # Create a conversation
        conversation_id = self.manager.start_conversation()
        
        # Get the mock conversation object
        conversation = self.mock_conversation_repo.save_conversation.call_args[0][0]
        
        # Setup mock messages in the conversation
        message1 = MagicMock()
        message1.to_dict.return_value = {"role": "assistant", "content": "Welcome message"}
        message2 = MagicMock()
        message2.to_dict.return_value = {"role": "user", "content": "Hello"}
        conversation.messages = [message1, message2]
        
        # Call the method
        history = self.manager.get_conversation_history(conversation_id)
        
        # Verify history contains expected messages
        assert len(history) == 2
        assert history[0]["role"] == "assistant"
        assert history[0]["content"] == "Welcome message"
        assert history[1]["role"] == "user"
        assert history[1]["content"] == "Hello"
    
    def test_get_lead_info(self):
        """Test getting lead info from a conversation"""
        # Create a conversation with a lead
        lead_id = "test_lead_id"
        conversation_id = self.manager.start_conversation(lead_id=lead_id)
        
        # Setup mock lead
        mock_lead = MagicMock()
        mock_lead.to_dict.return_value = {"id": lead_id, "name": "Test User", "email": "test@example.com"}
        self.mock_lead_repo.get_lead.return_value = mock_lead
        
        # Call the method
        lead_info = self.manager.get_lead_info(conversation_id)
        
        # Verify lead repository was called
        self.mock_lead_repo.get_lead.assert_called_with(lead_id)
        
        # Verify returned lead info
        assert lead_info["id"] == lead_id
        assert lead_info["name"] == "Test User"
        assert lead_info["email"] == "test@example.com"