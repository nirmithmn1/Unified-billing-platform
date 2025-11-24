# employee_dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
from backend.database import get_db_connection

def get_employee_metrics(employee_id, tenant_id):
    """Get employee metrics including trips and incentives"""
    conn = get_db_connection()
    if not conn:
        return {'trip_count': 0, 'total_incentives': 0.0}
    
    try:
        cursor = conn.cursor(dictionary=True)
        # Get current month's trips and incentives
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT t.id) as trip_count,
                COALESCE(SUM(i.amount), 0) as total_incentives
            FROM trips t
            LEFT JOIN incentives i ON t.id = i.trip_id AND i.user_id = %s
            WHERE t.user_id = %s
            AND MONTH(t.trip_date) = MONTH(CURRENT_DATE())
            AND t.tenant_id = %s
        """, (employee_id, employee_id, tenant_id))
        
        return cursor.fetchone() or {'trip_count': 0, 'total_incentives': 0.0}
    except Exception as e:
        st.error(f"Error fetching employee metrics: {e}")
        return {'trip_count': 0, 'total_incentives': 0.0}
    finally:
        if conn:
            conn.close()

def get_employee_incentives(employee_id, tenant_id):
    """Get detailed incentives for the employee"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        query = """
            SELECT 
                i.amount,
                i.reason,
                i.created_at,
                t.distance_km,
                t.duration_hours,
                bm.name as billing_model
            FROM incentives i
            JOIN trips t ON i.trip_id = t.id
            LEFT JOIN billing_models bm ON t.billing_model_id = bm.id
            WHERE i.user_id = %s
            AND i.tenant_id = %s
            ORDER BY i.created_at DESC
        """
        return pd.read_sql(query, conn, params=(employee_id, tenant_id))
    except Exception as e:
        st.error(f"Error fetching incentives: {e}")
        return None
    finally:
        if conn:
            conn.close()

def show_employee_dashboard():
    """Main employee dashboard function"""
    st.title("Employee Dashboard")
    st.write(f"Welcome, {st.session_state.username}!")
    
    # Get employee metrics
    employee_id = st.session_state.user_id
    tenant_id = st.session_state.tenant_id
    metrics = get_employee_metrics(employee_id, tenant_id)
    
    # Summary metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Trips This Month", metrics['trip_count'])
    with col2:
        st.metric("Total Incentives", f"${metrics['total_incentives']:,.2f}")
    
    # Incentive breakdown
    st.subheader("Incentive Breakdown")
    incentives = get_employee_incentives(employee_id, tenant_id)
    
    if incentives is not None and not incentives.empty:
        # Group incentives by reason
        incentive_summary = incentives.groupby('reason')['amount'].sum().reset_index()
        
        # Display pie chart
        if not incentive_summary.empty:
            fig = px.pie(
                incentive_summary,
                values='amount',
                names='reason',
                title='Incentives by Type',
                hole=0.3
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Display recent incentives
        st.subheader("Recent Incentives")
        recent_incentives = incentives[['created_at', 'amount', 'reason', 'billing_model']].head(5)
        recent_incentives = recent_incentives.rename(columns={
            'created_at': 'Date',
            'amount': 'Amount ($)',
            'reason': 'Reason',
            'billing_model': 'Billing Model'
        })
        st.dataframe(recent_incentives, use_container_width=True)
    else:
        st.info("No incentives found for this month.")
    
    # Add logout button
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.user_role = None
        st.session_state.username = None
        st.session_state.user_id = None
        st.session_state.tenant_id = None
        st.experimental_rerun()