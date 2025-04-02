import pytest
import os
import sqlite3
from unittest.mock import patch, MagicMock
import tempfile
import shutil

from app.db.base import Database

class TestDatabase:
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test database files"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Clean up after test
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def db_path(self, temp_dir):
        """Create a path for the test database"""
        return os.path.join(temp_dir, "test_leads.db")
    
    def test_initialization(self, db_path):
        """Test database initialization with default settings"""
        db = Database(db_path=db_path)
        
        # Verify connection was established
        assert db.conn is not None
        assert db.cursor is not None
        
        # Verify the database file was created
        assert os.path.exists(db_path)
        
        # Clean up
        db.conn.close()
    
    def test_initialization_with_directory_creation(self, temp_dir):
        """Test database initialization with directory creation"""
        nested_dir = os.path.join(temp_dir, "nested", "path")
        db_path = os.path.join(nested_dir, "test_leads.db")
        
        # Directory shouldn't exist yet
        assert not os.path.exists(nested_dir)
        
        # Initialize database, which should create the directory
        db = Database(db_path=db_path)
        
        # Verify directory and file were created
        assert os.path.exists(nested_dir)
        assert os.path.exists(db_path)
        
        # Clean up
        db.conn.close()
    
    def test_init_tables(self, db_path):
        """Test that tables are properly initialized"""
        db = Database(db_path=db_path)
        
        # Check if tables exist by querying the sqlite_master table
        db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in db.cursor.fetchall()]
        
        # Verify our three tables were created
        assert "leads" in tables
        assert "conversations" in tables
        assert "messages" in tables
        
        # Check the schema of the leads table
        db.cursor.execute("PRAGMA table_info(leads)")
        columns = {row[1] for row in db.cursor.fetchall()}
        
        # Verify some of the expected columns exist
        expected_columns = {"id", "nombre", "empresa", "email", "telefono", "necesidades", 
                           "presupuesto", "plazo", "conversation_stage"}
        assert expected_columns.issubset(columns)
        
        # Clean up
        db.conn.close()
    
    def test_connection_error_handling(self):
        """Test error handling during connection"""
        # Use an invalid path to force a connection error
        invalid_path = "/:invalid:path:/leads.db"
        
        with patch('os.makedirs') as mock_makedirs:
            # Make os.makedirs raise an exception
            mock_makedirs.side_effect = PermissionError("Permission denied")
            
            with pytest.raises(PermissionError) as excinfo:
                Database(db_path=invalid_path)
            
            assert "Permission denied" in str(excinfo.value)
    
    def test_table_schema_preservation(self, db_path):
        """Test that existing table schemas are preserved when initializing the database"""
        # First, create a db connection
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create a table with a different schema than what our Database class would create
        cursor.execute("CREATE TABLE leads (id INTEGER PRIMARY KEY, test_column TEXT)")
        conn.commit()
        conn.close()
        
        # Initialize our database with the existing file
        db = Database(db_path=db_path)
        
        # Check the schema to verify our original schema was preserved
        db.cursor.execute("PRAGMA table_info(leads)")
        columns = {row[1] for row in db.cursor.fetchall()}
        
        # Our original schema should be preserved (SQLite's IF NOT EXISTS behavior)
        assert "test_column" in columns
        
        # Check for INTEGER vs TEXT type for ID
        db.cursor.execute("PRAGMA table_info(leads)")
        id_column_type = None
        for row in db.cursor.fetchall():
            if row[1] == "id":
                id_column_type = row[2]
                break
        
        # The id should still be INTEGER type from our original schema, not TEXT from the Database class
        assert id_column_type == "INTEGER"
        
        # Clean up
        db.conn.close()
    
    def test_row_factory(self, db_path):
        """Test that row_factory is properly set"""
        db = Database(db_path=db_path)
        
        # Insert a test row
        db.cursor.execute('''
            INSERT INTO leads (id, nombre, empresa) 
            VALUES (?, ?, ?)
        ''', ('123', 'Test Name', 'Test Company'))
        db.conn.commit()
        
        # Query the row back
        db.cursor.execute("SELECT id, nombre, empresa FROM leads WHERE id = ?", ('123',))
        row = db.cursor.fetchone()
        
        # Verify we can access by column name due to row_factory
        assert row['id'] == '123'
        assert row['nombre'] == 'Test Name'
        assert row['empresa'] == 'Test Company'
        
        # Clean up
        db.conn.close()
    
    def test_commit_after_table_creation(self, db_path):
        """Test that successful table creation leads to a commit"""
        # Initialize database
        db = Database(db_path=db_path)
        db.conn.close()
        
        # Connect again to check persistence
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tables were committed and exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        
        # All tables should exist
        assert "leads" in tables
        assert "conversations" in tables
        assert "messages" in tables
        
        conn.close()
