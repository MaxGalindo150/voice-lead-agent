import json
import logging
from typing import List, Dict, Any, Optional

from app.core.llm.base import BaseLLM
from app import config

# Configurar logger
logger = logging.getLogger(__name__)

class OpenAILLM(BaseLLM):
    """
    Implementación de LLM que utiliza la API de OpenAI.
    """
    
    def __init__(self, api_key: str = None, model: str = None, temperature: float = None):
        """
        Inicializa el LLM de OpenAI.
        
        Args:
            api_key (str, optional): Clave API de OpenAI. Si no se proporciona, se usa la de config.
            model (str, optional): Modelo a utilizar. Por defecto, el definido en config.
            temperature (float, optional): Temperatura para la generación. Por defecto, la de config.
        """
        self.api_key = api_key or config.OPENAI_API_KEY
        self.model = model or config.OPENAI_MODEL
        self.temperature = temperature if temperature is not None else config.OPENAI_TEMPERATURE
        
        # Cliente de OpenAI
        self.client = None
        
        # Prompt del sistema por defecto
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
        
        # Inicializar cliente
        self._initialize_client()
    
    def _initialize_client(self):
        """
        Inicializa el cliente de OpenAI.
        """
        try:
            from openai import OpenAI
            
            if not self.api_key:
                logger.error("No se ha proporcionado una clave API para OpenAI")
                raise ValueError("Se requiere una clave API para OpenAI")
            
            self.client = OpenAI(api_key=self.api_key)
            logger.info(f"Cliente OpenAI inicializado para modelo {self.model}")
            
        except ImportError:
            logger.error("La biblioteca 'openai' no está instalada. Instala con: pip install openai")
            raise
        except Exception as e:
            logger.error(f"Error al inicializar el cliente OpenAI: {str(e)}")
            raise
    
    def generate(self, prompt: str) -> str:
        """
        Genera una respuesta basada en un prompt simple.
        
        Args:
            prompt (str): El prompt o instrucción para el modelo.
            
        Returns:
            str: La respuesta generada.
        """
        if not self.client:
            logger.error("Cliente OpenAI no inicializado")
            return "Lo siento, no puedo procesar tu solicitud en este momento."
        
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
            logger.error(f"Error al generar respuesta con OpenAI: {str(e)}")
            return "Lo siento, ocurrió un error al procesar tu solicitud."
    
    def generate_with_history(self, history: List[Dict[str, str]], user_input: str) -> str:
        """
        Genera una respuesta basada en el historial de conversación y la entrada actual.
        
        Args:
            history (List[Dict]): Historial de mensajes anteriores.
            user_input (str): Entrada actual del usuario.
            
        Returns:
            str: La respuesta generada.
        """
        if not self.client:
            logger.error("Cliente OpenAI no inicializado")
            return "Lo siento, no puedo procesar tu solicitud en este momento."
        
        try:
            # Convertir historial al formato esperado por OpenAI
            messages = [{"role": "system", "content": self.system_prompt}]
            
            for msg in history:
                role = "user" if msg["role"] == "user" else "assistant"
                messages.append({"role": role, "content": msg["content"]})
            
            # Añadir la entrada actual del usuario
            messages.append({"role": "user", "content": user_input})
            
            # Generar respuesta
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=512
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error al generar respuesta con OpenAI: {str(e)}")
            return "Lo siento, ocurrió un error al procesar tu solicitud."
    
    def extract_info(self, conversation_text: str) -> Dict[str, Any]:
        """
        Extrae información estructurada de una conversación.
        
        Args:
            conversation_text (str): Texto de la conversación.
            
        Returns:
            Dict[str, Any]: Diccionario con información extraída.
        """
        if not self.client:
            logger.error("Cliente OpenAI no inicializado")
            return {}
        
        try:
            # Crear un prompt específico para extracción de información
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
            
            # Solicitar extracción al modelo
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Eres un asistente que extrae información estructurada de conversaciones."},
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=0.1,  # Temperatura baja para resultados más deterministas
                max_tokens=1024
            )
            
            content = response.choices[0].message.content
            
            # Procesar la respuesta para extraer el JSON
            try:
                # Eliminar posibles decoradores de código
                cleaned_content = content.strip()
                if cleaned_content.startswith("json"):
                    cleaned_content = cleaned_content.replace("json", "", 1)
                if cleaned_content.endswith(""):
                    cleaned_content = cleaned_content.rstrip("")
                
                # Parsear JSON
                result = json.loads(cleaned_content.strip())
                return result
            except json.JSONDecodeError as e:
                logger.warning(f"No se pudo parsear el JSON: {str(e)}")
                # Intento recuperar usando regex como fallback
                import re
                json_match = re.search(r'(\{.*\})', content, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group(1))
                    except:
                        pass
                return {}
            
        except Exception as e:
            logger.error(f"Error al extraer información: {str(e)}")
            return {}