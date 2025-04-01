# core/langchain_integration.py
from typing import Dict, List, Any, Optional
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage

from app.core.llm.base import BaseLLM
from app import config

class ConversationOrchestrator:
    """
    Orquestador de conversaciones usando Langchain para mantener el contexto
    y estructurar el flujo de la conversación con el lead.
    """
    
    def __init__(self, llm: BaseLLM, initial_context: Dict[str, Any] = None):
        """
        Inicializa el orquestador de conversaciones.
        
        Args:
            llm (BaseLLM): Modelo de lenguaje a utilizar
            initial_context (Dict[str, Any], optional): Contexto inicial si existe
        """
        self.llm = llm
        self.lead_info = initial_context or {}
        self.memory = ConversationBufferMemory()
        self.conversation_stage = "introduccion"
        
        # Historial de mensajes para tracking
        self.message_history = []
    
    def get_stage_prompt(self) -> str:
        """
        Obtiene el prompt específico para la etapa actual de la conversación.
        """
        prompts = {
            "introduccion": """
            Estás en la etapa de introducción. Preséntate brevemente como LeadBot y 
            pregunta el nombre del prospecto y su empresa de manera amigable. 
            No hagas demasiadas preguntas a la vez.
            """,
            
            "identificacion_necesidades": """
            Estás en la etapa de identificación de necesidades. Ya conoces al prospecto.
            Pregunta sobre los desafíos o problemas que enfrenta su empresa actualmente.
            Usa preguntas abiertas para entender mejor sus necesidades.
            """,
            
            "calificacion": """
            Estás en la etapa de calificación. Ya conoces las necesidades del prospecto.
            Ahora, pregunta sutilmente sobre presupuesto, plazos o recursos disponibles.
            Mantén un tono profesional y no seas demasiado directo.
            """,
            
            "propuesta": """
            Estás en la etapa de propuesta. Con la información recopilada, presenta
            cómo nuestras soluciones podrían ayudar al prospecto con sus necesidades.
            Destaca los beneficios relevantes para su situación específica.
            """,
            
            "cierre": """
            Estás en la etapa de cierre. Resume los puntos clave de la conversación
            y sugiere un siguiente paso concreto, como una demostración o una reunión
            con un especialista. Pregunta si esto le parece bien.
            """
        }
        
        return prompts.get(self.conversation_stage, prompts["introduccion"])
    
    def advance_stage(self):
        """
        Avanza a la siguiente etapa de la conversación.
        """
        stages = ["introduccion", "identificacion_necesidades", "calificacion", "propuesta", "cierre"]
        current_index = stages.index(self.conversation_stage)
        
        if current_index < len(stages) - 1:
            self.conversation_stage = stages[current_index + 1]
            return True
        return False
    
    def should_advance_stage(self) -> bool:
        """
        Determina si se debe avanzar a la siguiente etapa basado en la información recopilada.
        """
        if self.conversation_stage == "introduccion":
            # Avanzar si tenemos nombre y empresa
            return bool(self.lead_info.get("nombre") and self.lead_info.get("empresa"))
            
        elif self.conversation_stage == "identificacion_necesidades":
            # Avanzar si tenemos alguna necesidad identificada
            return bool(self.lead_info.get("necesidades"))
            
        elif self.conversation_stage == "calificacion":
            # Avanzar si tenemos información sobre presupuesto o plazos
            return bool(self.lead_info.get("presupuesto") or self.lead_info.get("plazo"))
            
        elif self.conversation_stage == "propuesta":
            # Criterio para pasar de propuesta a cierre (podría ser más complejo)
            # Por simplicidad, usamos un contador de mensajes en esta etapa
            stage_messages = sum(1 for msg in self.message_history[-5:] if self.conversation_stage == "propuesta")
            return stage_messages >= 2
            
        return False
    
    def process_message(self, user_input: str) -> Dict[str, Any]:
        """
        Procesa un mensaje del usuario y genera una respuesta.
        
        Args:
            user_input (str): Mensaje del usuario
            
        Returns:
            Dict[str, Any]: Respuesta y metadatos
        """
        # Añadir mensaje al historial
        self.message_history.append({"role": "user", "content": user_input})
        
        # Construir contexto para el prompt
        context = f"""
        Información actual del lead: {self.lead_info}
        Etapa actual de conversación: {self.conversation_stage}
        
        {self.get_stage_prompt()}
        
        Recuerda mantener un tono conversacional y amigable.
        """
        
        # Convertir historial al formato esperado por el LLM
        formatted_history = [{"role": msg["role"], "content": msg["content"]} for msg in self.message_history]
        
        # Generar respuesta
        response = self.llm.generate_with_history(formatted_history, context)
        
        # Añadir respuesta al historial
        self.message_history.append({"role": "assistant", "content": response})
        
        # Extraer información del lead de la conversación
        full_conversation = "\n".join([
            f"{'Usuario' if msg['role'] == 'user' else 'Asistente'}: {msg['content']}" 
            for msg in self.message_history
        ])
        
        extracted_info = self.llm.extract_info(full_conversation)
        
        # Actualizar información del lead
        if extracted_info:
            self.lead_info.update(extracted_info)
            
            # Evaluar si se debe avanzar a la siguiente etapa
            if self.should_advance_stage():
                self.advance_stage()
        
        return {
            "response": response,
            "lead_info": self.lead_info,
            "stage": self.conversation_stage,
            "extracted_info": extracted_info
        }