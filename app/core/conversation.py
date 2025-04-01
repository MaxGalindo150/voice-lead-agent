# core/conversation.py
import uuid
import datetime
import logging
from typing import Dict, Any, Optional, List

from app.core.asr import WhisperASR
from app.core.tts import TTSProcessor
from app.core.langchain_integration import ConversationOrchestrator
from app.core.llm.base import BaseLLM
from app.db.repository import LeadRepository

logger = logging.getLogger(__name__)

class ConversationManager:
    """
    Administrador de conversaciones que integra ASR, LLM y TTS.
    """
    
    def __init__(self, 
                 llm: BaseLLM, 
                 asr: Optional[WhisperASR] = None,
                 tts: Optional[TTSProcessor] = None,
                 lead_repo: Optional[LeadRepository] = None):
        """
        Inicializa el administrador de conversaciones.
        
        Args:
            llm (BaseLLM): Modelo de lenguaje
            asr (WhisperASR, optional): Procesador de reconocimiento de voz
            tts (TTSProcessor, optional): Procesador de síntesis de voz
            lead_repo (LeadRepository, optional): Repositorio para guardar datos de leads
        """
        self.llm = llm
        self.asr = asr
        self.tts = tts
        self.lead_repo = lead_repo
        
        # Diccionario de conversaciones activas: id -> orquestador
        self.active_conversations = {}
    
    def start_conversation(self, lead_id: Optional[str] = None) -> str:
        """
        Inicia una nueva conversación.
        
        Args:
            lead_id (str, optional): ID del lead si ya existe
            
        Returns:
            str: ID de la conversación
        """
        conversation_id = str(uuid.uuid4())
        
        # Si hay un lead existente, obtener su información
        initial_context = {}
        if lead_id and self.lead_repo:
            lead = self.lead_repo.get_lead(lead_id)
            if lead:
                initial_context = lead.to_dict()
        
        # Crear orquestador para esta conversación
        orchestrator = ConversationOrchestrator(self.llm, initial_context)
        self.active_conversations[conversation_id] = orchestrator
        
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
            raise ValueError(f"Conversación no encontrada: {conversation_id}")
        
        # Obtener orquestador
        orchestrator = self.active_conversations[conversation_id]
        
        # Procesar mensaje
        result = orchestrator.process_message(text)
        
        # Guardar o actualizar información del lead
        lead_id = None
        if self.lead_repo and result.get("lead_info"):
            lead_data = result["lead_info"].copy()
            # Añadir metadatos
            lead_data["last_interaction"] = datetime.datetime.now().isoformat()
            lead_data["conversation_stage"] = result["stage"]
            
            # Guardar en el repositorio
            lead_id = self.lead_repo.create_or_update_lead(lead_data)
        
        # Generar audio si hay TTS disponible
        audio_response = None
        if self.tts:
            try:
                audio_response = self.tts.synthesize(result["response"])
            except Exception as e:
                logger.error(f"Error al generar audio: {str(e)}")
        
        return {
            "conversation_id": conversation_id,
            "user_message": text,
            "assistant_response": result["response"],
            "audio_response": audio_response,
            "lead_info": result.get("lead_info"),
            "stage": result.get("stage"),
            "lead_id": lead_id
        }
    
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
        
        # Transcribir audio a texto
        transcription = self.asr.transcribe(audio_data)
        
        if not transcription.get("success"):
            return {
                "conversation_id": conversation_id,
                "error": "Error en la transcripción del audio",
                "details": transcription.get("error")
            }
        
        # Procesar el texto transcrito
        text = transcription["text"]
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
            return False
        
        # Aquí podrías realizar acciones finales
        # como guardar un resumen de la conversación
        
        # Eliminar la conversación
        del self.active_conversations[conversation_id]
        logger.info(f"Conversación finalizada: {conversation_id}")
        
        return True