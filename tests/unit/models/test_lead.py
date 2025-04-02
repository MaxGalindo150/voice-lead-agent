import pytest
from datetime import datetime, timedelta
import json

from app.models.lead import Lead

class TestLead:
    
    def test_lead_creation_defaults(self):
        """Test creating a lead with default values"""
        lead = Lead()
        
        # Check that ID is generated
        assert lead.id is not None
        assert isinstance(lead.id, str)
        assert len(lead.id) > 0
        
        # Check default values
        assert lead.nombre is None
        assert lead.empresa is None
        assert lead.conversation_stage == "introduccion"
        assert isinstance(lead.created_at, datetime)
        assert isinstance(lead.updated_at, datetime)
        assert lead.conversation_ids == []
    
    def test_lead_creation_with_values(self):
        """Test creating a lead with specific values"""
        lead = Lead(
            id="lead123",
            nombre="John Doe",
            empresa="Acme Inc",
            cargo="CEO",
            email="john@acme.com",
            telefono="123456789",
            necesidades="Automation",
            presupuesto="10000",
            conversation_stage="calificacion"
        )
        
        assert lead.id == "lead123"
        assert lead.nombre == "John Doe"
        assert lead.empresa == "Acme Inc"
        assert lead.cargo == "CEO"
        assert lead.email == "john@acme.com"
        assert lead.telefono == "123456789"
        assert lead.necesidades == "Automation"
        assert lead.presupuesto == "10000"
        assert lead.conversation_stage == "calificacion"
    
    def test_to_dict(self):
        """Test converting a lead to dictionary"""
        # Create a lead with fixed timestamps
        created = datetime(2023, 1, 1, 12, 0, 0)
        updated = datetime(2023, 1, 1, 12, 30, 0)
        
        lead = Lead(
            id="lead123",
            nombre="John Doe",
            empresa="Acme Inc",
            created_at=created,
            updated_at=updated
        )
        
        # Convert to dictionary
        lead_dict = lead.to_dict()
        
        assert lead_dict["id"] == "lead123"
        assert lead_dict["nombre"] == "John Doe"
        assert lead_dict["empresa"] == "Acme Inc"
        assert lead_dict["created_at"] == created.isoformat()
        assert lead_dict["updated_at"] == updated.isoformat()
    
    def test_from_dict(self):
        """Test creating a lead from dictionary"""
        created_str = "2023-01-01T12:00:00"
        updated_str = "2023-01-01T12:30:00"
        
        lead_dict = {
            "id": "lead123",
            "nombre": "John Doe",
            "empresa": "Acme Inc",
            "email": "john@acme.com",
            "created_at": created_str,
            "updated_at": updated_str,
            "conversation_ids": ["conv1", "conv2"]
        }
        
        lead = Lead.from_dict(lead_dict)
        
        assert lead.id == "lead123"
        assert lead.nombre == "John Doe"
        assert lead.empresa == "Acme Inc"
        assert lead.email == "john@acme.com"
        assert lead.created_at == datetime.fromisoformat(created_str)
        assert lead.updated_at == datetime.fromisoformat(updated_str)
        assert lead.conversation_ids == ["conv1", "conv2"]
    
    def test_update(self):
        """Test updating a lead with new information"""
        lead = Lead(
            nombre="John Doe",
            empresa="Acme Inc"
        )
        original_updated_at = lead.updated_at
        
        # Small delay to ensure updated_at will be different
        # Not needed in the actual test, but helpful for clarity
        
        # Update lead with new information
        lead.update({
            "nombre": "Jane Doe",
            "cargo": "CTO",
            "necesidades": "Cloud Services"
        })
        
        # Check updated fields
        assert lead.nombre == "Jane Doe"  # Updated
        assert lead.empresa == "Acme Inc"  # Unchanged
        assert lead.cargo == "CTO"  # New value
        assert lead.necesidades == "Cloud Services"  # New value
        
        # Check that updated_at was changed
        assert lead.updated_at > original_updated_at
    
    def test_update_empty_values(self):
        """Test that update doesn't overwrite with empty values"""
        lead = Lead(
            nombre="John Doe",
            email="john@acme.com"
        )
        
        # Update with some empty values
        lead.update({
            "nombre": "",  # Empty string
            "email": None,  # None
            "cargo": "CEO"  # Valid value
        })
        
        # Empty values should not overwrite existing values
        assert lead.nombre == "John Doe"  # Not changed
        assert lead.email == "john@acme.com"  # Not changed
        assert lead.cargo == "CEO"  # New value
    
    def test_add_conversation(self):
        """Test adding a conversation to a lead"""
        lead = Lead()
        original_updated_at = lead.updated_at
        
        # Add a conversation
        lead.add_conversation("conv123")
        
        # Check the conversation was added
        assert "conv123" in lead.conversation_ids
        assert len(lead.conversation_ids) == 1
        
        # Check that updated_at was changed
        assert lead.updated_at > original_updated_at
        
        # Add the same conversation again
        old_updated_at = lead.updated_at
        lead.add_conversation("conv123")
        
        # It shouldn't be added twice
        assert lead.conversation_ids.count("conv123") == 1
        assert len(lead.conversation_ids) == 1