import logging
from typing import Optional

from app.core.llm.base import BaseLLM
from app.core.llm.openai_llm import OpenAILLM
from app import config

# Configure logger
logger = logging.getLogger(__name__)

def create_llm(llm_type: Optional[str] = None) -> BaseLLM:
    """
    Creates an instance of the specified LLM.
    
    Args:
        llm_type (str, optional): Type of LLM to create. Valid values: 'openai', 'mistral', 'auto'.
                                If None, the value from config.LLM_MODE is used.
    
    Returns:
        BaseLLM: Initialized LLM instance.
        
    Raises:
        ValueError: If the LLM type is not recognized.
        Exception: If an error occurs during initialization.
    """
    # If no type is provided, use the one from configuration
    llm_type = llm_type or config.LLM_MODE
    
    if llm_type == "openai":
        logger.info("Initializing OpenAI LLM")
        return OpenAILLM(
            api_key=config.OPENAI_API_KEY,
            model=config.OPENAI_MODEL,
            temperature=config.OPENAI_TEMPERATURE
        )
    
    elif llm_type == "mistral":
        logger.info("Initializing Mistral LLM (local)")
        # Dynamic import to avoid error if not installed
        try:
            from app.core.llm.mistral_llm import MistralLLM
            return MistralLLM(
                model_path=config.MISTRAL_MODEL_PATH,
                gpu_layers=config.MISTRAL_GPU_LAYERS
            )
        except ImportError:
            logger.error("Mistral module not available. Install the necessary dependencies.")
            raise ImportError("Could not import MistralLLM. Make sure you have ctransformers installed.")
    
    elif llm_type == "auto":
        logger.info("Automatic mode: trying Mistral first, fallback to OpenAI")
        # Try Mistral first
        try:
            from app.core.llm.mistral_llm import MistralLLM
            
            logger.info("Initializing Mistral...")
            mistral = MistralLLM(
                model_path=config.MISTRAL_MODEL_PATH,
                gpu_layers=config.MISTRAL_GPU_LAYERS
            )
            
            # Verify that it works with a simple test
            logger.info("Verifying Mistral functionality...")
            test_result = mistral.generate("Hello, initialization test.")
            
            if test_result:
                logger.info("Mistral initialized correctly")
                return mistral
            else:
                logger.warning("Mistral initialized but returned empty response. Using OpenAI as fallback.")
                return OpenAILLM(
                    api_key=config.OPENAI_API_KEY,
                    model=config.OPENAI_MODEL,
                    temperature=config.OPENAI_TEMPERATURE
                )
                
        except (ImportError, Exception) as e:
            logger.warning(f"Could not initialize Mistral: {str(e)}. Using OpenAI as fallback.")
            return OpenAILLM(
                api_key=config.OPENAI_API_KEY,
                model=config.OPENAI_MODEL,
                temperature=config.OPENAI_TEMPERATURE
            )
    
    else:
        logger.error(f"Unknown LLM type: {llm_type}")
        raise ValueError(f"Unknown LLM type: {llm_type}. " 
                         f"Valid values: 'openai', 'mistral', 'auto'")