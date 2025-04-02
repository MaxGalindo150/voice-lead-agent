# app/db/repository.py
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import sqlite3
import time

import json


from app.models.lead import Lead
from app.models.conversation import Conversation, Message
from app.db.base import Database

logger = logging.getLogger(__name__)

class LeadRepository:
    """Repository for managing leads in the database."""
    
    def __init__(self, db: Optional[Database] = None):
        """
        Initializes the repository.
        
        Args:
            db: Database instance (optional)
        """
        self.db = db or Database()
    

    def save_lead(self, lead: Lead) -> str:
        """
        Saves a lead to the database.
        
        Args:
            lead: Lead object to save
            
        Returns:
            ID of the saved lead
        """
        try:
            lead_dict = lead.to_dict()  # This should already convert datetimes to strings
            
            # Convert conversation_ids to serializable format (JSON)
            if 'conversation_ids' in lead_dict:
                lead_dict['conversation_ids'] = json.dumps(lead_dict['conversation_ids'])
            
            # Ensure all dates are in string format
            for date_field in ['created_at', 'updated_at']:
                if date_field in lead_dict and not isinstance(lead_dict[date_field], str):
                    lead_dict[date_field] = lead_dict[date_field].isoformat()
            
            # Prepare query
            columns = ', '.join(lead_dict.keys())
            placeholders = ', '.join(['?' for _ in lead_dict])
            
            query = f"INSERT OR REPLACE INTO leads ({columns}) VALUES ({placeholders})"
            
            # Execute query
            self.db.cursor.execute(query, tuple(lead_dict.values()))
            self.db.conn.commit()
            
            return lead.id
            
        except Exception as e:
            logger.error(f"Error saving lead: {str(e)}")
            self.db.conn.rollback()
            raise

    def get_lead(self, lead_id: str, max_retries=3) -> Optional[Lead]:
        """
        Gets a lead by its ID.
        
        Args:
            lead_id: ID of the lead to get
            max_retries: Maximum number of retry attempts for database operations
            
        Returns:
            Lead if it exists, None otherwise
        """
        retries = 0
        while retries < max_retries:
            try:
                query = "SELECT * FROM leads WHERE id = ?"
                
                self.db.cursor.execute(query, (lead_id,))
                row = self.db.cursor.fetchone()
                
                if row:
                    # Convert to dictionary
                    lead_dict = dict(row)
                    
                    # Deserialize conversation_ids from JSON
                    if 'conversation_ids' in lead_dict and lead_dict['conversation_ids']:
                        try:
                            lead_dict['conversation_ids'] = json.loads(lead_dict['conversation_ids'])
                        except:
                            lead_dict['conversation_ids'] = []
                    
                    # Create Lead object
                    return Lead.from_dict(lead_dict)
                
                return None
                
            except sqlite3.OperationalError as e:
                if "Recursive use of cursors" in str(e):
                    retries += 1
                    logger.warning(f"Recursive cursor use detected, retry {retries}/{max_retries}")
                    time.sleep(0.1 * retries)  # Incrementar el tiempo de espera con cada reintento
                else:
                    logger.error(f"Database error getting lead: {str(e)}")
                    return None
            except Exception as e:
                logger.error(f"Error getting lead: {str(e)}")
                return None
        
        logger.error(f"Failed to get lead after {max_retries} retries due to recursive cursor use")
        return None
    
    def update_lead(self, lead_id: str, updates: Dict[str, Any]) -> bool:
        """
        Updates an existing lead.
        
        Args:
            lead_id: ID of the lead to update
            updates: Dictionary with fields to update
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            # Verify the lead exists
            lead = self.get_lead(lead_id)
            if not lead:
                return False
            
            # If 'updated_at' is in updates and is a string, convert it to datetime
            if 'updated_at' in updates and isinstance(updates['updated_at'], str):
                try:
                    updates['updated_at'] = datetime.fromisoformat(updates['updated_at'])
                except ValueError:
                    # If it can't be converted, use current date
                    updates['updated_at'] = datetime.now()
            
            # If 'created_at' is in updates and is a string, convert it to datetime
            if 'created_at' in updates and isinstance(updates['created_at'], str):
                try:
                    updates['created_at'] = datetime.fromisoformat(updates['created_at'])
                except ValueError:
                    # If it can't be converted, leave the original value
                    updates.pop('created_at')
            
            # Update fields
            lead.update(updates)
            
            # Save changes
            self.save_lead(lead)
            
            return True
        
        except Exception as e:
            logger.error(f"Error updating lead: {str(e)}")
            self.db.conn.rollback()
            return False
    
    def get_all_leads(self) -> List[Lead]:
        """
        Gets all leads.
        
        Returns:
            List of all leads
        """
        try:
            query = "SELECT * FROM leads ORDER BY updated_at DESC"
            
            self.db.cursor.execute(query)
            rows = self.db.cursor.fetchall()
            
            # Convert each row to a Lead object
            leads = []
            for row in rows:
                lead_dict = dict(row)
                leads.append(Lead.from_dict(lead_dict))
            
            return leads
            
        except Exception as e:
            logger.error(f"Error getting all leads: {str(e)}")
            return []
    
    def delete_lead(self, lead_id: str) -> bool:
        """
        Deletes a lead by its ID.
        
        Args:
            lead_id: ID of the lead to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            query = "DELETE FROM leads WHERE id = ?"
            
            self.db.cursor.execute(query, (lead_id,))
            self.db.conn.commit()
            
            return self.db.cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Error deleting lead: {str(e)}")
            self.db.conn.rollback()
            return False
        
        
