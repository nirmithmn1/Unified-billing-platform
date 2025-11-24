# setup_database.py
import os
import sys
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import logging
from typing import Optional
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def get_db_connection(use_database: bool = False) -> Optional[mysql.connector.connection.MySQLConnection]:
    """Create and return a database connection."""
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            port=int(os.getenv('DB_PORT', 3307)),
            database=os.getenv('DB_NAME', 'billing_platform') if use_database else None,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        return conn
    except Error as e:
        logger.error(f"Error connecting to MySQL: {e}")
        return None

def execute_sql_file(conn: mysql.connector.connection.MySQLConnection, file_path: str) -> bool:
    """Execute SQL commands from a file with error handling."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            sql_commands = file.read().split(';')
        
        cursor = conn.cursor()
        
        for command in sql_commands:
            command = command.strip()
            if not command:
                continue
                
            try:
                cursor.execute(command)
                conn.commit()
            except Error as e:
                if "already exists" in str(e).lower() or "Duplicate" in str(e):
                    logger.warning(f"Warning (non-fatal): {e}")
                    conn.rollback()
                else:
                    logger.error(f"Error executing command: {e}")
                    logger.error(f"Command: {command[:200]}...")
                    return False
        
        return True
    except Exception as e:
        logger.error(f"Error executing SQL file: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()

def setup_database() -> bool:
    """Set up the database by executing the schema file."""
    load_dotenv()
    
    # Connect to MySQL server (without database)
    conn = get_db_connection(use_database=False)
    if not conn:
        return False
    
    try:
        # Create database if not exists
        cursor = conn.cursor()
        cursor.execute("""
            CREATE DATABASE IF NOT EXISTS billing_platform 
            CHARACTER SET utf8mb4 
            COLLATE utf8mb4_unicode_ci
        """)
        conn.commit()
        cursor.close()
        
        # Reconnect with database
        conn.database = os.getenv('DB_NAME', 'billing_platform')
        
        # Execute schema file
        schema_file = os.path.join('database', 'schema.sql')
        if not os.path.exists(schema_file):
            logger.error(f"Schema file not found: {schema_file}")
            return False
            
        if not execute_sql_file(conn, schema_file):
            return False
            
        logger.info("✅ Database setup completed successfully!")
        return True
        
    except Error as e:
        logger.error(f"Database error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False
    finally:
        if conn and conn.is_connected():
            conn.close()

if __name__ == "__main__":
    if setup_database():
        sys.exit(0)
    else:
        sys.exit(1)