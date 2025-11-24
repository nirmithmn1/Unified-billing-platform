import os
from dotenv import load_dotenv
import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent))

# Load environment variables
load_dotenv()

# Import after setting up the path
from backend.database_connector import db

def test_connection():
    try:
        with db.get_connection() as conn:
            print("✅ Successfully connected to the database!")
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"📊 MySQL Version: {version[0]}")
            
            # Test creating a test table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_table (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    message VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Test table created successfully")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nTroubleshooting steps:")
        print("1. Is MySQL server running?")
        print("2. Are your database credentials in .env correct?")
        print("3. Is the database 'billing_platform' created?")
        print("4. Does the database user have proper permissions?")
        print(f"\nError details: {str(e)}")

if __name__ == "__main__":
    test_connection()