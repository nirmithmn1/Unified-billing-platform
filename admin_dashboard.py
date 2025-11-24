# admin_dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import io
from dashboard_queries import (
    get_total_trips, get_total_revenue, get_active_billing_models_count,
    show_billing_models, get_recent_activity, get_vendors_list,
    get_employees_list, get_trips_summary, get_revenue_by_vendor,
    get_vendor_performance, get_employee_performance, get_users_list
)

def show_admin_dashboard():
    st.title("🚀 Admin Dashboard")
    
    # Navigation
    tabs = ["📊 Dashboard", "💰 Billing Models", "📈 Reports", "⚙️ Admin Controls"]
    selected_tab = st.sidebar.radio("Navigation", tabs)
    
    # Add Logout Button at the bottom of the sidebar
    st.sidebar.markdown("---")  # Add a separator
    
    # Add some space before the logout button
    st.sidebar.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
    
    # Logout button with full width
    logout_clicked = st.sidebar.button("🚪 Logout", width='stretch', key="logout_btn")
    
    # Add some space after the button
    st.sidebar.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    
    # Logout confirmation
    if 'show_logout_confirm' not in st.session_state:
        st.session_state.show_logout_confirm = False
    
    if logout_clicked:
        st.session_state.show_logout_confirm = True
    
    if st.session_state.show_logout_confirm:
        st.sidebar.warning("Are you sure you want to logout?")
        col1, col2 = st.sidebar.columns(2)
        if col1.button("Yes, Logout", type="primary"):
            # Clear all session state variables
            st.session_state.clear()
            st.rerun()
        if col2.button("Cancel"):
            st.session_state.show_logout_confirm = False
            st.rerun()
    
    # Date range selector
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(start_date, end_date),
        min_value=end_date - timedelta(days=365),
        max_value=end_date
    )
    
    if len(date_range) == 2:
        start_date, end_date = date_range
    
    # Dashboard Tab
    if selected_tab == "📊 Dashboard":
        show_dashboard_metrics(start_date, end_date)
    
    # Billing Models Tab
    elif selected_tab == "💰 Billing Models":
        show_billing_models_section()
    
    # Reports Tab
    elif selected_tab == "📈 Reports":
        show_reports_section(start_date, end_date)
    
    # Admin Controls Tab
    elif selected_tab == "⚙️ Admin Controls":
        show_admin_controls()

def show_dashboard_metrics(start_date, end_date):
    # Summary metrics
    st.subheader("📊 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Trips", get_total_trips())
    with col2:
        st.metric("Total Revenue", f"₹{get_total_revenue():,.2f}")
    with col3:
        st.metric("Active Billing Models", get_active_billing_models_count())
    with col4:
        st.metric("Active Vendors", len(get_vendors_list()))
    
    # Revenue and Trips Trend
    st.subheader("📈 Revenue & Trips Trend")
    show_trends(start_date, end_date)
    
    # Recent Activity
    st.subheader("🔄 Recent Activity")
    activities = get_recent_activity()
    if activities:
        st.dataframe(pd.DataFrame(activities),width='stretch')
    else:
        st.info("No recent activity found.")

def show_billing_models_section():
    st.subheader("💰 Billing Models")
    
    # Add new billing model
    with st.expander("➕ Add New Billing Model"):
        with st.form("billing_model_form"):
            model_name = st.text_input("Model Name")
            model_type = st.selectbox("Type", ["Fixed Rate", "Tiered", "Dynamic"])
            rate = st.number_input("Rate", min_value=0.0, step=0.01)
            is_active = st.checkbox("Active", value=True)
            
            if st.form_submit_button("Save Model"):
                # Add logic to save the billing model
                st.success(f"Billing model '{model_name}' added successfully!")
    
    # List existing billing models
    st.subheader("Existing Billing Models")
    models = show_billing_models()
    if models is not None and not models.empty:
        st.data_editor(
            models,
            column_config={
                "is_active": st.column_config.CheckboxColumn("Active")
            },
            width='stretch',
            hide_index=True
        )
    else:
        st.info("No billing models found.")

