# db/repository.py
import uuid
import json
import os
import logging
from typing import Dict, Any, List, Optional

from app.db.base import BaseRepository
from app.models.lead import Lead
from app import config

logger = logging.getLogger(__name__)

class LeadRepository(BaseRepository):
    """
    Repositorio para gestionar leads.
    
    Esta implementación usa archivos JSON como almacenamiento, 
    pero podría cambiarse por una base de datos real.
    """
    
    def __init__(self, storage_dir: str = None):
        """
        Inicializa el repositorio de leads.
        
        Args:
            storage_dir (str, optional): Directorio para almacenar los archivos JSON
        """
        self.storage_dir = storage_dir or config.LEADS_STORAGE_DIR or "data/leads"
        
        # Crear directorio si no existe
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def _get_file_path(self, lead_id: str) -> str:
        """
        Obtiene la ruta del archivo para un lead.
        
        Args:
            lead_id (str): ID del lead
            
        Returns:
            str: Ruta del archivo
        """
        return os.path.join(self.storage_dir, f"{lead_id}.json")
    
    def create(self, data: Dict[str, Any]) -> str:
        """
        Crea un nuevo lead.
        
        Args:
            data (Dict[str, Any]): Datos del lead
            
        Returns:
            str: ID del lead creado
        """
        # Generar ID único si no se proporciona
        lead_id = data.get("id") or str(uuid.uuid4())
        
        # Asegurarse de que el ID esté en los datos
        data["id"] = lead_id
        
        # Guardar en archivo
        file_path = self._get_file_path(lead_id)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Lead creado: {lead_id}")
        return lead_id
    
    def get(self, id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un lead por su ID.
        
        Args:
            id (str): ID del lead
            
        Returns:
            Optional[Dict[str, Any]]: Datos del lead o None si no existe
        """
        file_path = self._get_file_path(id)
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception as e:
            logger.error(f"Error al leer lead {id}: {str(e)}")
            return None
    
    def get_lead(self, id: str) -> Optional[Lead]:
        """
        Obtiene un lead como objeto Lead.
        
        Args:
            id (str): ID del lead
            
        Returns:
            Optional[Lead]: Objeto Lead o None si no existe
        """
        data = self.get(id)
        if not data:
            return None
        
        return Lead(**data)
    
    def update(self, id: str, data: Dict[str, Any]) -> bool:
        """
        Actualiza un lead existente.
        
        Args:
            id (str): ID del lead
            data (Dict[str, Any]): Datos a actualizar
            
        Returns:
            bool: True si la actualización fue exitosa
        """
        # Verificar si existe
        current_data = self.get(id)
        if not current_data:
            return False
        
        # Actualizar datos
        current_data.update(data)
        
        # Asegurar que el ID sea consistente
        current_data["id"] = id
        
        # Guardar actualización
        file_path = self._get_file_path(id)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(current_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Lead actualizado: {id}")
        return True
    
    def delete(self, id: str) -> bool:
        """
        Elimina un lead.
        
        Args:
            id (str): ID del lead
            
        Returns:
            bool: True si la eliminación fue exitosa
        """
        file_path = self._get_file_path(id)
        if not os.path.exists(file_path):
            return False
        
        try:
            os.remove(file_path)
            logger.info(f"Lead eliminado: {id}")
            return True
        except Exception as e:
            logger.error(f"Error al eliminar lead {id}: {str(e)}")
            return False
    
    def list_leads(self) -> List[Dict[str, Any]]:
        """
        Lista todos los leads.
        
        Returns:
            List[Dict[str, Any]]: Lista de datos de leads
        """
        leads = []
        for filename in os.listdir(self.storage_dir):
            if filename.endswith(".json"):
                lead_id = filename[:-5]  # Quitar la extensión .json
                lead_data = self.get(lead_id)
                if lead_data:
                    leads.append(lead_data)
        
        return leads
    
    def create_or_update_lead(self, data: Dict[str, Any]) -> str:
        """
        Crea o actualiza un lead basado en la información disponible.
        
        Args:
            data (Dict[str, Any]): Datos del lead
            
        Returns:
            str: ID del lead
        """
        # Si hay ID, intentar actualizar
        if "id" in data and data["id"]:
            lead_id = data["id"]
            success = self.update(lead_id, data)
            if success:
                return lead_id
        
        # Si no hay ID o la actualización falló, buscar por email o nombre+empresa
        leads = self.list_leads()
        
        # Buscar por email
        if "email" in data and data["email"]:
            for lead in leads:
                if lead.get("email") == data["email"]:
                    lead_id = lead["id"]
                    self.update(lead_id, data)
                    return lead_id
        
        # Buscar por nombre y empresa
        if "nombre" in data and data["nombre"] and "empresa" in data and data["empresa"]:
            for lead in leads:
                if (lead.get("nombre") == data["nombre"] and 
                    lead.get("empresa") == data["empresa"]):
                    lead_id = lead["id"]
                    self.update(lead_id, data)
                    return lead_id
        
        # Si no se encontró, crear nuevo
        return self.create(data)