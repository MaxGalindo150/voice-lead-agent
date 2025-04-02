# scripts/test_conversation_storage.py
import os
import sys
import logging

# Asegurar que podemos importar desde el directorio raíz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.llm.factory import create_llm
from app.core.conversation import ConversationManager
from app.db.repository import LeadRepository, ConversationRepository

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Prueba completa del flujo de conversación y almacenamiento."""
    
    # Inicializar repositorios
    lead_repo = LeadRepository()
    conversation_repo = ConversationRepository()
    
    # Crear LLM
    llm = create_llm("openai")  # o el modelo que estés usando
    
    # Inicializar ConversationManager
    conversation_manager = ConversationManager(
        llm=llm,
        lead_repo=lead_repo,
        conversation_repo=conversation_repo
    )
    
    # Iniciar una nueva conversación
    conversation_id = conversation_manager.start_conversation()
    logger.info(f"Conversación iniciada: {conversation_id}")
    
    # Simular intercambio de mensajes
    messages = [
        "Hola, me llamo Juan Pérez y trabajo en Empresa XYZ",
        "Soy el director de tecnología",
        "Estamos buscando una solución para automatizar nuestro proceso de atención al cliente",
        "Nuestro presupuesto es de aproximadamente 50.000 euros",
        "Necesitamos implementarlo en los próximos 3 meses",
        "Nuestro principal problema es que actualmente todo se hace manualmente y es muy ineficiente",
        "Me interesa saber más sobre vuestro chatbot con IA"
    ]
    
    # Procesar cada mensaje
    for message in messages:
        logger.info(f"Enviando mensaje: {message}")
        response = conversation_manager.process_text_message(conversation_id, message)
        logger.info(f"Respuesta: {response['assistant_response']}")
        
        if response.get("lead_info"):
            logger.info(f"Información extraída: {response['lead_info']}")
    
    # Obtener lead_id de la conversación
    lead_info = conversation_manager.get_lead_info(conversation_id)
    lead_id = lead_info.get("id")
    
    if lead_id:
        # Obtener lead completo
        lead = lead_repo.get_lead(lead_id)
        logger.info(f"Lead guardado: {lead.to_dict()}")
        
        # Obtener todas las conversaciones del lead
        conversations = conversation_repo.get_conversations_by_lead(lead_id)
        logger.info(f"Número de conversaciones del lead: {len(conversations)}")
    
    # Finalizar conversación
    conversation_manager.end_conversation(conversation_id)
    logger.info("Conversación finalizada")
    
    # Obtener historial completo
    conversation = conversation_repo.get_conversation(conversation_id)
    if conversation:
        logger.info(f"Conversación recuperada: {conversation.id}")
        logger.info(f"Número de mensajes: {len(conversation.messages)}")
        logger.info(f"Resumen: {conversation.summary}")
    
    # Verificar que podemos iniciar una nueva conversación con el mismo lead
    if lead_id:
        new_conversation_id = conversation_manager.start_conversation(lead_id)
        logger.info(f"Nueva conversación iniciada con lead existente: {new_conversation_id}")
        
        # Enviar un mensaje adicional
        response = conversation_manager.process_text_message(
            new_conversation_id, 
            "Hola de nuevo, he estado pensando en lo que hablamos y me gustaría programar una demo"
        )
        logger.info(f"Respuesta: {response['assistant_response']}")
        
        # Finalizar la segunda conversación
        conversation_manager.end_conversation(new_conversation_id)
        
        # Verificar que ahora hay dos conversaciones
        conversations = conversation_repo.get_conversations_by_lead(lead_id)
        logger.info(f"Número de conversaciones del lead después de la segunda: {len(conversations)}")

if __name__ == "__main__":
    main()