import json
import logging
from typing import List, Dict, Any, Optional

from app.core.llm.base import BaseLLM
from app import config

# Configure logger
logger = logging.getLogger(__name__)

class OpenAILLM(BaseLLM):
    """
    LLM implementation that uses the OpenAI API.
    """
    
    def __init__(self, api_key: str = None, model: str = None, temperature: float = None):
        """
        Initialize the OpenAI LLM.
        
        Args:
            api_key (str, optional): OpenAI API key. If not provided, the one from config is used.
            model (str, optional): Model to use. By default, the one defined in config.
            temperature (float, optional): Temperature for generation. By default, the one from config.
        """
        self.api_key = api_key or config.OPENAI_API_KEY
        self.model = model or config.OPENAI_MODEL
        self.temperature = temperature if temperature is not None else config.OPENAI_TEMPERATURE
        
        # OpenAI client
        self.client = None
        
        # Default system prompt
        self.system_prompt = """
        Eres un asistente virtual especializado en ventas llamado LeadBot. 
        Tu objetivo es recopilar información importante de prospectos de manera conversacional y amigable.
        
        Información importante que debes recopilar durante la conversación:
        - Nombre completo del prospecto
        - Empresa donde trabaja
        - Cargo o rol en la empresa
        - Necesidades o desafíos que enfrenta
        - Presupuesto disponible (si es apropiado preguntar)
        - Plazos o tiempos para implementar soluciones
        
        Mantén un tono profesional pero cercano. Haz preguntas abiertas y muestra 
        interés en lo que dice el prospecto. No hagas todas las preguntas de una vez,
        mantén una conversación natural.
        """
        
        # Initialize client
        self._initialize_client()
    
    def _initialize_client(self):
        """
        Initialize the OpenAI client.
        """
        try:
            from openai import OpenAI
            
            if not self.api_key:
                logger.error("No OpenAI API key provided")
                raise ValueError("An API key is required for OpenAI")
            
            self.client = OpenAI(api_key=self.api_key)
            logger.info(f"OpenAI client initialized for model {self.model}")
            
        except ImportError:
            logger.error("The 'openai' library is not installed. Install with: pip install openai")
            raise
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {str(e)}")
            raise
    
    def generate(self, prompt: str) -> str:
        """
        Generate a response based on a simple prompt.
        
        Args:
            prompt (str): The prompt or instruction for the model.
            
        Returns:
            str: The generated response.
        """
        if not self.client:
            logger.error("OpenAI client not initialized")
            return "Sorry, I cannot process your request at this time."
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=512
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating response with OpenAI: {str(e)}")
            return "Sorry, an error occurred while processing your request."
    
    def generate_with_history(self, history: List[Dict[str, str]], user_input: str) -> str:
        """
        Generate a response based on conversation history and current input.
        
        Args:
            history (List[Dict]): History of previous messages.
            user_input (str): Current user input.
            
        Returns:
            str: The generated response.
        """
        if not self.client:
            logger.error("OpenAI client not initialized")
            return "Sorry, I cannot process your request at this time."
        
        try:
            # Convert history to the format expected by OpenAI
            messages = [{"role": "system", "content": self.system_prompt}]
            
            for msg in history:
                role = "user" if msg["role"] == "user" else "assistant"
                messages.append({"role": role, "content": msg["content"]})
            
            # Add the current user input
            messages.append({"role": "user", "content": user_input})
            
            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=512
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating response with OpenAI: {str(e)}")
            return "Sorry, an error occurred while processing your request."
    
    def extract_info(self, conversation_text: str) -> Dict[str, Any]:
        """
        Extract structured information from a conversation.
        
        Args:
            conversation_text (str): Conversation text.
            
        Returns:
            Dict[str, Any]: Dictionary with extracted information.
        """
        if not self.client:
            logger.error("OpenAI client not initialized")
            return {}
        
        try:
            # Create a specific prompt for information extraction
            extraction_prompt = f"""
            Analiza la siguiente conversación entre un asistente virtual y un prospecto.
            Extrae la siguiente información si está disponible:
            - nombre: Nombre completo del prospecto
            - empresa: Nombre de la empresa donde trabaja
            - cargo: Cargo o rol del prospecto
            - necesidades: Problemas o necesidades mencionadas
            - presupuesto: Información sobre presupuesto disponible
            - plazo: Plazos o tiempos mencionados
            - email: Dirección de correo electrónico (si se menciona)
            - telefono: Número de teléfono (si se menciona)
            
            Devuelve ÚNICAMENTE un objeto JSON con estos campos. 
            Si no puedes identificar alguno de estos datos, omite el campo.
            No incluyas explicaciones adicionales, solo el JSON.
            
            Conversación:
            {conversation_text}
            """
            
            # Request extraction from the model
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Eres un asistente que extrae información estructurada de conversaciones."},
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=0.1,  # Low temperature for more deterministic results
                max_tokens=1024
            )
            
            content = response.choices[0].message.content
            
            # Process the response to extract the JSON
            try:
                # Remove possible code decorators
                cleaned_content = content.strip()
                if cleaned_content.startswith("json"):
                    cleaned_content = cleaned_content.replace("json", "", 1)
                if cleaned_content.endswith(""):
                    cleaned_content = cleaned_content.rstrip("")
                
                # Parse JSON
                result = json.loads(cleaned_content.strip())
                return result
            except json.JSONDecodeError as e:
                logger.warning(f"Could not parse JSON: {str(e)}")
                # Try to recover using regex as fallback
                import re
                json_match = re.search(r'(\{.*\})', content, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group(1))
                    except:
                        pass
                return {}
            
        except Exception as e:
            logger.error(f"Error extracting information: {str(e)}")
            return {}