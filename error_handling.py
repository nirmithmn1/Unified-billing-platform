# error_handling.py
import logging
import traceback
import sys
from functools import wraps
from datetime import datetime
import streamlit as st
from typing import Optional, Type, Dict, Any, Callable
import mysql.connector
from mysql.connector import Error as MySQLError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app_errors.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Custom Exceptions
class AppError(Exception):
    """Base exception class for application-specific errors"""
    def __init__(self, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class DatabaseError(AppError):
    """Raised when a database operation fails"""
    def __init__(self, message: str, query: Optional[str] = None, params: Optional[Dict] = None):
        super().__init__(
            message=f"Database error: {message}",
            status_code=500,
            details={
                'query': query,
                'params': params
            }
        )

class ValidationError(AppError):
    """Raised when input validation fails"""
    def __init__(self, field: str, message: str):
        super().__init__(
            message=f"Validation error in field '{field}': {message}",
            status_code=422,
            details={'field': field, 'error': message}
        )

class AuthenticationError(AppError):
    """Raised when authentication fails"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, status_code=401)

class AuthorizationError(AppError):
    """Raised when a user is not authorized to perform an action"""
    def __init__(self, message: str = "Not authorized"):
        super().__init__(message=message, status_code=403)

# Error handler decorator
def handle_errors(func: Callable) -> Callable:
    """
    A decorator to handle exceptions and provide user-friendly error messages.
    Logs the full error details and displays a user-friendly message.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AppError as e:
            # Log the error
            logger.error(
                f"Application Error: {e.message}",
                extra={
                    'status_code': e.status_code,
                    'details': e.details,
                    'traceback': traceback.format_exc()
                }
            )
            # Show user-friendly error
            st.error(f"⚠️ {e.message}")
            if st.session_state.get('debug_mode', False):
                with st.expander("Error Details (Debug Mode)"):
                    st.json({
                        'error': e.message,
                        'status_code': e.status_code,
                        'details': e.details,
                        'timestamp': datetime.now().isoformat()
                    })
            return None
        except MySQLError as e:
            # Handle database errors
            error_msg = f"Database error: {str(e)}"
            logger.error(
                error_msg,
                extra={'traceback': traceback.format_exc()}
            )
            st.error("🔌 A database error occurred. Please try again later.")
            if st.session_state.get('debug_mode', False):
                with st.expander("Database Error Details (Debug Mode)"):
                    st.json({
                        'error': str(e),
                        'type': type(e).__name__,
                        'timestamp': datetime.now().isoformat()
                    })
            return None
        except Exception as e:
            # Handle all other exceptions
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(
                error_msg,
                extra={'traceback': traceback.format_exc()}
            )
            st.error("⚠️ An unexpected error occurred. Our team has been notified.")
            if st.session_state.get('debug_mode', False):
                with st.expander("Error Details (Debug Mode)"):
                    st.json({
                        'error': str(e),
                        'type': type(e).__name__,
                        'timestamp': datetime.now().isoformat(),
                        'traceback': traceback.format_exc()
                    })
            return None
    return wrapper

# Database error handler
def handle_db_errors(func: Callable) -> Callable:
    """Decorator specifically for database operations with retry logic"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except (mysql.connector.Error, mysql.connector.OperationalError) as e:
                if attempt == max_retries - 1:  # Last attempt
                    raise DatabaseError(
                        message=f"Database operation failed after {max_retries} attempts: {str(e)}",
                        query=getattr(args[0], 'query', None) if args else None,
                        params=getattr(args[0], 'params', None) if args else None
                    )
                # Wait before retrying (exponential backoff)
                time.sleep(2 ** attempt)
    return wrapper

# Validation helper
def validate_input(value: Any, field_name: str, validation_rules: Dict) -> bool:
    """Validate input based on rules"""
    if 'required' in validation_rules and not value:
        raise ValidationError(field_name, "This field is required")
    
    if 'min_length' in validation_rules and len(str(value)) < validation_rules['min_length']:
        raise ValidationError(
            field_name,
            f"Must be at least {validation_rules['min_length']} characters"
        )
    
    if 'max_length' in validation_rules and len(str(value)) > validation_rules['max_length']:
        raise ValidationError(
            field_name,
            f"Must be at most {validation_rules['max_length']} characters"
        )
    
    if 'pattern' in validation_rules and not re.match(validation_rules['pattern'], str(value)):
        raise ValidationError(
            field_name,
            f"Invalid format. Must match pattern: {validation_rules['pattern']}"
        )
    
    return True

# Error reporting function
def report_error(error: Exception, context: Optional[Dict] = None) -> None:
    """Report an error to the error tracking system"""
    error_info = {
        'timestamp': datetime.now().isoformat(),
        'error_type': type(error).__name__,
        'error_message': str(error),
        'context': context or {},
        'traceback': traceback.format_exc()
    }
    
    # Log the error
    logger.error(
        f"Error reported: {error}",
        extra=error_info
    )
    
    # Here you could also send the error to an external service like Sentry
    # if SENTRY_DSN:
    #     sentry_sdk.capture_exception(error, extra=context)
    
    return error_info