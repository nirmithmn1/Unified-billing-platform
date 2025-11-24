# backend/billing_config.py
import mysql.connector
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def get_db_connection():
    """Create and return a database connection"""
    try:
        return mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'billing_platform'),
            port=int(os.getenv('DB_PORT', 3307))
        )
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def save_billing_config(model_type, config_data):
    """Save billing configuration to the database"""
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            print("Failed to connect to database")
            return False
            
        cursor = conn.cursor()
        
        # Convert config_data to a JSON string
        try:
            config_json = json.dumps(config_data)
        except Exception as e:
            print(f"Error converting config_data to JSON: {e}")
            return False
        
        try:
            # First, deactivate any existing config for this model type
            cursor.execute("""
                UPDATE billing_configs 
                SET is_active = FALSE 
                WHERE model_type = %s AND is_active = TRUE
            """, (model_type,))
            
            # Insert the new configuration
            cursor.execute("""
                INSERT INTO billing_configs 
                (model_type, config_data, is_active)
                VALUES (%s, %s, TRUE)
            """, (model_type, config_json))
            
            conn.commit()
            return True
            
        except mysql.connector.Error as err:
            print(f"Database error: {err}")
            if conn:
                conn.rollback()
            return False
            
    except Exception as e:
        print(f"Unexpected error in save_billing_config: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn and conn.is_connected():
            conn.close()

def get_billing_config(model_type):
    """Retrieve the active billing configuration for a model type"""
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            print("Failed to connect to database")
            return {}
            
        cursor = conn.cursor(dictionary=True)
        
        # First, check if the table exists
        cursor.execute("""
            SELECT 1 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = 'billing_configs'
            LIMIT 1
        """)
        if not cursor.fetchone():
            print("billing_configs table does not exist")
            return {}
        
        # Get the active configuration
        cursor.execute("""
            SELECT * FROM billing_configs 
            WHERE model_type = %s AND is_active = TRUE
            ORDER BY created_at DESC 
            LIMIT 1
        """, (model_type,))
        
        config = cursor.fetchone()
        if not config:
            print(f"No active configuration found for model_type: {model_type}")
            return {}
            
        # Parse the JSON data if it exists
        if 'config_data' in config and config['config_data']:
            try:
                if isinstance(config['config_data'], str):
                    config['config_data'] = json.loads(config['config_data'])
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Error parsing config_data JSON: {e}")
                config['config_data'] = {}
        
        return config
        
    except mysql.connector.Error as err:
        print(f"Database error in get_billing_config: {err}")
        return {}
    except Exception as e:
        print(f"Unexpected error in get_billing_config: {e}")
        return {}
    finally:
        if conn and conn.is_connected():
            conn.close()

def ensure_billing_configs_table():
    """Ensure the billing_configs table exists with the correct schema"""
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            print("❌ Failed to connect to database")
            return False
            
        cursor = conn.cursor(dictionary=True)
        
        # First, check if the table exists with the correct schema
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'billing_configs'
        """)
        
        columns = {row['COLUMN_NAME']: row['DATA_TYPE'] for row in cursor.fetchall()}
        table_exists = bool(columns)
        
        # If table exists but is missing required columns, drop it
        if table_exists and 'config_data' not in columns:
            print("⚠️ Table exists but has incorrect schema. Dropping and recreating...")
            cursor.execute("DROP TABLE IF EXISTS billing_configs")
            conn.commit()
            table_exists = False
        
        # Create the table if it doesn't exist
        if not table_exists:
            print("🔄 Creating billing_configs table...")
            cursor.execute("""
                CREATE TABLE billing_configs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    model_type ENUM('package', 'trip', 'hybrid') NOT NULL,
                    config_data JSON,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_model_type (model_type, is_active)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("✅ billing_configs table created successfully")
            conn.commit()
            return True
        
        print("ℹ️ billing_configs table already exists with correct schema")
        return True
        
    except Exception as e:
        print(f"❌ Error ensuring billing_configs table: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn and conn.is_connected():
            conn.close()