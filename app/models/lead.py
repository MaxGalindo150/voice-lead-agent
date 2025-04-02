# app/models/lead.py
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid


@dataclass
class Lead:
    """Modelo de datos para representar un lead (prospecto)."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    nombre: Optional[str] = None
    empresa: Optional[str] = None
    cargo: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    
    # Información de cualificación
    necesidades: Optional[str] = None
    presupuesto: Optional[str] = None
    plazo: Optional[str] = None
    punto_dolor: Optional[str] = None
    producto_interes: Optional[str] = None
    
    # Etapa de la conversación
    conversation_stage: str = "introduccion"
    
    # Metadatos
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Relación con conversaciones
    conversation_ids: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el objeto Lead a un diccionario."""
        data = asdict(self)
        # Convertir datetimes a strings ISO para serialización
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Lead':
        """Crea un objeto Lead desde un diccionario."""
        # Convertir strings ISO a datetimes
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        return cls(**data)
    
    def update(self, info: Dict[str, Any]) -> None:
        """Actualiza los campos del lead con nueva información."""
        for key, value in info.items():
            if hasattr(self, key) and value:  # Solo actualizar si el valor no es None o vacío
                setattr(self, key, value)
        
        # Actualizar timestamp
        self.updated_at = datetime.now()
        
    def add_conversation(self, conversation_id: str) -> None:
        """Asocia una conversación con este lead."""
        if conversation_id not in self.conversation_ids:
            self.conversation_ids.append(conversation_id)
            self.updated_at = datetime.now()