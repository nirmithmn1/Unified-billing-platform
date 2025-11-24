# main_app.py
import streamlit as st
import mysql.connector
from dotenv import load_dotenv
import os
import hashlib
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
from vendor_dashboard import render_vendor_dashboard
from backend.billing_config import save_billing_config, get_billing_config
from admin_dashboard import show_admin_dashboard

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
        st.error(f"Database connection error: {e}")
        return None

def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    if not stored_password:
        return False
    try:
        # Try SHA-256 hashing
        hashed_provided = hashlib.sha256(provided_password.encode()).hexdigest()
        if stored_password == hashed_provided:
            return True
        # Try direct comparison (for backward compatibility)
        if stored_password == provided_password:
            return True
        return False
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

def login_section():
    st.title("Billing Platform Login")
    st.write("Select your role and enter your credentials to continue.")
    
    # Role selection
    role = st.radio("Select your role:", ["Admin", "Vendor", "Employee"])
    
    # Login form
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            if not username or not password:
                st.error("Please enter both username and password")
                return
                
            conn = get_db_connection()
            if not conn:
                st.error("Database connection failed")
                return
                
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    "SELECT * FROM users WHERE username = %s AND role = %s", 
                    (username, role.lower())
                )
                user = cursor.fetchone()
                
                if user and verify_password(user['password'], password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.user_role = role.lower()
                    st.session_state.user_id = user['id']
                    st.session_state.tenant_id = user.get('tenant_id', 1)
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            except Exception as e:
                st.error(f"Login error: {e}")
            finally:
                conn.close()

def generate_report(report_type, start_date, end_date):
    """Generate report data based on type and date range"""
    conn = get_db_connection()
    if not conn:
        return None
        
    try:
        cursor = conn.cursor(dictionary=True)
        
        if report_type == "Client":
            query = """
                SELECT 
                    c.client_name,
                    COUNT(t.id) as total_trips,
                    SUM(t.amount) as total_billing
                FROM clients c
                LEFT JOIN trips t ON c.id = t.client_id
                WHERE t.trip_date BETWEEN %s AND %s
                GROUP BY c.id, c.client_name
            """
            cursor.execute(query, (start_date, end_date))
            data = cursor.fetchall()
            return pd.DataFrame(data)
            
        elif report_type == "Vendor":
            query = """
                SELECT 
                    v.vendor_name,
                    COUNT(t.id) as total_trips,
                    SUM(t.amount) as total_earnings
                FROM vendors v
                LEFT JOIN trips t ON v.id = t.vendor_id
                WHERE t.trip_date BETWEEN %s AND %s
                GROUP BY v.id, v.vendor_name
            """
            cursor.execute(query, (start_date, end_date))
            data = cursor.fetchall()
            return pd.DataFrame(data)
            
        elif report_type == "Employee":
            query = """
                SELECT 
                    e.employee_name,
                    COUNT(t.id) as total_trips,
                    SUM(t.commission) as total_commission
                FROM employees e
                LEFT JOIN trips t ON e.id = t.employee_id
                WHERE t.trip_date BETWEEN %s AND %s
                GROUP BY e.id, e.employee_name
            """
            cursor.execute(query, (start_date, end_date))
            data = cursor.fetchall()
            return pd.DataFrame(data)
            
        elif report_type == "Billing":
            query = """
                SELECT 
                    DATE_FORMAT(billing_date, '%Y-%m') as month,
                    COUNT(*) as total_invoices,
                    SUM(amount) as total_amount,
                    SUM(paid_amount) as total_paid
                FROM billing
                WHERE billing_date BETWEEN %s AND %s
                GROUP BY DATE_FORMAT(billing_date, '%Y-%m')
                ORDER BY month
            """
            cursor.execute(query, (start_date, end_date))
            data = cursor.fetchall()
            return pd.DataFrame(data)
            
    except Exception as e:
        st.error(f"Error generating report: {e}")
        return None
    finally:
        conn.close()

def vendor_dashboard():
    """Render the vendor dashboard"""
    # Call the new vendor dashboard implementation
    render_vendor_dashboard(st.session_state.username)
    
    # Keep the existing logout functionality
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

def employee_dashboard():
    """Render the employee dashboard"""
    st.title("Employee Dashboard")
    st.write(f"Welcome, {st.session_state.username}!")
    
    # Add metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Monthly Incentives", "$450")
    with col2:
        st.metric("Trips Completed", "38")
    
    # Incentive breakdown
    st.subheader("Incentive Breakdown")
    incentive_data = pd.DataFrame({
        'Category': ['Trip Completion', 'Customer Rating', 'Extra Hours'],
        'Amount': [320, 80, 50]
    })
    fig = px.pie(incentive_data, values='Amount', names='Category', title='Incentive Distribution')
    st.plotly_chart(fig)
    
    # Recent incentives
    st.subheader("Recent Incentives")
    recent_incentives = pd.DataFrame({
        'Date': ['2023-11-23', '2023-11-22', '2023-11-21'],
        'Type': ['Trip Bonus', 'Customer Rating', 'Overtime'],
        'Amount': [25.00, 15.00, 30.00]
    })
    st.dataframe(recent_incentives)
    
    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

def main():
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        login_section()
    else:
        # Show appropriate dashboard based on role
        if st.session_state.user_role == 'admin':
            show_admin_dashboard()
        elif st.session_state.user_role == 'vendor':
            vendor_dashboard()
        elif st.session_state.user_role == 'employee':
            employee_dashboard()
        else:
            st.error("Invalid user role")
            if st.button("Logout"):
                st.session_state.clear()
                st.rerun()

if __name__ == "__main__":
    main()