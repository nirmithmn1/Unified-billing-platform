import mysql.connector
from dotenv import load_dotenv
import os

def update_admin_password():
    load_dotenv()
    
    try:
        # Connect to the database
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'billing_platform'),
            port=int(os.getenv('DB_PORT', 3307))
        )
        
        cursor = conn.cursor()
        
        # The hashed password for "admin123"
        hashed_password = "$2b$12$LQv3c1yigFQYkHNyBmZ0bO9Xv7JQ9w8z6vJZ8VhW5YdN3XrZ1vJbK"
        
        # Update the password
        cursor.execute(
            "UPDATE users SET password = %s WHERE username = 'admin'",
            (hashed_password,)
        )
        
        conn.commit()
        print("✅ Admin password updated successfully!")
        
    except Exception as e:
        print(f"❌ Error updating password: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    update_admin_password()