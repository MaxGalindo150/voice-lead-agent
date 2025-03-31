import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Base directory of the project (2 levels above this file)
BASE_DIR = Path(__file__).resolve().parent.parent

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = os.getenv("LOG_FILE", str(BASE_DIR / "logs" / "app.log"))

# Ensure the logs directory exists
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Data directories configuration
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = DATA_DIR / "models"
CONVERSATIONS_DIR = DATA_DIR / "conversations"

# Ensure the data directories exist
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(CONVERSATIONS_DIR, exist_ok=True)

# LLM configuration
LLM_MODE = os.getenv("LLM_MODE", "auto")  # 'openai', 'mistral', 'auto'

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))

# Mistral configuration
MISTRAL_MODEL_PATH = os.getenv(
    "MISTRAL_MODEL_PATH", 
    str(MODELS_DIR / "mistral-7b-instruct-v0.2.Q4_K_M.gguf")
)
MISTRAL_GPU_LAYERS = int(os.getenv("MISTRAL_GPU_LAYERS", "50"))

# ASR (Whisper) configuration
ASR_MODEL_SIZE = os.getenv("ASR_MODEL_SIZE", "base")  # 'tiny', 'base', 'small', 'medium', 'large'
ASR_LANGUAGE = os.getenv("ASR_LANGUAGE", "es")

# TTS (Text-to-Speech) configuration
TTS_LANGUAGE = os.getenv("TTS_LANGUAGE", "es")
TTS_SLOW = os.getenv("TTS_SLOW", "False").lower() == "true"

# Database configuration
DB_TYPE = os.getenv("DB_TYPE", "sqlite")
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", str(DATA_DIR / "leads.sqlite"))

# CRM Mock configuration
CRM_MOCK_DATA_PATH = os.getenv("CRM_MOCK_DATA_PATH", str(DATA_DIR / "crm_mock.json"))

# Application configuration
APP_NAME = os.getenv("APP_NAME", "Voice Lead Agent")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"


# Initialize logging
def setup_logging():
    """Configures the logging system."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )
    
    # Reduce verbosity of some libraries
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    

# Debugging information
def print_config_info():
    """Prints configuration information for debugging."""
    if DEBUG_MODE:
        print(f"== {APP_NAME} v{APP_VERSION} ==")
        print(f"Base Dir: {BASE_DIR}")
        print(f"LLM Mode: {LLM_MODE}")
        print(f"ASR Model: {ASR_MODEL_SIZE} ({ASR_LANGUAGE})")
        print(f"DB Type: {DB_TYPE}")
        print(f"Debug Mode: {DEBUG_MODE}")
        if LLM_MODE in ["openai", "auto"]:
            print(f"OpenAI Model: {OPENAI_MODEL} (API Key: {'Configured' if OPENAI_API_KEY else 'Not configured'})")
        if LLM_MODE in ["mistral", "auto"]:
            print(f"Mistral Model: {MISTRAL_MODEL_PATH} (Exists: {os.path.exists(MISTRAL_MODEL_PATH)})")