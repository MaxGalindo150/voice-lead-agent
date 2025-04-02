# app/db/repository.py
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import sqlite3

import json


from app.models.lead import Lead
from app.models.conversation import Conversation, Message
from app.db.base import Database

logger = logging.getLogger(__name__)

class LeadRepository:
    """Repositorio para gestionar leads (prospectos) en la base de datos."""
    
    def __init__(self, db: Optional[Database] = None):
        """
        Inicializa el repositorio.
        
        Args:
            db: Instancia de la base de datos (opcional)
        """
        self.db = db or Database()
    

    def save_lead(self, lead: Lead) -> str:
        """
        Guarda un lead en la base de datos.
        
        Args:
            lead: Objeto Lead a guardar
            
        Returns:
            ID del lead guardado
        """
        try:
            lead_dict = lead.to_dict()  # Esto ya debería convertir datetimes a strings
            
            # Convertir conversation_ids a formato serializable (JSON)
            if 'conversation_ids' in lead_dict:
                lead_dict['conversation_ids'] = json.dumps(lead_dict['conversation_ids'])
            
            # Asegurar que todas las fechas están en formato string
            for date_field in ['created_at', 'updated_at']:
                if date_field in lead_dict and not isinstance(lead_dict[date_field], str):
                    lead_dict[date_field] = lead_dict[date_field].isoformat()
            
            # Preparar consulta
            columns = ', '.join(lead_dict.keys())
            placeholders = ', '.join(['?' for _ in lead_dict])
            
            query = f"INSERT OR REPLACE INTO leads ({columns}) VALUES ({placeholders})"
            
            # Ejecutar consulta
            self.db.cursor.execute(query, tuple(lead_dict.values()))
            self.db.conn.commit()
            
            return lead.id
            
        except Exception as e:
            logger.error(f"Error al guardar lead: {str(e)}")
            self.db.conn.rollback()
            raise
    
    def get_lead(self, lead_id: str) -> Optional[Lead]:
        """
        Obtiene un lead por su ID.
        
        Args:
            lead_id: ID del lead a obtener
            
        Returns:
            Lead si existe, None en caso contrario
        """
        try:
            query = "SELECT * FROM leads WHERE id = ?"
            
            self.db.cursor.execute(query, (lead_id,))
            row = self.db.cursor.fetchone()
            
            if row:
                # Convertir a diccionario
                lead_dict = dict(row)
                
                # Deserializar conversation_ids de JSON
                if 'conversation_ids' in lead_dict and lead_dict['conversation_ids']:
                    try:
                        lead_dict['conversation_ids'] = json.loads(lead_dict['conversation_ids'])
                    except:
                        lead_dict['conversation_ids'] = []
                
                # Crear objeto Lead
                return Lead.from_dict(lead_dict)
            
            return None
            
        except Exception as e:
            logger.error(f"Error al obtener lead: {str(e)}")
            return None
    
    def update_lead(self, lead_id: str, updates: Dict[str, Any]) -> bool:
        """
        Actualiza un lead existente.
        
        Args:
            lead_id: ID del lead a actualizar
            updates: Diccionario con campos a actualizar
            
        Returns:
            True si se actualizó correctamente, False en caso contrario
        """
        try:
            # Verificar que el lead existe
            lead = self.get_lead(lead_id)
            if not lead:
                return False
            
            # Si 'updated_at' está en updates y es string, convertirlo a datetime
            if 'updated_at' in updates and isinstance(updates['updated_at'], str):
                try:
                    updates['updated_at'] = datetime.fromisoformat(updates['updated_at'])
                except ValueError:
                    # Si no se puede convertir, usar la fecha actual
                    updates['updated_at'] = datetime.now()
            
            # Si 'created_at' está en updates y es string, convertirlo a datetime
            if 'created_at' in updates and isinstance(updates['created_at'], str):
                try:
                    updates['created_at'] = datetime.fromisoformat(updates['created_at'])
                except ValueError:
                    # Si no se puede convertir, dejar el valor original
                    updates.pop('created_at')
            
            # Actualizar campos
            lead.update(updates)
            
            # Guardar cambios
            self.save_lead(lead)
            
            return True
        
        except Exception as e:
            logger.error(f"Error al actualizar lead: {str(e)}")
            self.db.conn.rollback()
            return False
    
    def get_all_leads(self) -> List[Lead]:
        """
        Obtiene todos los leads.
        
        Returns:
            Lista de todos los leads
        """
        try:
            query = "SELECT * FROM leads ORDER BY updated_at DESC"
            
            self.db.cursor.execute(query)
            rows = self.db.cursor.fetchall()
            
            # Convertir cada fila a un objeto Lead
            leads = []
            for row in rows:
                lead_dict = dict(row)
                leads.append(Lead.from_dict(lead_dict))
            
            return leads
            
        except Exception as e:
            logger.error(f"Error al obtener todos los leads: {str(e)}")
            return []
    
    def delete_lead(self, lead_id: str) -> bool:
        """
        Elimina un lead por su ID.
        
        Args:
            lead_id: ID del lead a eliminar
            
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        try:
            query = "DELETE FROM leads WHERE id = ?"
            
            self.db.cursor.execute(query, (lead_id,))
            self.db.conn.commit()
            
            return self.db.cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Error al eliminar lead: {str(e)}")
            self.db.conn.rollback()
            return False
        
        
class ConversationRepository:
    """Repositorio para gestionar conversaciones en la base de datos."""
    
    def __init__(self, db: Optional[Database] = None):
        """
        Inicializa el repositorio.
        
        Args:
            db: Instancia de la base de datos (opcional)
        """
        self.db = db or Database()
    
    def save_conversation(self, conversation: Conversation) -> str:
        """
        Guarda una conversación en la base de datos.
        
        Args:
            conversation: Objeto Conversation a guardar
            
        Returns:
            ID de la conversación guardada
        """
        try:
            # Primero guardar la conversación
            data = {
                'id': conversation.id,
                'lead_id': conversation.lead_id,
                'summary': conversation.summary,
                'lead_info_extracted': json.dumps(conversation.lead_info_extracted)
            }
            
            if isinstance(conversation.created_at, datetime):
                data['created_at'] = conversation.created_at.isoformat()
            else:
                data['created_at'] = str(conversation.created_at)
                
            if isinstance(conversation.updated_at, datetime):
                data['updated_at'] = conversation.updated_at.isoformat()
            else:
                data['updated_at'] = str(conversation.updated_at)
            
            if conversation.ended_at:
                if isinstance(conversation.ended_at, datetime):
                    data['ended_at'] = conversation.ended_at.isoformat()
                else:
                    data['ended_at'] = str(conversation.ended_at)
            
            # Preparar consulta
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            
            query = f"INSERT OR REPLACE INTO conversations ({columns}) VALUES ({placeholders})"
            
            # Ejecutar consulta
            self.db.cursor.execute(query, tuple(data.values()))
            
            # Luego guardar los mensajes
            # Primero eliminar mensajes existentes para esta conversación
            self.db.cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation.id,))
            
            # Insertar nuevos mensajes
            for message in conversation.messages:
                msg_data = {
                    'conversation_id': conversation.id,
                    'role': message.role,
                    'content': message.content,
                    'audio_file_path': message.audio_file_path,
                    'transcription': message.transcription
                }
                
                    # Manejar timestamp correctamente
                if isinstance(message.timestamp, datetime):
                    msg_data['timestamp'] = message.timestamp.isoformat()
                else:
                    msg_data['timestamp'] = str(message.timestamp)
                
                msg_columns = ', '.join(msg_data.keys())
                msg_placeholders = ', '.join(['?' for _ in msg_data])
                
                msg_query = f"INSERT INTO messages ({msg_columns}) VALUES ({msg_placeholders})"
                
                self.db.cursor.execute(msg_query, tuple(msg_data.values()))
            
            self.db.conn.commit()
            return conversation.id
            
        except Exception as e:
            logger.error(f"Error al guardar conversación: {str(e)}")
            self.db.conn.rollback()
            raise
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Obtiene una conversación por su ID.
        
        Args:
            conversation_id: ID de la conversación a obtener
            
        Returns:
            Conversation si existe, None en caso contrario
        """
        try:
            # Obtener datos de la conversación
            query = "SELECT * FROM conversations WHERE id = ?"
            
            self.db.cursor.execute(query, (conversation_id,))
            row = self.db.cursor.fetchone()
            
            if not row:
                return None
            
            # Convertir a diccionario
            conv_dict = dict(row)
            
            # Procesar campos específicos
            if 'lead_info_extracted' in conv_dict and conv_dict['lead_info_extracted']:
                try:
                    conv_dict['lead_info_extracted'] = json.loads(conv_dict['lead_info_extracted'])
                except:
                    conv_dict['lead_info_extracted'] = {}
            
            # Crear objeto Conversation
            conversation = Conversation.from_dict(conv_dict)
            
            # Obtener mensajes de la conversación
            msg_query = "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp"
            
            self.db.cursor.execute(msg_query, (conversation_id,))
            msg_rows = self.db.cursor.fetchall()
            
            # Añadir mensajes
            conversation.messages = []
            for msg_row in msg_rows:
                try:
                    msg_dict = dict(msg_row)
                    # Extraer los campos que sí usa Message
                    filtered_msg = {
                        'role': msg_dict.get('role'),
                        'content': msg_dict.get('content'),
                        'timestamp': msg_dict.get('timestamp'),
                        'audio_file_path': msg_dict.get('audio_file_path'),
                        'transcription': msg_dict.get('transcription'),
                        'id': msg_dict.get('id'),
                        'conversation_id': msg_dict.get('conversation_id')
                    }
                    # Eliminar None values para evitar problemas con campos requeridos
                    filtered_msg = {k: v for k, v in filtered_msg.items() if v is not None}
                    
                    message = Message(**filtered_msg)
                    conversation.messages.append(message)
                except Exception as e:
                    logger.error(f"Error al procesar mensaje: {str(e)}, datos: {msg_dict}")
                    # Continuar con el siguiente mensaje
            
            return conversation
            
        except Exception as e:
            logger.error(f"Error al obtener conversación: {str(e)}")
            return None
    
    def get_conversations_by_lead(self, lead_id: str) -> List[Conversation]:
        """
        Obtiene todas las conversaciones de un lead.
        
        Args:
            lead_id: ID del lead
            
        Returns:
            Lista de conversaciones
        """
        try:
            query = "SELECT id FROM conversations WHERE lead_id = ? ORDER BY created_at DESC"
            
            self.db.cursor.execute(query, (lead_id,))
            rows = self.db.cursor.fetchall()
            
            conversations = []
            for row in rows:
                conversation_id = row['id']
                conversation = self.get_conversation(conversation_id)
                if conversation:
                    conversations.append(conversation)
            
            return conversations
            
        except Exception as e:
            logger.error(f"Error al obtener conversaciones por lead: {str(e)}")
            return []
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Elimina una conversación por su ID.
        
        Args:
            conversation_id: ID de la conversación a eliminar
            
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        try:
            # Primero eliminar mensajes
            self.db.cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
            
            # Luego eliminar conversación
            query = "DELETE FROM conversations WHERE id = ?"
            
            self.db.cursor.execute(query, (conversation_id,))
            self.db.conn.commit()
            
            return self.db.cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Error al eliminar conversación: {str(e)}")
            self.db.conn.rollback()
            return False
    
    def get_all_conversations(self) -> List[Conversation]:
        """
        Obtiene todas las conversaciones.
        
        Returns:
            Lista de todas las conversaciones
        """
        try:
            query = "SELECT id FROM conversations ORDER BY updated_at DESC"
            
            self.db.cursor.execute(query)
            rows = self.db.cursor.fetchall()
            
            conversations = []
            for row in rows:
                conversation_id = row['id']
                conversation = self.get_conversation(conversation_id)
                if conversation:
                    conversations.append(conversation)
            
            return conversations
            
        except Exception as e:
            logger.error(f"Error al obtener todas las conversaciones: {str(e)}")
            return []