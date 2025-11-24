import os
import mysql.connector
from mysql.connector import pooling, Error as MySQLError
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseError(Exception):
    """Custom database error class"""
    pass

class DatabaseConnector:
    _instance = None
    _connection_pool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnector, cls).__new__(cls)
            cls._initialize_pool()
        return cls._instance

    @classmethod
    def _initialize_pool(cls):
        try:
            # Get database configuration from environment variables
            db_config = {
                "host": os.getenv("DB_HOST", "localhost"),
                "port": int(os.getenv("DB_PORT", 3306)),
                "database": os.getenv("DB_NAME", "billing_platform"),
                "user": os.getenv("DB_USER", "root"),
                "pool_name": "billing_pool",
                "pool_size": 5
            }
            
            # Only add password to config if it's set in the environment
            db_password = os.getenv("DB_PASSWORD")
            if db_password is not None and db_password != "":
                db_config["password"] = db_password

            logger.info(f"Initializing database connection pool with config: { {k: v for k, v in db_config.items() if k != 'password'} }")
            
            cls._connection_pool = pooling.MySQLConnectionPool(**db_config)
            logger.info("Database connection pool created successfully")
            
        except MySQLError as e:
            logger.error(f"Error creating connection pool: {e}")
            raise DatabaseError(f"Database connection failed: {e}")

    def get_connection(self):
        """Get a connection from the pool"""
        if self._connection_pool is None:
            self._initialize_pool()
        return self._connection_pool.get_connection()

    def execute_query(self, query, params=None, fetch_one=False):
        """Execute a query and return the results"""
        with self.get_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(query, params or ())
                if query.strip().upper().startswith(('SELECT', 'SHOW', 'DESCRIBE')):
                    return cursor.fetchone() if fetch_one else cursor.fetchall()
                else:
                    conn.commit()
                    return cursor.lastrowid

# Create a singleton instance
db = DatabaseConnector()