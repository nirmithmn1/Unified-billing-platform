import mysql.connector
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def get_db_connection():
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

def list_users():
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username, role, is_active FROM users")
        users = cursor.fetchall()
        
        if not users:
            print("No users found in the database")
            return
            
        print("\nCurrent Users:")
        print("-" * 60)
        print(f"{'ID':<5} {'Username':<20} {'Role':<15} {'Active'}")
        print("-" * 60)
        for user in users:
            print(f"{user['id']:<5} {user['username']:<20} {user['role']:<15} {'Yes' if user['is_active'] else 'No'}")
            
    except Exception as e:
        print(f"Error listing users: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    list_users()