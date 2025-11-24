import streamlit as st
from streamlit_option_menu import option_menu
from backend.database_connector import db
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Unified Billing Platform",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

# Database functions
def get_table_data(table_name):
    with db.get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {table_name}")
        return cursor.fetchall()

def add_customer(name, email, phone, address):
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO customers (name, email, phone, address) VALUES (%s, %s, %s, %s)",
            (name, email, phone, address)
        )
        conn.commit()
        return cursor.lastrowid

# Authentication
def login(username, password):
    # In a real app, verify credentials against the database
    # This is a simple demo - replace with proper authentication
    if username == "admin" and password == "admin123":
        st.session_state.authenticated = True
        st.session_state.current_user = username
        return True
    return False

def logout():
    st.session_state.authenticated = False
    st.session_state.current_user = None

# Login page
def show_login():
    st.title("🔑 Login to Billing Platform")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if login(username, password):
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials")

# Dashboard
def show_dashboard():
    st.sidebar.title(f"👤 {st.session_state.current_user}")
    if st.sidebar.button("Logout"):
        logout()
        st.rerun()

    # Navigation
    menu = option_menu(
        menu_title=None,
        options=["Dashboard", "Invoices", "Customers", "Products"],
        icons=["house", "file-text", "people", "box"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal"
    )

    if menu == "Dashboard":
        st.title("📊 Dashboard")
        # Add dashboard widgets
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Customers", len(get_table_data("customers")))
        with col2:
            st.metric("Total Invoices", len(get_table_data("invoices")))
        with col3:
            st.metric("Total Products", len(get_table_data("products")))

    elif menu == "Invoices":
        st.title("📄 Invoices")
        invoices = get_table_data("invoices")
        st.dataframe(pd.DataFrame(invoices))

    elif menu == "Customers":
        st.title("👥 Customers")
        
        # Add new customer form
        with st.expander("➕ Add New Customer"):
            with st.form("add_customer"):
                name = st.text_input("Name")
                email = st.text_input("Email")
                phone = st.text_input("Phone")
                address = st.text_area("Address")
                if st.form_submit_button("Add Customer"):
                    if name and email:
                        add_customer(name, email, phone, address)
                        st.success("Customer added successfully!")
                        st.rerun()
        
        # Display customers table
        customers = get_table_data("customers")
        st.dataframe(pd.DataFrame(customers))

    elif menu == "Products":
        st.title("📦 Products")
        products = get_table_data("products")
        st.dataframe(pd.DataFrame(products))

# Main app
def main():
    if not st.session_state.authenticated:
        show_login()
    else:
        show_dashboard()

if __name__ == "__main__":
    main()
