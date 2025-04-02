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
    Conversation manager for managing conversations with users.
    This class handles the orchestration of conversations, including text and audio processing, and saving conversation data.
    """
    
    def __init__(self, 
                 llm: BaseLLM, 
                 asr: Optional[WhisperASR] = None,
                 tts: Optional[TTSProcessor] = None,
                 lead_repo: Optional[LeadRepository] = None,
                 conversation_repo: Optional[ConversationRepository] = None):
        """
        Initializes the conversation manager.

        Args:
            llm (BaseLLM): The language model used for generating responses.
            asr (WhisperASR, optional): The Automatic Speech Recognition (ASR) processor.
            tts (TTSProcessor, optional): The Text-to-Speech (TTS) processor.
            lead_repo (LeadRepository, optional): Repository for storing lead data.
            conversation_repo (ConversationRepository, optional): Repository for storing conversation data.
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
        Starts a new conversation.

        This method initializes a new conversation, optionally linking it to an existing lead. 
        It also sets up the conversation orchestrator and saves the conversation to the database.

        Args:
            lead_id (str, optional): The ID of an existing lead, if available.

        Returns:
            str: The ID of the newly created conversation.
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
        Processes a text message from the user.

        This method processes a user's text message, generates a response using the orchestrator, 
        and updates the conversation state. It also saves or updates lead information in the database.

        Args:
            conversation_id (str): The ID of the conversation.
            text (str): The user's text message.

        Returns:
            Dict[str, Any]: A dictionary containing:
                - **conversation_id** (str): The ID of the conversation.
                - **user_message** (str): The user's original message.
                - **assistant_response** (str): The assistant's response message.
                - **audio_response** (bytes, optional): The audio version of the assistant's response (if TTS is enabled).
                - **lead_info** (dict, optional): Updated lead information extracted from the conversation.
                - **stage** (str, optional): The current stage of the conversation.
                - **lead_id** (str, optional): The ID of the associated lead.
                - **conversation_ending** (bool): Whether the conversation is nearing its end.
                - **conversation_ended** (bool): Whether the conversation has ended.
        """
        if conversation_id not in self.active_conversations:
            # Intentar cargar la conversación desde el repositorio
            conversation = self.conversation_repo.get_conversation(conversation_id)
            if not conversation:
                raise ValueError(f"Conversación no encontrada: {conversation_id}")
            
            initial_context = {}
            if conversation.lead_id:
                lead = self.lead_repo.get_lead(conversation.lead_id)
                if lead:
                    initial_context = lead.to_dict()
            
            orchestrator = ConversationOrchestrator(self.llm, initial_context)
            
            for msg in conversation.messages:
                if msg.role == "user":
                    orchestrator.process_message(msg.content)
            
            self.active_conversations[conversation_id] = {
                "orchestrator": orchestrator,
                "conversation": conversation
            }
        
        conversation_data = self.active_conversations[conversation_id]
        orchestrator = conversation_data["orchestrator"]
        conversation = conversation_data["conversation"]
        
        conversation.add_message("user", text)
        
        result = orchestrator.process_message(text)
        
        conversation.add_message("assistant", result["response"])
        
        if result.get("lead_info"):
            conversation.lead_info_extracted.update(result.get("lead_info", {}))
        
        lead_id = conversation.lead_id
        if self.lead_repo and result.get("lead_info"):
            if lead_id:
                self.lead_repo.update_lead(lead_id, result["lead_info"])
                if result.get("stage"):
                    self.lead_repo.update_lead(lead_id, {"conversation_stage": result["stage"]})
            else:
                lead = Lead()
                lead.update(result["lead_info"])
                lead.conversation_stage = result.get("stage", "introduccion")
                
                lead_id = self.lead_repo.save_lead(lead)
                
                conversation.lead_id = lead_id
        
        audio_response = None
        if self.tts:
            try:
                audio_response = self.tts.synthesize(result["response"])
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


    def process_audio_message(self, conversation_id: str, audio_data: bytes) -> Dict[str, Any]:
        """
        Processes an audio message from the user.

        This method handles the transcription of an audio message using the ASR (Automatic Speech Recognition) system.
        It updates the conversation state and processes the transcribed text as a regular text message.

        Args:
            conversation_id (str): The ID of the conversation.
            audio_data (bytes): The audio data of the user's message.

        Returns:
            Dict[str, Any]: A dictionary containing:
                - **conversation_id** (str): The ID of the conversation.
                - **transcription** (dict): The transcription result, including the transcribed text and metadata.
                - **assistant_response** (str): The assistant's response message.
                - **audio_response** (bytes, optional): The audio version of the assistant's response (if TTS is enabled).
                - **lead_info** (dict, optional): Updated lead information extracted from the conversation.
                - **stage** (str, optional): The current stage of the conversation.
                - **lead_id** (str, optional): The ID of the associated lead.
                - **conversation_ending** (bool): Whether the conversation is nearing its end.
                - **conversation_ended** (bool): Whether the conversation has ended.

        Raises:
            ValueError: If no ASR processor is configured.
        """
        if not self.asr:
            raise ValueError("No hay procesador ASR configurado")
        
        audio_path = self._save_audio_file(audio_data, conversation_id, "user")
        
        transcription = self.asr.transcribe(audio_data)
        
        if not transcription.get("success"):
            return {
                "conversation_id": conversation_id,
                "error": "Error en la transcripción del audio",
                "details": transcription.get("error")
            }
        
        text = transcription["text"]
        
        if conversation_id in self.active_conversations:
            conversation = self.active_conversations[conversation_id]["conversation"]
        else:
            conversation = self.conversation_repo.get_conversation(conversation_id)
            if not conversation:
                raise ValueError(f"Conversación no encontrada: {conversation_id}")
        
        conversation.add_message("user", text, audio_path, text)
        
        result = self.process_text_message(conversation_id, text)
        
        result["transcription"] = transcription
        
        return result
    
    def end_conversation(self, conversation_id: str) -> bool:
        """
        Ends a conversation.

        This method finalizes a conversation by marking it as ended, generating a structured summary 
        using the language model (if available), and saving the updated conversation to the database. 
        It also removes the conversation from the list of active conversations.

        Args:
            conversation_id (str): The ID of the conversation to be ended.

        Returns:
            bool: `True` if the conversation was successfully finalized, `False` otherwise.
        """
        if conversation_id not in self.active_conversations:
            # Intentar cargar del repositorio
            conversation = self.conversation_repo.get_conversation(conversation_id)
            if not conversation:
                return False
        else:
            conversation = self.active_conversations[conversation_id]["conversation"]
        
        conversation.end_conversation()
        
        if self.llm:
            try:
                conversation_text = "\n".join([f"{msg.role}: {msg.content}" for msg in conversation.messages])
                
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
                
                summary = self.llm.generate(prompt)
                conversation.summary = summary
            except Exception as e:
                logger.error(f"Error al generar resumen: {str(e)}")
        
        self.conversation_repo.save_conversation(conversation)
        
        if conversation_id in self.active_conversations:
            del self.active_conversations[conversation_id]
        
        logger.info(f"Conversación finalizada: {conversation_id}")
        return True
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves the message history of a conversation.

        This method fetches all messages exchanged in a conversation, including both user and assistant messages.

        Args:
            conversation_id (str): The ID of the conversation.

        Returns:
            List[Dict[str, Any]]: A list of messages, where each message is represented as a dictionary containing:
                - **role** (str): The role of the sender (e.g., "user" or "assistant").
                - **content** (str): The content of the message.
                - **timestamp** (datetime): The timestamp of when the message was sent.
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
            Retrieves the extracted lead information from a conversation.

            This method fetches the lead information associated with a conversation, either from the active conversation
            or from the database. If no lead is associated, it returns the extracted lead information from the conversation.

            Args:
                conversation_id (str): The ID of the conversation.

            Returns:
                Dict[str, Any]: A dictionary containing the lead information, including:
                    - **name** (str, optional): The name of the lead.
                    - **company** (str, optional): The company of the lead.
                    - **position** (str, optional): The position or role of the lead.
                    - **contact_info** (dict, optional): Contact details such as email or phone number.
                    - **other_details** (dict, optional): Any additional information extracted during the conversation.
            """
        if conversation_id in self.active_conversations:
            conversation = self.active_conversations[conversation_id]["conversation"]
        else:
            conversation = self.conversation_repo.get_conversation(conversation_id)
            if not conversation:
                return {}
        
        if conversation.lead_id:
            lead = self.lead_repo.get_lead(conversation.lead_id)
            if lead:
                return lead.to_dict()
        
        return conversation.lead_info_extracted
    
    def _save_audio_file(self, audio_data: bytes, conversation_id: str, role: str) -> str:
        """
        Saves an audio file to disk.

        This method saves the provided audio data to a file on disk, associating it with a specific conversation 
        and role (e.g., "user" or "assistant"). The file is stored in a temporary directory.

        Args:
            audio_data (bytes): The audio data to be saved.
            conversation_id (str): The ID of the conversation associated with the audio file.
            role (str): The role of the message (e.g., "user" or "assistant").

        Returns:
            str: The file path of the saved audio file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{conversation_id}_{role}_{timestamp}.wav"
        filepath = os.path.join(self.audio_dir, filename)
        
        with open(filepath, "wb") as f:
            f.write(audio_data)
            
        return filepath