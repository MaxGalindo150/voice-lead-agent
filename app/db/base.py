# app/db/base.py
import sqlite3
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class Database:
    """Base class for interacting with the SQLite database."""
    
    def __init__(self, db_path: str = 'leads.db'):
        """
        Initializes the database connection.
        
        Args:
            db_path: Path to the database file
        """
        try:
            # Ensure the directory exists
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
                
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            
            # Initialize tables
            self._init_tables()
            
            logger.info(f"Database initialized at {db_path}")
            
        except Exception as e:
            logger.error(f"Error initializing the database: {str(e)}")
            raise
    
    def _init_tables(self) -> None:
        """Inicializa las tablas necesarias en la base de datos."""
        try:
            # Tabla de leads
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS leads (
                    id TEXT PRIMARY KEY,
                    nombre TEXT,
                    empresa TEXT,
                    cargo TEXT,
                    email TEXT,
                    telefono TEXT,
                    necesidades TEXT,
                    presupuesto TEXT,
                    plazo TEXT,
                    punto_dolor TEXT,
                    producto_interes TEXT,
                    conversation_stage TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    conversation_ids TEXT
                )
            ''')
            
            # Tabla de conversaciones
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    lead_id TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    ended_at TEXT,
                    summary TEXT,
                    lead_info_extracted TEXT,
                    FOREIGN KEY (lead_id) REFERENCES leads (id)
                )
            ''')
            
            # Tabla de mensajes
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT,
                    role TEXT,
                    content TEXT,
                    timestamp TEXT,
                    audio_file_path TEXT,
                    transcription TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                )
            ''')
            
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"Error al inicializar tablas: {str(e)}")
            self.conn.rollback()
            raise