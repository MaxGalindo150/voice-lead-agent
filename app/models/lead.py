# app/models/lead.py
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid


@dataclass
class Lead:
    """Data model for representing a lead (prospect)."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    nombre: Optional[str] = None
    empresa: Optional[str] = None
    cargo: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    
    # Qualification information
    necesidades: Optional[str] = None
    presupuesto: Optional[str] = None
    plazo: Optional[str] = None
    punto_dolor: Optional[str] = None
    producto_interes: Optional[str] = None
    
    # Conversation stage
    conversation_stage: str = "introduccion"
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Relationship with conversations
    conversation_ids: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converts the Lead object to a dictionary."""
        data = asdict(self)
        # Convert datetimes to ISO strings for serialization
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Lead':
        """Creates a Lead object from a dictionary."""
        # Convert ISO strings to datetimes
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        return cls(**data)
    
    def update(self, info: Dict[str, Any]) -> None:
        """Updates the lead fields with new information."""
        for key, value in info.items():
            if hasattr(self, key) and value:  # Only update if the value is not None or empty
                setattr(self, key, value)
        
        # Update timestamp
        self.updated_at = datetime.now()
        
    def add_conversation(self, conversation_id: str) -> None:
        """Associates a conversation with this lead."""
        if conversation_id not in self.conversation_ids:
            self.conversation_ids.append(conversation_id)
            self.updated_at = datetime.now()