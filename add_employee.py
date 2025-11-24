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

def add_employee(username, password, email, name, phone=None):
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Insert into users table without the name field
        cursor.execute("""
            INSERT INTO users (username, password, email, phone, role, is_active)
            VALUES (%s, %s, %s, %s, 'employee', 1)
        """, (username, hashed_password, email, phone))
        
        # Get the auto-generated user_id
        user_id = cursor.lastrowid
        
        # Add to employees table with the name
        try:
            cursor.execute("""
                INSERT INTO employees (user_id, name, email, phone, is_active)
                VALUES (%s, %s, %s, %s, 1)
            """, (user_id, name, email, phone))
        except mysql.connector.Error as e:
            print(f"Note: Couldn't add to employees table. Error: {e}")
            print("Continuing with user creation...")
        
        conn.commit()
        print(f"Employee '{username}' added successfully with ID: {user_id}")
        return True
        
    except mysql.connector.Error as e:
        print(f"Error adding employee: {e}")
        return False
    finally:
        if conn and conn.is_connected():
            conn.close()

if __name__ == "__main__":
    print("Add New Employee User")
    print("---------------------")
    username = input("Enter employee username: ")
    password = input("Enter password: ")
    confirm = input("Confirm password: ")
    name = input("Enter full name: ")
    email = input("Enter email: ")
    phone = input("Enter phone (optional): ") or None
    
    if password != confirm:
        print("Error: Passwords do not match!")
    else:
        if add_employee(username, password, email, name, phone):
            print("Employee added successfully!")
        else:
            print("Failed to add employee. Check the error message above.")