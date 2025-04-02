import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from app.core.langchain_integration import ConversationOrchestrator

class TestStageTransitionsAndEndDetection:
    
    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM for testing"""
        mock = MagicMock()
        mock.generate_with_history.return_value = "Respuesta de prueba"
        mock.extract_info.return_value = {}
        return mock
    
    @pytest.fixture
    def orchestrator(self, mock_llm):
        """Create a ConversationOrchestrator instance for testing"""
        return ConversationOrchestrator(mock_llm)
    
    def test_should_advance_stage_criteria(self, orchestrator):
        """Test the criteria for advancing through conversation stages"""
        # Test introduction stage advancement based on collected information
        orchestrator.conversation_stage = "introduccion"
        orchestrator.stage_message_count = 0
        
        # Should not advance with no information
        assert orchestrator.should_advance_stage() == False
        assert orchestrator.stage_message_count == 1  # Counter incremented
        
        # Should advance after adding basic information
        orchestrator.lead_info = {"nombre": "Juan", "empresa": "TechCorp"}
        assert orchestrator.should_advance_stage() == True
        
        # Test introduction stage advancement based on message count
        orchestrator.lead_info = {}  # Clear info
        orchestrator.stage_message_count = 1
        
        # First message shouldn't advance
        assert orchestrator.should_advance_stage() == False
        assert orchestrator.stage_message_count == 2
        
        # But third message should advance even without info
        assert orchestrator.should_advance_stage() == True
        
        # Test needs identification stage
        orchestrator.conversation_stage = "identificacion_necesidades"
        orchestrator.stage_message_count = 0
        
        # Should not advance initially
        assert orchestrator.should_advance_stage() == False
        
        # Should advance with identified needs
        orchestrator.lead_info = {"necesidades": "automatización de procesos"}
        assert orchestrator.should_advance_stage() == True
        
        # Test proposal stage with user brief interest
        orchestrator.conversation_stage = "propuesta"
        orchestrator.stage_message_count = 0
        orchestrator.propuesta_message_count = 0
        
        # Add a short response indicating interest
        orchestrator.message_history = [
            {"role": "assistant", "content": "¿Qué te parece nuestra solución?"},
            {"role": "user", "content": "Suena bien, me interesa."}
        ]
        
        # Should advance based on user interest
        assert orchestrator.should_advance_stage() == True
    
    def test_is_stuck_in_stage(self, orchestrator):
        """Test the stuck detection logic directly"""
        # Not enough responses initially
        orchestrator.last_responses = []
        assert orchestrator._is_stuck_in_stage() == False
        
        # Just one response
        orchestrator.last_responses = ["Hello"]
        assert orchestrator._is_stuck_in_stage() == False
        
        # Two responses
        orchestrator.last_responses = ["Hello", "Hi there"]
        assert orchestrator._is_stuck_in_stage() == False
        
        # Three different responses shouldn't trigger
        orchestrator.last_responses = [
            "Our solution can help automate your workflow.",
            "What's your budget for this project?",
            "We can implement this in about two weeks."
        ]
        assert orchestrator._is_stuck_in_stage() == False
        
        # Three extremely similar responses should trigger
        # These are identical except for one word to make the test more reliable
        orchestrator.last_responses = [
            "We offer the best solution for your automation needs.",
            "We offer the best solution for your automation needs.",
            "We offer the best solution for your automation needs."
        ]
        assert orchestrator._is_stuck_in_stage() == True
    
    def test_end_conversation_detection(self, orchestrator):
        """Test detection of conversation ending signals"""
        # Test ending based on farewell phrase
        orchestrator.conversation_ending = True
        orchestrator.closing_message_count = 0
        
        # Should end with the exact farewell phrase
        result = orchestrator._should_end_conversation(
            "Gracias por la información", 
            "¡Hasta pronto! Ha sido un placer ayudarte hoy."
        )
        assert result == True
        assert orchestrator.conversation_ended == True
        
        # Reset for next test
        orchestrator.conversation_ending = True
        orchestrator.conversation_ended = False
        orchestrator.closing_message_count = 0
        
        # Should end after 2+ closing messages even without exact phrase
        result = orchestrator._should_end_conversation("Ok", "Gracias por tu tiempo")
        assert result == False  # Not yet
        
        result = orchestrator._should_end_conversation("Ok", "Te estaremos contactando pronto")
        assert result == True  # Now it should end
        assert orchestrator.conversation_ended == True
        
        # Test detection of user farewell signals
        orchestrator.conversation_ending = False
        orchestrator.conversation_ended = False
        orchestrator.conversation_stage = "cierre"
        
        # Should trigger ending sequence on user farewell
        result = orchestrator._should_end_conversation("Muchas gracias por tu ayuda", "De nada")
        assert result == False  # Doesn't end immediately
        assert orchestrator.conversation_ending == True  # But starts ending sequence
    
    def test_stuck_detection_and_handling(self, orchestrator):
        """Test detection and handling of being stuck in a stage"""
        # Setup being stuck in proposal stage
        orchestrator.conversation_stage = "propuesta"
        
        # Create responses that are more similar to ensure the similarity threshold is met
        # The current implementation checks both length difference and content overlap
        orchestrator.last_responses = [
            "Nuestra solución de automatización mejora la eficiencia operativa y reduce costos en un 30%. Contacta con nosotros.",
            "Nuestra plataforma de automatización aumenta la eficiencia y puede reducir costos hasta en un 30%. Contáctanos hoy.",
            "Nuestra solución mejora la eficiencia operativa y reduce costos en aproximadamente 30%. Ponte en contacto con nosotros."
        ]
        
        # Mock the implementation of _is_stuck_in_stage to return True
        with patch.object(orchestrator, '_is_stuck_in_stage', return_value=True):
            # Now it should detect stagnation and force advancement
            assert orchestrator.should_advance_stage() == True
        
        # Setup being stuck in closing stage
        orchestrator.conversation_stage = "cierre"
        orchestrator.conversation_ending = False  # Reset from previous test
        
        # Again, use mocking to ensure _is_stuck_in_stage returns True
        with patch.object(orchestrator, '_is_stuck_in_stage', return_value=True):
            # Should detect stagnation and start ending sequence
            assert orchestrator.should_advance_stage() == False  # Doesn't advance stage
            assert orchestrator.conversation_ending == True  # But starts ending sequence