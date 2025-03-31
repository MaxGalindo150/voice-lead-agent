import unittest
from unittest.mock import patch, MagicMock

from app.core.llm.factory import create_llm
from app.core.llm.openai_llm import OpenAILLM


class TestLLMFactory(unittest.TestCase):
    """Tests para el factory de LLM."""

    @patch('app.core.llm.factory.OpenAILLM')
    def test_create_openai_llm(self, mock_openai_llm):
        """Verifica que se crea correctamente un LLM de OpenAI."""
        # Configurar el mock
        mock_instance = MagicMock()
        mock_openai_llm.return_value = mock_instance

        # Llamar a la factory
        llm = create_llm("openai")

        # Verificar que se llamó al constructor con los parámetros correctos
        mock_openai_llm.assert_called_once()
        self.assertEqual(llm, mock_instance)

    @patch('app.core.llm.factory.OpenAILLM')
    def test_auto_mode_fallback_to_openai(self, mock_openai_llm):
        """Verifica que el modo auto hace fallback a OpenAI cuando Mistral falla."""
        # Configurar el mock de OpenAI
        openai_instance = MagicMock()
        mock_openai_llm.return_value = openai_instance

        # Patch para simular un error al importar MistralLLM
        with patch('app.core.llm.factory.logger'), \
             patch('importlib.import_module', side_effect=ImportError("No module named 'ctransformers'")):
            
            # Llamar a la factory en modo auto
            llm = create_llm("auto")

            # Verificar que se usó OpenAI como fallback
            mock_openai_llm.assert_called_once()
            self.assertEqual(llm, openai_instance)

    def test_invalid_llm_type(self):
        """Verifica que se lanza una excepción con un tipo de LLM inválido."""
        with self.assertRaises(ValueError):
            create_llm("invalid_type")


if __name__ == '__main__':
    unittest.main()