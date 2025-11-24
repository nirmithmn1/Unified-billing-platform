import mysql.connector
from dotenv import load_dotenv
import os
import hashlib

load_dotenv()

def update_employee_password(username, new_password):
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'billing_platform'),
        port=int(os.getenv('DB_PORT', 3307))
    )
    
    try:
        cursor = conn.cursor()
        hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
        
        cursor.execute("""
            UPDATE users 
            SET password = %s 
            WHERE username = %s AND role = 'employee'
        """, (hashed_password, username))
        
        conn.commit()
        print(f"Password updated for employee: {username}")
        return True
        
    except Exception as e:
        print(f"Error updating password: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("Update Employee Password")
    print("-----------------------")
    username = input("Enter employee username: ")
    new_password = input("Enter new password: ")
    confirm = input("Confirm new password: ")
    
    if new_password != confirm:
        print("Error: Passwords do not match!")
    else:
        update_employee_password(username, new_password)