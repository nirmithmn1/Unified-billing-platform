# dashboard_queries.py
import streamlit as st
from datetime import datetime, timedelta
import mysql.connector
from dotenv import load_dotenv
import os
import pandas as pd
import plotly.express as px

# Load environment variables
load_dotenv()

def get_db_connection():
    """Create and return a database connection."""
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 3307)),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'billing_platform')
    )

def check_vendor_columns():
    """Check if the trips table has the required vendor columns."""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SHOW COLUMNS FROM trips LIKE 'vendor_id'")
            return bool(cursor.fetchone())
        except Exception as e:
            print(f"Error checking vendor columns: {e}")
            return False

def get_completed_trips_count(vendor_id):
    """Get count of completed trips for a vendor."""
    if not check_vendor_columns():
        return 0
        
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM trips 
                WHERE vendor_id = %s AND status = 'completed'
            """, (vendor_id,))
            return cursor.fetchone()['count'] or 0
        except Exception as e:
            print(f"Error in get_completed_trips_count: {e}")
            return 0

def get_total_earnings(vendor_id):
    """Get total earnings for a vendor."""
    if not check_vendor_columns():
        return 0.0
        
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) as total 
                FROM trips 
                WHERE vendor_id = %s
            """, (vendor_id,))
            return float(cursor.fetchone()['total'])
        except Exception as e:
            print(f"Error in get_total_earnings: {e}")
            return 0.0

def show_vendor_trips(vendor_id):
    """Show recent trips for a vendor."""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT * FROM trips 
                WHERE vendor_id = %s 
                ORDER BY trip_date DESC 
                LIMIT 10
            """, (vendor_id,))
            trips = cursor.fetchall()
            if trips:
                return pd.DataFrame(trips)
            return None
        except Exception as e:
            print(f"Error in show_vendor_trips: {e}")
            return None

def get_total_trips():
    """Get total number of trips in the system."""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM trips")
        return cursor.fetchone()['count']

def get_total_revenue():
    """Get total revenue from all trips."""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COALESCE(SUM(amount), 0) as total FROM trips")
        return float(cursor.fetchone()['total'])

def get_active_billing_models_count():
    """Get count of active billing models."""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM billing_models WHERE is_active = 1")
        return cursor.fetchone()['count']

def show_billing_models():
    """Get all billing models."""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT * FROM billing_models
                ORDER BY created_at DESC
            """)
            models = cursor.fetchall()
            if models:
                return pd.DataFrame(models)
            return None
        except Exception as e:
            print(f"Error in show_billing_models: {e}")
            return None

def get_recent_activity(limit=10):
    """Get recent activity from audit logs."""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT * FROM audit_logs 
                ORDER BY created_at DESC 
                LIMIT %s
            """, (limit,))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error in get_recent_activity: {e}")
            return []

def get_employee_trips_count(employee_id):
    """Get trip count for an employee."""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM trips 
                WHERE created_by = %s
            """, (employee_id,))
            return cursor.fetchone()['count'] or 0
        except Exception as e:
            print(f"Error in get_employee_trips_count: {e}")
            return 0

def get_employee_incentives(employee_id):
    """Get total incentives for an employee."""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT COALESCE(SUM(incentive_amount), 0) as total 
                FROM incentives 
                WHERE employee_id = %s
            """, (employee_id,))
            result = cursor.fetchone()
            return float(result['total']) if result and 'total' in result else 0.0
        except Exception as e:
            print(f"Error in get_employee_incentives: {e}")
            return 0.0

def show_employee_trips(employee_id):
    """Show recent trips for an employee."""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT t.*, v.name as vendor_name 
                FROM trips t
                LEFT JOIN vendors v ON t.vendor_id = v.id
                WHERE t.created_by = %s 
                ORDER BY t.trip_date DESC 
                LIMIT 10
            """, (employee_id,))
            trips = cursor.fetchall()
            if trips:
                df = pd.DataFrame(trips)
                # Format date for better display
                if 'trip_date' in df.columns:
                    df['trip_date'] = pd.to_datetime(df['trip_date']).dt.strftime('%Y-%m-%d %H:%M')
                return df
            return None
        except Exception as e:
            print(f"Error in show_employee_trips: {e}")
            return None

def get_vendors_list():
    """Get list of all vendors."""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT v.*, u.username, u.role, u.is_active
                FROM vendors v
                LEFT JOIN users u ON v.email = u.email
                ORDER BY v.name
            """)
            vendors = cursor.fetchall()
            return pd.DataFrame(vendors) if vendors else pd.DataFrame()
        except Exception as e:
            print(f"Error in get_vendors_list: {e}")
            return pd.DataFrame()

def get_employees_list():
    """Get list of all employees."""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT e.*, u.username, u.email, u.phone, u.is_active
                FROM employees e
                JOIN users u ON e.user_id = u.id
                ORDER BY e.name
            """)
            employees = cursor.fetchall()
            return pd.DataFrame(employees) if employees else pd.DataFrame()
        except Exception as e:
            print(f"Error in get_employees_list: {e}")
            return pd.DataFrame()

