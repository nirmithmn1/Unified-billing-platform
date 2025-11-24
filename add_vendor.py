import mysql.connector
from dotenv import load_dotenv
import os
import hashlib

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

def add_vendor(username, password, email, phone=None):
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # First, add to users table
        cursor.execute("""
            INSERT INTO users (username, password, email, phone, role, is_active)
            VALUES (%s, %s, %s, %s, 'vendor', TRUE)
        """, (username, hashed_password, email, phone))
        
        # Get the user_id of the newly created user
        user_id = cursor.lastrowid
        
        # Then add to vendors table
        cursor.execute("""
            INSERT INTO vendors (name, email, phone, is_active)
            VALUES (%s, %s, %s, TRUE)
        """, (username, email, phone))
        
        conn.commit()
        print(f"Vendor '{username}' added successfully!")
        return True
        
    except mysql.connector.Error as e:
        print(f"Error adding vendor: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn and conn.is_connected():
            conn.close()

if __name__ == "__main__":
    print("\nAdd New Vendor User")
    print("-------------------")
    username = input("Enter vendor username: ").strip()
    password = input("Enter password: ").strip()
    confirm = input("Confirm password: ").strip()
    email = input("Enter email: ").strip()
    phone = input("Enter phone (optional): ").strip() or None
    
    if not username or not password or not email:
        print("Error: Username, password, and email are required!")
    elif password != confirm:
        print("Error: Passwords do not match!")
    else:
        if add_vendor(username, password, email, phone):
            print("Vendor added successfully!")
        else:
            print("Failed to add vendor. Check the error message above.")