class ConversationRepository:
    """Repository for managing conversations in the database."""
    
    def __init__(self, db: Optional[Database] = None):
        """
        Initializes the repository.
        
        Args:
            db: Database instance (optional)
        """
        self.db = db or Database()
    
    def save_conversation(self, conversation: Conversation) -> str:
        """
        Saves a conversation to the database.
        
        Args:
            conversation: Conversation object to save
            
        Returns:
            ID of the saved conversation
        """
        try:
            # First save the conversation
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
            
            # Prepare query
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            
            query = f"INSERT OR REPLACE INTO conversations ({columns}) VALUES ({placeholders})"
            
            # Execute query
            self.db.cursor.execute(query, tuple(data.values()))
            
            # Then save the messages
            # First delete existing messages for this conversation
            self.db.cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation.id,))
            
            # Insert new messages
            for message in conversation.messages:
                msg_data = {
                    'conversation_id': conversation.id,
                    'role': message.role,
                    'content': message.content,
                    'audio_file_path': message.audio_file_path,
                    'transcription': message.transcription
                }
                
                    # Handle timestamp correctly
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
            logger.error(f"Error saving conversation: {str(e)}")
            self.db.conn.rollback()
            raise
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Gets a conversation by its ID.
        
        Args:
            conversation_id: ID of the conversation to get
            
        Returns:
            Conversation if it exists, None otherwise
        """
        try:
            # Get conversation data
            query = "SELECT * FROM conversations WHERE id = ?"
            
            self.db.cursor.execute(query, (conversation_id,))
            row = self.db.cursor.fetchone()
            
            if not row:
                return None
            
            # Convert to dictionary
            conv_dict = dict(row)
            
            # Process specific fields
            if 'lead_info_extracted' in conv_dict and conv_dict['lead_info_extracted']:
                try:
                    conv_dict['lead_info_extracted'] = json.loads(conv_dict['lead_info_extracted'])
                except:
                    conv_dict['lead_info_extracted'] = {}
            
            # Create Conversation object
            conversation = Conversation.from_dict(conv_dict)
            
            # Get conversation messages
            msg_query = "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp"
            
            self.db.cursor.execute(msg_query, (conversation_id,))
            msg_rows = self.db.cursor.fetchall()
            
            # Add messages
            conversation.messages = []
            for msg_row in msg_rows:
                try:
                    msg_dict = dict(msg_row)
                    # Extract the fields that Message uses
                    filtered_msg = {
                        'role': msg_dict.get('role'),
                        'content': msg_dict.get('content'),
                        'timestamp': msg_dict.get('timestamp'),
                        'audio_file_path': msg_dict.get('audio_file_path'),
                        'transcription': msg_dict.get('transcription'),
                        'id': msg_dict.get('id'),
                        'conversation_id': msg_dict.get('conversation_id')
                    }
                    # Remove None values to avoid issues with required fields
                    filtered_msg = {k: v for k, v in filtered_msg.items() if v is not None}
                    
                    message = Message(**filtered_msg)
                    conversation.messages.append(message)
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}, data: {msg_dict}")
                    # Continue with the next message
            
            return conversation
            
        except Exception as e:
            logger.error(f"Error getting conversation: {str(e)}")
            return None
    
    def get_conversations_by_lead(self, lead_id: str) -> List[Conversation]:
        """
        Gets all conversations for a lead.
        
        Args:
            lead_id: ID of the lead
            
        Returns:
            List of conversations
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
            logger.error(f"Error getting conversations by lead: {str(e)}")
            return []
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Deletes a conversation by its ID.
        
        Args:
            conversation_id: ID of the conversation to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # First delete messages
            self.db.cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
            
            # Then delete conversation
            query = "DELETE FROM conversations WHERE id = ?"
            
            self.db.cursor.execute(query, (conversation_id,))
            self.db.conn.commit()
            
            return self.db.cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Error deleting conversation: {str(e)}")
            self.db.conn.rollback()
            return False
    
    def get_all_conversations(self) -> List[Conversation]:
        """
        Gets all conversations.
        
        Returns:
            List of all conversations
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
            logger.error(f"Error getting all conversations: {str(e)}")
            return []