def show_reports_section(start_date, end_date):
    st.subheader("📊 Generate Reports")
    
    # Report type selection
    report_type = st.selectbox(
        "Select Report Type",
        ["Revenue Report", "Trip Summary", "Vendor Performance", "Employee Performance"]
    )
    
    # Date range display
    st.caption(f"Showing data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Generate and display report
    if st.button("Generate Report"):
        with st.spinner("Generating report..."):
            if report_type == "Revenue Report":
                show_revenue_report(start_date, end_date)
            elif report_type == "Trip Summary":
                show_trip_summary(start_date, end_date)
            elif report_type == "Vendor Performance":
                show_vendor_performance(start_date, end_date)
            else:  # Employee Performance
                show_employee_performance(start_date, end_date)

def show_admin_controls():
    st.subheader("⚙️ System Configuration")
    
    # System Settings
    with st.expander("System Settings"):
        st.number_input("Session Timeout (minutes)", min_value=5, max_value=120, value=30)
        st.number_input("Max Login Attempts", min_value=1, max_value=10, value=3)
        st.checkbox("Enable Email Notifications", value=True)
        
        if st.button("Save Settings"):
            st.success("System settings updated successfully!")
    
    # User Management
    st.subheader("👥 User Management")
    user_action = st.radio("Action", ["View Users", "Add User", "Reset Password"])
    
    if user_action == "View Users":
        show_user_list()
    elif user_action == "Add User":
        show_add_user_form()
    else:  # Reset Password
        show_reset_password_form()

def show_trends(start_date, end_date):
    # Sample data - replace with actual data from your database
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    trend_data = pd.DataFrame({
        'date': date_range,
        'revenue': [1000 + i * 50 + (i * 10) for i in range(len(date_range))],
        'trips': [10 + i for i in range(len(date_range))]
    })
    
    # Create a figure with secondary y-axis
    fig = px.line(trend_data, x='date', y=['revenue', 'trips'],
                 labels={'value': 'Count/Amount', 'date': 'Date'},
                 title='Revenue & Trips Trend')
    
    # Update layout
    fig.update_layout(
        hovermode='x unified',
        yaxis_title='Count/Amount',
        legend_title='Metrics',
        xaxis=dict(rangeslider=dict(visible=True))
    )
    
    st.plotly_chart(fig, width='stretch')

def show_revenue_report(start_date, end_date):
    # Sample data - replace with actual data from your database
    revenue_data = get_revenue_by_vendor(start_date, end_date)
    
    if not revenue_data.empty:
        # Display summary metrics
        total_revenue = revenue_data['revenue'].sum()
        avg_revenue = revenue_data['revenue'].mean()
        
        col1, col2 = st.columns(2)
        col1.metric("Total Revenue", f"₹{total_revenue:,.2f}")
        col2.metric("Average Revenue per Vendor", f"₹{avg_revenue:,.2f}")
        
        # Display data table
        st.dataframe(revenue_data, width='stretch')
        
        # Export options
        export_format = st.radio("Export Format", ["CSV", "Excel"])
        if st.button("Export Report"):
            output = io.BytesIO()
            if export_format == "CSV":
                csv = revenue_data.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Download CSV",
                    data=csv,
                    file_name=f"revenue_report_{start_date}_to_{end_date}.csv",
                    mime="text/csv"
                )
            else:  # Excel
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    revenue_data.to_excel(writer, index=False, sheet_name='Revenue Report')
                st.download_button(
                    "Download Excel",
                    data=output.getvalue(),
                    file_name=f"revenue_report_{start_date}_to_{end_date}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    else:
        st.warning("No revenue data available for the selected period.")

def show_trip_summary(start_date, end_date):
    # Get trip summary data
    trip_data = get_trips_summary(start_date, end_date)
    
    if not trip_data.empty:
        # Display metrics
        total_trips = trip_data['trip_count'].sum()
        avg_fare = trip_data['avg_fare'].mean()
        
        col1, col2 = st.columns(2)
        col1.metric("Total Trips", f"{total_trips:,}")
        col2.metric("Average Fare", f"₹{avg_fare:,.2f}")
        
        # Display data table
        st.dataframe(trip_data, width='stretch')
    else:
        st.warning("No trip data available for the selected period.")

def show_vendor_performance(start_date, end_date):
    # Get vendor performance data
    vendor_data = get_vendor_performance(start_date, end_date)
    
    if not vendor_data.empty:
        # Display metrics
        top_vendor = vendor_data.loc[vendor_data['revenue'].idxmax()]
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Top Performing Vendor", top_vendor['vendor_name'])
        col2.metric("Highest Revenue", f"₹{top_vendor['revenue']:,.2f}")
        col3.metric("Total Trips", f"{vendor_data['trip_count'].sum():,}")
        
        # Display data table
        st.dataframe(vendor_data, width='stretch')
    else:
        st.warning("No vendor performance data available for the selected period.")

def show_employee_performance(start_date, end_date):
    # Get employee performance data
    employee_data = get_employee_performance(start_date, end_date)
    
    if not employee_data.empty:
        # Display metrics
        top_employee = employee_data.loc[employee_data['trip_count'].idxmax()]
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Top Performing Employee", top_employee['employee_name'])
        col2.metric("Trips Completed", top_employee['trip_count'])
        col3.metric("Total Incentives", f"₹{employee_data['incentives'].sum():,.2f}")
        
        # Display data table
        st.dataframe(employee_data, width='stretch')
    else:
        st.warning("No employee performance data available for the selected period.")

def show_user_list():
    # Get users from database
    users = get_users_list()
    
    if not users.empty:
        st.dataframe(
            users[['username', 'email', 'role', 'last_login', 'is_active']],
            column_config={
                "is_active": st.column_config.CheckboxColumn("Active")
            },
            width='stretch',
            hide_index=True
        )
    else:
        st.info("No users found.")

def show_add_user_form():
    with st.form("add_user_form"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        role = st.selectbox("Role", ["admin", "vendor", "employee"])
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        if st.form_submit_button("Add User"):
            if password != confirm_password:
                st.error("Passwords do not match!")
            else:
                # Add user to database
                st.success(f"User '{username}' added successfully!")

def show_reset_password_form():
    users = get_users_list()
    
    if not users.empty:
        username = st.selectbox("Select User", users['username'].tolist())
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        if st.button("Reset Password"):
            if new_password != confirm_password:
                st.error("Passwords do not match!")
            else:
                # Update password in database
                st.success(f"Password for '{username}' has been reset successfully!")
    else:
        st.warning("No users found.")

# This allows the file to be run directly for testing
if __name__ == "__main__":
    show_admin_dashboard()