def get_trips_summary(start_date, end_date):
    """Get trip summary for the given date range."""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT 
                    DATE(trip_date) as date,
                    COUNT(*) as trip_count,
                    AVG(amount) as avg_fare,
                    SUM(amount) as total_revenue
                FROM trips
                WHERE trip_date BETWEEN %s AND %s
                GROUP BY DATE(trip_date)
                ORDER BY date
            """, (start_date, end_date))
            trips = cursor.fetchall()
            if trips:
                df = pd.DataFrame(trips)
                df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
                return df
            return pd.DataFrame()
        except Exception as e:
            print(f"Error in get_trips_summary: {e}")
            return pd.DataFrame()

def get_revenue_by_vendor(start_date, end_date):
    """Get revenue by vendor for the given date range."""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT 
                    v.name as vendor_name,
                    COUNT(t.id) as trip_count,
                    COALESCE(SUM(t.amount), 0) as revenue,
                    AVG(t.amount) as avg_fare
                FROM vendors v
                LEFT JOIN trips t ON v.id = t.vendor_id 
                    AND t.trip_date BETWEEN %s AND %s
                GROUP BY v.id, v.name
                HAVING trip_count > 0
                ORDER BY revenue DESC
            """, (start_date, end_date))
            results = cursor.fetchall()
            return pd.DataFrame(results) if results else pd.DataFrame()
        except Exception as e:
            print(f"Error in get_revenue_by_vendor: {e}")
            return pd.DataFrame()

def get_vendor_performance(start_date, end_date):
    """Get vendor performance metrics."""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT 
                    v.id,
                    v.name as vendor_name,
                    COUNT(t.id) as trip_count,
                    COALESCE(SUM(t.amount), 0) as revenue,
                    AVG(t.amount) as avg_fare,
                    AVG(TIMESTAMPDIFF(MINUTE, t.pickup_time, t.drop_time)) as avg_trip_duration
                FROM vendors v
                LEFT JOIN trips t ON v.id = t.vendor_id 
                    AND t.trip_date BETWEEN %s AND %s
                GROUP BY v.id, v.name
                ORDER BY revenue DESC
            """, (start_date, end_date))
            results = cursor.fetchall()
            if results:
                df = pd.DataFrame(results)
                # Format numeric columns
                df['revenue'] = df['revenue'].round(2)
                df['avg_fare'] = df['avg_fare'].round(2)
                df['avg_trip_duration'] = df['avg_trip_duration'].round(1)
                return df
            return pd.DataFrame()
        except Exception as e:
            print(f"Error in get_vendor_performance: {e}")
            return pd.DataFrame()

def get_employee_performance(start_date, end_date):
    """Get employee performance metrics."""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT 
                    e.id,
                    e.name as employee_name,
                    COUNT(t.id) as trip_count,
                    COALESCE(SUM(i.amount), 0) as incentives,
                    AVG(t.amount) as avg_fare,
                    COUNT(DISTINCT t.vendor_id) as vendors_served
                FROM employees e
                LEFT JOIN trips t ON e.id = t.employee_id 
                    AND t.trip_date BETWEEN %s AND %s
                LEFT JOIN incentives i ON t.id = i.trip_id
                GROUP BY e.id, e.name
                HAVING trip_count > 0
                ORDER BY trip_count DESC
            """, (start_date, end_date))
            results = cursor.fetchall()
            if results:
                df = pd.DataFrame(results)
                # Format numeric columns
                df['incentives'] = df['incentives'].round(2)
                df['avg_fare'] = df['avg_fare'].round(2)
                return df
            return pd.DataFrame()
        except Exception as e:
            print(f"Error in get_employee_performance: {e}")
            return pd.DataFrame()

def get_users_list():
    """Get list of all users with their roles."""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT 
                    u.id,
                    u.username,
                    u.email,
                    u.phone,
                    u.role,
                    u.is_active,
                    u.created_at as last_login,
                    CASE 
                        WHEN u.role = 'vendor' THEN v.name
                        WHEN u.role = 'employee' THEN e.name
                        ELSE 'Admin'
                    END as display_name
                FROM users u
                LEFT JOIN vendors v ON u.email = v.email AND u.role = 'vendor'
                LEFT JOIN employees e ON u.email = e.email AND u.role = 'employee'
                ORDER BY u.role, u.username
            """)
            users = cursor.fetchall()
            if users:
                df = pd.DataFrame(users)
                # Format last login datetime
                if 'last_login' in df.columns:
                    df['last_login'] = pd.to_datetime(df['last_login']).dt.strftime('%Y-%m-%d %H:%M')
                return df
            return pd.DataFrame()
        except Exception as e:
            print(f"Error in get_users_list: {e}")
            return pd.DataFrame()