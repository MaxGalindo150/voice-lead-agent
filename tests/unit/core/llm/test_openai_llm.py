import unittest
from unittest.mock import patch, MagicMock

from app.core.llm.openai_llm import OpenAILLM


class TestOpenAILLM(unittest.TestCase):
    """Tests para la implementación de OpenAI LLM."""

    @patch('openai.OpenAI')
    def setUp(self, mock_openai):
        """Configuración común para todos los tests."""
        # Configurar mock del cliente de OpenAI
        self.mock_client = MagicMock()
        mock_openai.return_value = self.mock_client
        
        # Crear instancia de OpenAILLM
        self.llm = OpenAILLM(api_key="test_key", model="test_model", temperature=0.5)

    def test_initialization(self):
        """Verifica que se inicializa correctamente."""
        self.assertEqual(self.llm.api_key, "test_key")
        self.assertEqual(self.llm.model, "test_model")
        self.assertEqual(self.llm.temperature, 0.5)
        self.assertIsNotNone(self.llm.system_prompt)

    def test_generate(self):
        """Verifica que el método generate funciona correctamente."""
        # Configurar mock de la respuesta
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Respuesta de prueba"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        self.mock_client.chat.completions.create.return_value = mock_response
        
        # Llamar al método y verificar resultado
        result = self.llm.generate("Hola")
        
        self.assertEqual(result, "Respuesta de prueba")
        self.mock_client.chat.completions.create.assert_called_once()

    def test_generate_with_history(self):
        """Verifica que el método generate_with_history funciona correctamente."""
        # Configurar mock de la respuesta
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Respuesta con historial"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        self.mock_client.chat.completions.create.return_value = mock_response
        
        # Historial de prueba
        history = [
            {"role": "user", "content": "Hola"},
            {"role": "assistant", "content": "Hola, ¿en qué puedo ayudarte?"}
        ]
        
        # Llamar al método y verificar resultado
        result = self.llm.generate_with_history(history, "¿Qué servicios ofrecen?")
        
        self.assertEqual(result, "Respuesta con historial")
        self.mock_client.chat.completions.create.assert_called_once()

    def test_extract_info(self):
        """Verifica que el método extract_info funciona correctamente."""
        # Configurar mock de la respuesta con un JSON
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = '{"nombre": "Juan", "empresa": "ACME"}'
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        self.mock_client.chat.completions.create.return_value = mock_response
        
        # Llamar al método y verificar resultado
        result = self.llm.extract_info("Conversación de prueba")
        
        self.assertEqual(result["nombre"], "Juan")
        self.assertEqual(result["empresa"], "ACME")
        self.mock_client.chat.completions.create.assert_called_once()

    def test_handle_error_in_generate(self):
        """Verifica que se manejan los errores durante la generación."""
        # Configurar mock para lanzar una excepción
        self.mock_client.chat.completions.create.side_effect = Exception("Error de prueba")
        
        # Llamar al método y verificar que maneja el error correctamente
        result = self.llm.generate("Hola")
        
        self.assertIn("Lo siento", result)
        self.mock_client.chat.completions.create.assert_called_once()

    def test_extract_info_with_unexpected_json(self):
        """Verifica que extract_info maneja respuestas con formato JSON inesperado."""
        # Configurar mock con respuesta que tiene formato JSON inválido
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Esto no es JSON válido"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        self.mock_client.chat.completions.create.return_value = mock_response
        
        # Llamar al método y verificar que no falla
        result = self.llm.extract_info("Conversación de prueba")
        
        self.assertEqual(result, {})
        self.mock_client.chat.completions.create.assert_called_once()


if __name__ == '__main__':
    unittest.main()