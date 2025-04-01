# models/lead.py
from typing import Dict, Any, Optional
from datetime import datetime

class Lead:
    """
    Modelo para representar un lead o prospecto.
    """
    
    def __init__(self, **kwargs):
        """
        Inicializa un lead con datos dinámicos.
        
        Args:
            **kwargs: Atributos del lead
        """
        self.id = kwargs.get("id")
        self.nombre = kwargs.get("nombre")
        self.empresa = kwargs.get("empresa")
        self.cargo = kwargs.get("cargo")
        self.email = kwargs.get("email")
        self.telefono = kwargs.get("telefono")
        self.necesidades = kwargs.get("necesidades")
        self.presupuesto = kwargs.get("presupuesto")
        self.plazo = kwargs.get("plazo")
        self.conversation_stage = kwargs.get("conversation_stage", "introduccion")
        self.created_at = kwargs.get("created_at", datetime.now().isoformat())
        self.last_interaction = kwargs.get("last_interaction", datetime.now().isoformat())
        
        # Campos dinámicos adicionales
        self.additional_data = {}
        for key, value in kwargs.items():
            if not hasattr(self, key):
                self.additional_data[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el lead a un diccionario.
        
        Returns:
            Dict[str, Any]: Representación del lead como diccionario
        """
        result = {
            "id": self.id,
            "nombre": self.nombre,
            "empresa": self.empresa,
            "cargo": self.cargo,
            "email": self.email,
            "telefono": self.telefono,
            "necesidades": self.necesidades,
            "presupuesto": self.presupuesto,
            "plazo": self.plazo,
            "conversation_stage": self.conversation_stage,
            "created_at": self.created_at,
            "last_interaction": self.last_interaction
        }
        
        # Eliminar campos None
        result = {k: v for k, v in result.items() if v is not None}
        
        # Añadir campos adicionales
        result.update(self.additional_data)
        
        return result
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Lead':
        """
        Crea un objeto Lead desde un diccionario.
        
        Args:
            data (Dict[str, Any]): Datos del lead
            
        Returns:
            Lead: Objeto Lead
        """
        return Lead(**data)