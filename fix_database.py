# fix_database.py
import mysql.connector
from dotenv import load_dotenv
import os
from werkzeug.security import generate_password_hash

load_dotenv()

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 3307)),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'billing_platform')
    )

def fix_users_table():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Add role column if it doesn't exist
        cursor.execute("""
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS role ENUM('admin', 'user') DEFAULT 'user' AFTER is_active
        """)
        
        # Add updated_at column if it doesn't exist
        cursor.execute("""
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        """)
        
        conn.commit()
        print("✅ Successfully updated users table")
        return True
        
    except Exception as e:
        print(f"❌ Error updating users table: {e}")
        return False
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def fix_indexes():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("Dropping existing indexes...")
        # First, disable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS=0;")
        conn.commit()
        
        # Drop existing indexes one by one
        drop_queries = [
            "DROP INDEX IF EXISTS idx_customer_name ON customers",
            "DROP INDEX IF EXISTS idx_customer_email ON customers",
            "DROP INDEX IF EXISTS idx_trip_client_date ON trips",
            "DROP INDEX IF EXISTS idx_invoice_client_date ON invoices",
            "DROP INDEX IF EXISTS idx_invoice_number ON invoices",
            "DROP INDEX IF EXISTS idx_payment_invoice ON payments",
            "DROP INDEX IF EXISTS idx_audit_log_entity ON audit_logs"
        ]
        
        for query in drop_queries:
            try:
                cursor.execute(query)
                conn.commit()
                if "DROP INDEX" in query:
                    print(f"  Dropped index: {query.split()[-1]}")
            except Exception as e:
                print(f"  ⚠️ Warning (drop): {e}")
                conn.rollback()
        
        print("\nCreating new indexes...")
        # Create indexes one by one
        create_queries = [
            "CREATE INDEX IF NOT EXISTS idx_customer_name ON customers(name)",
            "CREATE INDEX IF NOT EXISTS idx_customer_email ON customers(email)",
            "CREATE INDEX IF NOT EXISTS idx_trip_client_date ON trips(client_id, trip_date)",
            "CREATE INDEX IF NOT EXISTS idx_invoice_number ON invoices(invoice_number)",
            "CREATE INDEX IF NOT EXISTS idx_payment_invoice ON payments(invoice_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_logs(entity_type, entity_id)"
        ]
        
        for query in create_queries:
            try:
                cursor.execute(query)
                conn.commit()
                print(f"  Created index: {query.split()[-1].split('(')[0]}")
            except Exception as e:
                print(f"  ⚠️ Warning (create): {e}")
                conn.rollback()
        
        # Re-enable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS=1;")
        conn.commit()
        
        print("\n✅ Successfully updated database indexes")
        return True
        
    except Exception as e:
        print(f"❌ Error updating indexes: {e}")
        return False
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def create_admin_user():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if admin exists
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        admin = cursor.fetchone()
        
        if not admin:
            # Generate password hash using werkzeug
            password_hash = generate_password_hash('admin123')
            
            cursor.execute("""
            INSERT INTO users 
            (username, password_hash, email, full_name, is_active, role)
            VALUES (%s, %s, %s, %s, %s, %s)
            """, ('admin', password_hash, 'admin@example.com', 'Admin User', 1, 'admin'))
            
            conn.commit()
            print("✅ Admin user created successfully")
            print("   Username: admin")
            print("   Password: admin123")
        else:
            print("ℹ️ Admin user already exists")
            
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def main():
    print("🚀 Starting database fix...")
    
    # Fix users table
    print("\n1. Checking users table...")
    if not fix_users_table():
        print("❌ Failed to fix users table")
        return
    
    # Fix indexes
    print("\n2. Checking database indexes...")
    if not fix_indexes():
        print("❌ Failed to fix indexes")
        return
    
    # Create admin user
    print("\n3. Setting up admin user...")
    if not create_admin_user():
        print("❌ Failed to create admin user")
        return
    
    print("\n✅ Database fixes completed successfully!")
    print("\nYou can now run the application using:")
    print("streamlit run app.py")

if __name__ == "__main__":
    main()