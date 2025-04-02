# app/models/conversation.py
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import uuid


@dataclass
class Message:
    """Modelo para representar un mensaje en una conversación."""
    
    role: str  # 'user' o 'assistant'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Para mensajes de audio
    audio_file_path: Optional[str] = None
    transcription: Optional[str] = None
    
    # ID generado por la base de datos
    id: Optional[int] = None
    conversation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el mensaje a un diccionario."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Crea un objeto Message desde un diccionario."""
        # Crear una copia para no modificar el original
        data_copy = data.copy()
        
        # Convertir timestamp si es necesario
        if 'timestamp' in data_copy and isinstance(data_copy['timestamp'], str):
            data_copy['timestamp'] = datetime.fromisoformat(data_copy['timestamp'])
            
        return cls(**data_copy)


@dataclass
class Conversation:
    """Modelo para representar una conversación completa."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    lead_id: Optional[str] = None
    messages: List[Message] = field(default_factory=list)
    
    # Metadatos
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    
    # Resumen y análisis
    summary: Optional[str] = None
    lead_info_extracted: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: str, content: str, 
                   audio_file_path: Optional[str] = None,
                   transcription: Optional[str] = None) -> None:
        """Añade un mensaje a la conversación."""
        message = Message(
            role=role,
            content=content,
            audio_file_path=audio_file_path,
            transcription=transcription
        )
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def end_conversation(self) -> None:
        """Marca la conversación como finalizada."""
        self.ended_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la conversación a un diccionario."""
        data = {
            'id': self.id,
            'lead_id': self.lead_id,
            'messages': [msg.to_dict() for msg in self.messages],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'summary': self.summary,
            'lead_info_extracted': self.lead_info_extracted
        }
        
        if self.ended_at:
            data['ended_at'] = self.ended_at.isoformat()
            
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """Crea un objeto Conversation desde un diccionario."""
        # Convertir los timestamps
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        if 'ended_at' in data and isinstance(data['ended_at'], str) and data['ended_at']:
            data['ended_at'] = datetime.fromisoformat(data['ended_at'])
        
        # Convertir los mensajes
        messages = []
        for msg_data in data.get('messages', []):
            messages.append(Message.from_dict(msg_data))
        
        # Crear la conversación sin los mensajes y luego añadirlos
        conversation = cls(
            id=data.get('id'),
            lead_id=data.get('lead_id'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            ended_at=data.get('ended_at'),
            summary=data.get('summary'),
            lead_info_extracted=data.get('lead_info_extracted', {})
        )
        
        conversation.messages = messages
        return conversation