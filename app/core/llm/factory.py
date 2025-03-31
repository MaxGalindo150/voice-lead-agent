import logging
from typing import Optional

from app.core.llm.base import BaseLLM
from app.core.llm.openai_llm import OpenAILLM
from app import config

# Configurar logger
logger = logging.getLogger(__name__)

def create_llm(llm_type: Optional[str] = None) -> BaseLLM:
    """
    Crea una instancia del LLM especificado.
    
    Args:
        llm_type (str, optional): Tipo de LLM a crear. Valores válidos: 'openai', 'mistral', 'auto'.
                                Si es None, se usa el valor de config.LLM_MODE.
    
    Returns:
        BaseLLM: Instancia de LLM inicializada.
        
    Raises:
        ValueError: Si el tipo de LLM no es reconocido.
        Exception: Si ocurre un error en la inicialización.
    """
    # Si no se proporciona tipo, usar el de la configuración
    llm_type = llm_type or config.LLM_MODE
    
    if llm_type == "openai":
        logger.info("Inicializando LLM de OpenAI")
        return OpenAILLM(
            api_key=config.OPENAI_API_KEY,
            model=config.OPENAI_MODEL,
            temperature=config.OPENAI_TEMPERATURE
        )
    
    elif llm_type == "mistral":
        logger.info("Inicializando LLM de Mistral (local)")
        # Importación dinámica para evitar error si no está instalado
        try:
            from app.core.llm.mistral_llm import MistralLLM
            return MistralLLM(
                model_path=config.MISTRAL_MODEL_PATH,
                gpu_layers=config.MISTRAL_GPU_LAYERS
            )
        except ImportError:
            logger.error("Módulo Mistral no disponible. Instala las dependencias necesarias.")
            raise ImportError("No se pudo importar MistralLLM. Asegúrate de tener ctransformers instalado.")
    
    elif llm_type == "auto":
        logger.info("Modo automático: intentando Mistral primero, fallback a OpenAI")
        # Intentar con Mistral primero
        try:
            from app.core.llm.mistral_llm import MistralLLM
            
            logger.info("Inicializando Mistral...")
            mistral = MistralLLM(
                model_path=config.MISTRAL_MODEL_PATH,
                gpu_layers=config.MISTRAL_GPU_LAYERS
            )
            
            # Verificar que funciona con una prueba simple
            logger.info("Verificando funcionalidad de Mistral...")
            test_result = mistral.generate("Hola, prueba de inicialización.")
            
            if test_result:
                logger.info("Mistral inicializado correctamente")
                return mistral
            else:
                logger.warning("Mistral inicializado pero devolvió respuesta vacía. Usando OpenAI como fallback.")
                return OpenAILLM(
                    api_key=config.OPENAI_API_KEY,
                    model=config.OPENAI_MODEL,
                    temperature=config.OPENAI_TEMPERATURE
                )
                
        except (ImportError, Exception) as e:
            logger.warning(f"No se pudo inicializar Mistral: {str(e)}. Usando OpenAI como fallback.")
            return OpenAILLM(
                api_key=config.OPENAI_API_KEY,
                model=config.OPENAI_MODEL,
                temperature=config.OPENAI_TEMPERATURE
            )
    
    else:
        logger.error(f"Tipo de LLM desconocido: {llm_type}")
        raise ValueError(f"Tipo de LLM desconocido: {llm_type}. " 
                         f"Valores válidos: 'openai', 'mistral', 'auto'")