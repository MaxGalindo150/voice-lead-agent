# app/core/conversation.py
import uuid
import os
import tempfile
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.core.asr import WhisperASR
from app.core.tts import TTSProcessor
from app.core.langchain_integration import ConversationOrchestrator
from app.core.llm.base import BaseLLM
from app.db.repository import LeadRepository, ConversationRepository
from app.models.conversation import Conversation, Message
from app.models.lead import Lead

logger = logging.getLogger(__name__)

class ConversationManager:
    """
    Administrador de conversaciones que integra ASR, LLM y TTS.
    """
    
    def __init__(self, 
                 llm: BaseLLM, 
                 asr: Optional[WhisperASR] = None,
                 tts: Optional[TTSProcessor] = None,
                 lead_repo: Optional[LeadRepository] = None,
                 conversation_repo: Optional[ConversationRepository] = None):
        """
        Inicializa el administrador de conversaciones.
        
        Args:
            llm (BaseLLM): Modelo de lenguaje
            asr (WhisperASR, optional): Procesador de reconocimiento de voz
            tts (TTSProcessor, optional): Procesador de síntesis de voz
            lead_repo (LeadRepository, optional): Repositorio para guardar datos de leads
            conversation_repo (ConversationRepository, optional): Repositorio para guardar conversaciones
        """
        self.llm = llm
        self.asr = asr
        self.tts = tts
        self.lead_repo = lead_repo or LeadRepository()
        self.conversation_repo = conversation_repo or ConversationRepository()
        
        # Diccionario de conversaciones activas: id -> orquestador
        self.active_conversations = {}
        
        # Directorio para archivos de audio temporales
        self.audio_dir = os.path.join(tempfile.gettempdir(), "leadbot_audio")
        os.makedirs(self.audio_dir, exist_ok=True)
    
    def start_conversation(self, lead_id: Optional[str] = None) -> str:
        """
        Inicia una nueva conversación.
        
        Args:
            lead_id (str, optional): ID del lead si ya existe
            
        Returns:
            str: ID de la conversación
        """
        # Crear nueva conversación en el modelo
        conversation = Conversation(lead_id=lead_id)
        conversation_id = conversation.id
        
        # Mensaje de bienvenida
        welcome_message = "¡Hola! Soy LeadBot, tu asistente virtual. Estoy aquí para conocer más sobre ti y tus necesidades. ¿Podrías comenzar diciéndome tu nombre?"
        conversation.add_message("assistant", welcome_message)
        
        # Obtener contexto del lead si existe
        initial_context = {}
        if lead_id:
            lead = self.lead_repo.get_lead(lead_id)
            if lead:
                initial_context = lead.to_dict()
        
        # Crear orquestador para esta conversación
        orchestrator = ConversationOrchestrator(self.llm, initial_context)
        self.active_conversations[conversation_id] = {
            "orchestrator": orchestrator,
            "conversation": conversation
        }
        
        # Guardar conversación en BD
        self.conversation_repo.save_conversation(conversation)
        
        # Generar audio para el mensaje de bienvenida si hay TTS
        audio_response = None
        if self.tts:
            try:
                audio_response = self.tts.synthesize(welcome_message)
                # Guardar archivo de audio
                self._save_audio_file(audio_response, conversation_id, "assistant")
            except Exception as e:
                logger.error(f"Error al generar audio: {str(e)}")
        
        logger.info(f"Nueva conversación iniciada: {conversation_id}")
        return conversation_id
    
    def process_text_message(self, conversation_id: str, text: str) -> Dict[str, Any]:
        """
        Procesa un mensaje de texto del usuario.
        
        Args:
            conversation_id (str): ID de la conversación
            text (str): Mensaje de texto del usuario
            
        Returns:
            Dict[str, Any]: Respuesta y metadatos
        """
        if conversation_id not in self.active_conversations:
            # Intentar cargar la conversación desde el repositorio
            conversation = self.conversation_repo.get_conversation(conversation_id)
            if not conversation:
                raise ValueError(f"Conversación no encontrada: {conversation_id}")
            
            # Recrear el orquestador
            initial_context = {}
            if conversation.lead_id:
                lead = self.lead_repo.get_lead(conversation.lead_id)
                if lead:
                    initial_context = lead.to_dict()
            
            orchestrator = ConversationOrchestrator(self.llm, initial_context)
            
            # Recuperar historial de mensajes para el contexto
            for msg in conversation.messages:
                if msg.role == "user":
                    orchestrator.process_message(msg.content)
            
            self.active_conversations[conversation_id] = {
                "orchestrator": orchestrator,
                "conversation": conversation
            }
        
        # Obtener datos de la conversación
        conversation_data = self.active_conversations[conversation_id]
        orchestrator = conversation_data["orchestrator"]
        conversation = conversation_data["conversation"]
        
        # Registrar mensaje del usuario
        conversation.add_message("user", text)
        
        # Procesar mensaje con el orquestador
        result = orchestrator.process_message(text)
        
        # Registrar respuesta del asistente
        conversation.add_message("assistant", result["response"])
        
        # Actualizar información extraída del lead en la conversación
        if result.get("lead_info"):
            conversation.lead_info_extracted.update(result.get("lead_info", {}))
        
        # Guardar o actualizar información del lead
        lead_id = conversation.lead_id
        if self.lead_repo and result.get("lead_info"):
            if lead_id:
                # Actualizar lead existente
                self.lead_repo.update_lead(lead_id, result["lead_info"])
                # Actualizar etapa de conversación
                if result.get("stage"):
                    self.lead_repo.update_lead(lead_id, {"conversation_stage": result["stage"]})
            else:
                # Crear nuevo lead
                lead = Lead()
                lead.update(result["lead_info"])
                lead.conversation_stage = result.get("stage", "introduccion")
                
                # Guardar lead
                lead_id = self.lead_repo.save_lead(lead)
                
                # Actualizar referencia en la conversación
                conversation.lead_id = lead_id
        
        # Generar audio si hay TTS disponible
        audio_response = None
        if self.tts:
            try:
                audio_response = self.tts.synthesize(result["response"])
                # Guardar archivo de audio
                audio_path = self._save_audio_file(audio_response, conversation_id, "assistant")
            except Exception as e:
                logger.error(f"Error al generar audio: {str(e)}")
        
        # Verificar si la conversación ha terminado
        if result.get("conversation_ended", False):
            logger.info(f"Conversación {conversation_id} finalizada por el orquestador")
            # Generar resumen y finalizar
            self.end_conversation(conversation_id)
        
        # Guardar conversación actualizada
        self.conversation_repo.save_conversation(conversation)
        
        return {
            "conversation_id": conversation_id,
            "user_message": text,
            "assistant_response": result["response"],
            "audio_response": audio_response,
            "lead_info": result.get("lead_info"),
            "stage": result.get("stage"),
            "lead_id": lead_id,
            "conversation_ending": result.get("conversation_ending", False),
            "conversation_ended": result.get("conversation_ended", False)
        }

    def _finalize_conversation(self, conversation, conversation_id: str) -> None:
        """
        Finaliza una conversación, genera un resumen y actualiza el estado.
        
        Args:
            conversation: Objeto de conversación
            conversation_id (str): ID de la conversación
        """
        # Marcar como finalizada
        conversation.end_conversation()
        
        # Generar resumen
        try:
            # Construir contexto para el resumen
            conversation_text = "\n".join([f"{msg.role}: {msg.content}" for msg in conversation.messages])
            
            # Prompt mejorado para generar resumen más estructurado
            prompt = f"""
            Por favor, genera un resumen estructurado de la siguiente conversación entre un asistente y un usuario.
            
            Incluye:
            1. Puntos clave identificados
            2. Información del lead (nombre, empresa, cargo si se mencionó)
            3. Necesidades específicas identificadas
            4. Puntos de dolor mencionados
            5. Información sobre presupuesto o plazos si se mencionaron
            6. Objeciones o preocupaciones expresadas
            7. Siguiente paso acordado
            
            Formato el resumen en secciones claras para facilitar su lectura.
            
            Conversación:
            {conversation_text}
            
            Resumen:
            """
            
            # Generar resumen
            summary = self.llm.generate(prompt)
            conversation.summary = summary
            logger.info(f"Resumen generado para conversación {conversation_id}")
        except Exception as e:
            logger.error(f"Error al generar resumen: {str(e)}")
            conversation.summary = "Error al generar resumen automático."
        
        # Eliminar de conversaciones activas
        if conversation_id in self.active_conversations:
            del self.active_conversations[conversation_id]

    
    def process_audio_message(self, conversation_id: str, audio_data: bytes) -> Dict[str, Any]:
        """
        Procesa un mensaje de audio del usuario.
        
        Args:
            conversation_id (str): ID de la conversación
            audio_data (bytes): Datos de audio del mensaje del usuario
            
        Returns:
            Dict[str, Any]: Respuesta y metadatos
        """
        if not self.asr:
            raise ValueError("No hay procesador ASR configurado")
        
        # Guardar archivo de audio del usuario
        audio_path = self._save_audio_file(audio_data, conversation_id, "user")
        
        # Transcribir audio a texto
        transcription = self.asr.transcribe(audio_data)
        
        if not transcription.get("success"):
            return {
                "conversation_id": conversation_id,
                "error": "Error en la transcripción del audio",
                "details": transcription.get("error")
            }
        
        # Obtener texto transcrito
        text = transcription["text"]
        
        # Obtener la conversación
        if conversation_id in self.active_conversations:
            conversation = self.active_conversations[conversation_id]["conversation"]
        else:
            conversation = self.conversation_repo.get_conversation(conversation_id)
            if not conversation:
                raise ValueError(f"Conversación no encontrada: {conversation_id}")
        
        # Registrar mensaje de audio con su transcripción
        conversation.add_message("user", text, audio_path, text)
        
        # Procesar el texto transcrito
        result = self.process_text_message(conversation_id, text)
        
        # Añadir información de transcripción
        result["transcription"] = transcription
        
        return result
    
    def end_conversation(self, conversation_id: str) -> bool:
        """
        Finaliza una conversación.
        
        Args:
            conversation_id (str): ID de la conversación
            
        Returns:
            bool: True si la conversación se finalizó correctamente
        """
        if conversation_id not in self.active_conversations:
            # Intentar cargar del repositorio
            conversation = self.conversation_repo.get_conversation(conversation_id)
            if not conversation:
                return False
        else:
            conversation = self.active_conversations[conversation_id]["conversation"]
        
        # Marcar como finalizada
        conversation.end_conversation()
        
        # Generar resumen si se desea
        if self.llm:
            try:
                # Construir contexto para el resumen
                conversation_text = "\n".join([f"{msg.role}: {msg.content}" for msg in conversation.messages])
                
                # Prompt para generar resumen
                prompt = f"""
                Por favor, genera un resumen estructurado de la siguiente conversación entre un asistente y un usuario.
                
                Incluye:
                1. Puntos clave identificados
                2. Información del lead (nombre, empresa, cargo si se mencionó)
                3. Necesidades específicas identificadas
                4. Puntos de dolor mencionados
                5. Información sobre presupuesto o plazos si se mencionaron
                6. Objeciones o preocupaciones expresadas
                7. Siguiente paso acordado
                
                Formato el resumen en secciones claras para facilitar su lectura.
                
                Conversación:
                {conversation_text}
                
                Resumen:
                """
                
                # Generar resumen
                summary = self.llm.generate(prompt)
                conversation.summary = summary
            except Exception as e:
                logger.error(f"Error al generar resumen: {str(e)}")
        
        # Guardar conversación actualizada
        self.conversation_repo.save_conversation(conversation)
        
        # Eliminar de conversaciones activas
        if conversation_id in self.active_conversations:
            del self.active_conversations[conversation_id]
        
        logger.info(f"Conversación finalizada: {conversation_id}")
        return True
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de mensajes de una conversación.
        
        Args:
            conversation_id (str): ID de la conversación
            
        Returns:
            List[Dict[str, Any]]: Lista de mensajes
        """
        if conversation_id in self.active_conversations:
            conversation = self.active_conversations[conversation_id]["conversation"]
        else:
            conversation = self.conversation_repo.get_conversation(conversation_id)
            if not conversation:
                return []
        
        return [msg.to_dict() for msg in conversation.messages]
    
    def get_lead_info(self, conversation_id: str) -> Dict[str, Any]:
        """
        Obtiene la información extraída del lead en una conversación.
        
        Args:
            conversation_id (str): ID de la conversación
            
        Returns:
            Dict[str, Any]: Información del lead
        """
        # Primero intentar obtener de la conversación activa
        if conversation_id in self.active_conversations:
            conversation = self.active_conversations[conversation_id]["conversation"]
        else:
            conversation = self.conversation_repo.get_conversation(conversation_id)
            if not conversation:
                return {}
        
        # Si la conversación tiene lead_id, obtener información completa
        if conversation.lead_id:
            lead = self.lead_repo.get_lead(conversation.lead_id)
            if lead:
                return lead.to_dict()
        
        # Si no, devolver la información extraída en la conversación
        return conversation.lead_info_extracted
    
    def _save_audio_file(self, audio_data: bytes, conversation_id: str, role: str) -> str:
        """
        Guarda un archivo de audio en disco.
        
        Args:
            audio_data (bytes): Datos de audio
            conversation_id (str): ID de la conversación
            role (str): Rol del mensaje ('user' o 'assistant')
            
        Returns:
            str: Ruta al archivo guardado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{conversation_id}_{role}_{timestamp}.wav"
        filepath = os.path.join(self.audio_dir, filename)
        
        with open(filepath, "wb") as f:
            f.write(audio_data)
            
        return filepath