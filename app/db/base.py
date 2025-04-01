# db/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseRepository(ABC):
    """Clase base para todos los repositorios."""
    
    @abstractmethod
    def create(self, data: Dict[str, Any]) -> str:
        """
        Crea un nuevo registro.
        
        Args:
            data (Dict[str, Any]): Datos a guardar
            
        Returns:
            str: ID del registro creado
        """
        pass
    
    @abstractmethod
    def get(self, id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un registro por su ID.
        
        Args:
            id (str): ID del registro
            
        Returns:
            Optional[Dict[str, Any]]: Datos del registro o None si no existe
        """
        pass
    
    @abstractmethod
    def update(self, id: str, data: Dict[str, Any]) -> bool:
        """
        Actualiza un registro existente.
        
        Args:
            id (str): ID del registro
            data (Dict[str, Any]): Datos a actualizar
            
        Returns:
            bool: True si la actualización fue exitosa
        """
        pass
    
    @abstractmethod
    def delete(self, id: str) -> bool:
        """
        Elimina un registro.
        
        Args:
            id (str): ID del registro
            
        Returns:
            bool: True si la eliminación fue exitosa
        """
        pass