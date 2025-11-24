import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os


# Load environment variables
load_dotenv()

def get_db_connection():
    """Create and return a SQLAlchemy database engine"""
    load_dotenv()
    try:
        db_url = f"mysql+mysqlconnector://{os.getenv('DB_USER', 'root')}:{os.getenv('DB_PASSWORD', '')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', 3306)}/{os.getenv('DB_NAME', 'billing_platform')}"
        engine = create_engine(db_url)
        return engine
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None

def get_vendor_id(username):
    """Get vendor ID from username/email"""
    engine = get_db_connection()
    if not engine:
        return None
    
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT v.id 
                    FROM vendors v
                    JOIN users u ON v.email = u.email
                    WHERE u.username = :username 
                    LIMIT 1
                """),
                {'username': username}
            ).fetchone()
            return result[0] if result else None
    except Exception as e:
        st.error(f"Error fetching vendor ID: {e}")
        return None

def get_vendor_trips(vendor_id, start_date, end_date, status_filter=None):
    """Get trips for a vendor with filtering and pagination"""
    engine = get_db_connection()
    if not engine:
        return {'trips': [], 'total': 0, 'page': 1, 'page_size': 10, 'total_pages': 0}
    
    try:
        with engine.connect() as conn:
            # Calculate pagination
            page_size = 10
            page = st.session_state.get('trip_page', 1)
            offset = (page - 1) * page_size
            
            # Base query
            query = """
                SELECT 
                    t.id as trip_id,
                    t.trip_date,
                    c.name as client_name,
                    t.distance_km,
                    t.duration_hours,
                    b.amount as trip_fare,
                    b.status as payment_status,
                    t.status as trip_status,
                    b.payment_date
                FROM trips t
                JOIN billing b ON t.id = b.trip_id
                JOIN clients c ON t.client_id = c.id
                WHERE t.vendor_id = :vendor_id 
                AND DATE(t.trip_date) BETWEEN :start_date AND :end_date
                {status_condition}
                ORDER BY t.trip_date DESC
                LIMIT :limit OFFSET :offset
            """
            
            # Add status filter if provided
            params = {
                'vendor_id': vendor_id,
                'start_date': start_date,
                'end_date': end_date,
                'limit': page_size,
                'offset': offset
            }
            
            status_condition = ""
            if status_filter:
                # Create a list of named parameters for each status
                status_params = {f'status_{i}': status for i, status in enumerate(status_filter)}
                status_condition = "AND t.status IN (" + ", ".join(f":{param}" for param in status_params.keys()) + ")"
                params.update(status_params)
            
            # Execute query with pagination
            query = query.format(status_condition=status_condition)
            result = conn.execute(text(query), params)
            trips = [dict(row) for row in result.mappings()]
            
            # Get total count for pagination
            count_query = f"""
                SELECT COUNT(*) as total 
                FROM trips t
                JOIN billing b ON t.id = b.trip_id
                WHERE t.vendor_id = :vendor_id 
                AND DATE(t.trip_date) BETWEEN :start_date AND :end_date
                {status_condition}
            """
            
            count_params = {
                'vendor_id': vendor_id,
                'start_date': start_date,
                'end_date': end_date
            }
            
            if status_filter:
                # Use the same status parameters for the count query
                count_params.update(status_params)
                
            total_trips = conn.execute(text(count_query), count_params).scalar()
            
            return {
                'trips': trips,
                'total': total_trips,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_trips + page_size - 1) // page_size if total_trips > 0 else 1
            }
            
    except Exception as e:
        st.error(f"Error fetching trips: {e}")
        return {'trips': [], 'total': 0, 'page': 1, 'page_size': 10, 'total_pages': 1}

def calculate_earnings(trips_data, vendor_id, start_date, end_date):
    """Calculate earnings with detailed breakdown"""
    engine = get_db_connection()
    if not engine:
        return {
            'weekly_earnings': pd.DataFrame(),
            'status_breakdown': pd.DataFrame(),
            'recent_transactions': pd.DataFrame()
        }
    
    try:
        with engine.connect() as conn:
            # Weekly earnings
            weekly_query = """
                SELECT 
                    DATE_FORMAT(t.trip_date, '%Y-%u') as week,
                    SUM(b.amount) as total_earnings,
                    COUNT(t.id) as trip_count
                FROM trips t
                JOIN billing b ON t.id = b.trip_id
                WHERE t.vendor_id = :vendor_id
                AND DATE(t.trip_date) BETWEEN :start_date AND :end_date
                GROUP BY week
                ORDER BY week
            """
            weekly_earnings = pd.read_sql(
                text(weekly_query), 
                conn,
                params={'vendor_id': vendor_id, 'start_date': start_date, 'end_date': end_date}
            )
            
            # Payment status breakdown
            status_query = """
                SELECT 
                    b.status as payment_status,
                    COUNT(t.id) as trip_count,
                    SUM(b.amount) as total_amount
                FROM trips t
                JOIN billing b ON t.id = b.trip_id
                WHERE t.vendor_id = :vendor_id
                AND DATE(t.trip_date) BETWEEN :start_date AND :end_date
                GROUP BY b.status
            """
            status_breakdown = pd.read_sql(
                text(status_query),
                conn,
                params={'vendor_id': vendor_id, 'start_date': start_date, 'end_date': end_date}
            )
            
            # Recent transactions
            recent_query = """
                SELECT 
                    t.id as trip_id,
                    t.trip_date,
                    c.name as client_name,
                    b.amount,
                    b.status as payment_status
                FROM trips t
                JOIN billing b ON t.id = b.trip_id
                JOIN clients c ON t.client_id = c.id
                WHERE t.vendor_id = :vendor_id
                ORDER BY t.trip_date DESC
                LIMIT 5
            """
            recent_transactions = pd.read_sql(
                text(recent_query),
                conn,
                params={'vendor_id': vendor_id}
            )
            
            return {
                'weekly_earnings': weekly_earnings,
                'status_breakdown': status_breakdown,
                'recent_transactions': recent_transactions
            }
            
    except Exception as e:
        st.error(f"Error calculating earnings: {e}")
        return {
            'weekly_earnings': pd.DataFrame(),
            'status_breakdown': pd.DataFrame(),
            'recent_transactions': pd.DataFrame()
        }

def calculate_incentives(vendor_id, start_date, end_date):
    """Calculate incentives based on vendor performance"""
    engine = get_db_connection()
    if not engine:
        return {
            'total_incentives': 0,
            'incentive_breakdown': pd.DataFrame(),
            'eligible_trips': pd.DataFrame(),
            'rules': {}
        }
    
    try:
        with engine.connect() as conn:
            # Incentive rules configuration
            incentive_rules = {
                'high_volume': {
                    'threshold': 20,  # trips
                    'bonus_per_trip': 5.00
                },
                'long_distance': {
                    'threshold_km': 15.0,  # km
                    'bonus_percent': 0.05  # 5% of fare
                },
                'quick_completion': {
                    'max_hours': 0.5,  # hours
                    'bonus_percent': 0.03  # 3% of fare
                }
            }
            
            # Get trips for the period
            query = """
                SELECT 
                    t.id as trip_id,
                    t.trip_date,
                    t.distance_km,
                    t.duration_hours,
                    b.amount as fare,
                    b.status as payment_status
                FROM trips t
                JOIN billing b ON t.id = b.trip_id
                WHERE t.vendor_id = :vendor_id
                AND DATE(t.trip_date) BETWEEN :start_date AND :end_date
                AND b.status = 'paid'
            """
            
            trips = pd.read_sql(
                text(query),
                conn,
                params={
                    'vendor_id': vendor_id,
                    'start_date': start_date,
                    'end_date': end_date
                }
            )
            
            if trips.empty:
                return {
                    'total_incentives': 0,
                    'incentive_breakdown': pd.DataFrame(),
                    'eligible_trips': pd.DataFrame(),
                    'rules': incentive_rules
                }
            
            # Apply incentive rules
            incentives = []
            eligible_trips = []
            
            # High volume bonus
            if len(trips) >= incentive_rules['high_volume']['threshold']:
                bonus = incentive_rules['high_volume']['bonus_per_trip'] * len(trips)
                incentives.append({
                    'type': 'High Volume Bonus',
                    'amount': bonus,
                    'description': f"Bonus for completing {len(trips)} trips"
                })
            
            # Long distance and quick completion bonuses
            for _, trip in trips.iterrows():
                trip_bonus = 0
                bonuses = []
                
                # Long distance bonus
                if trip['distance_km'] > incentive_rules['long_distance']['threshold_km']:
                    bonus = trip['fare'] * incentive_rules['long_distance']['bonus_percent']
                    trip_bonus += bonus
                    bonuses.append(f"Long distance (+${bonus:.2f})")
                
                # Quick completion bonus
                if trip['duration_hours'] < incentive_rules['quick_completion']['max_hours']:
                    bonus = trip['fare'] * incentive_rules['quick_completion']['bonus_percent']
                    trip_bonus += bonus
                    bonuses.append(f"Quick completion (+${bonus:.2f})")
                
                if bonuses:
                    eligible_trips.append({
                        'trip_id': trip['trip_id'],
                        'trip_date': trip['trip_date'],
                        'bonus_amount': trip_bonus,
                        'bonus_details': ', '.join(bonuses)
                    })
            
            # Calculate total incentives
            total_incentives = sum(incentive['amount'] for incentive in incentives) + \
                            sum(trip['bonus_amount'] for trip in eligible_trips)
            
            # Create DataFrames for display
            incentive_breakdown = pd.DataFrame(incentives) if incentives else pd.DataFrame(
                columns=['type', 'amount', 'description'])
            eligible_trips_df = pd.DataFrame(eligible_trips) if eligible_trips else pd.DataFrame(
                columns=['trip_id', 'trip_date', 'bonus_amount', 'bonus_details'])
            
            return {
                'total_incentives': total_incentives,
                'incentive_breakdown': incentive_breakdown,
                'eligible_trips': eligible_trips_df,
                'rules': incentive_rules
            }
            
    except Exception as e:
        st.error(f"Error calculating incentives: {e}")
        return {
            'total_incentives': 0,
            'incentive_breakdown': pd.DataFrame(),
            'eligible_trips': pd.DataFrame(),
            'rules': {}
        }

def render_vendor_dashboard(username):
    """Render the vendor dashboard with all features"""
    st.title("Vendor Dashboard")
    
    # Get vendor ID
    vendor_id = get_vendor_id(username)
    if not vendor_id:
        st.error("Vendor not found. Please contact support.")
        return
    
    # Date range selection
    st.sidebar.header("Date Range")
    today = datetime.now().date()
    default_end = today
    default_start = today - timedelta(days=30)  # Last 30 days by default
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input("Start Date", default_start)
    with col2:
        end_date = st.date_input("End Date", default_end)
    
    if start_date > end_date:
        st.error("Error: Start date must be before end date.")
        return
    
    # Trip status filter
    status_options = ['scheduled', 'in_progress', 'completed', 'cancelled']
    selected_status = st.sidebar.multiselect(
        "Filter by Status",
        options=status_options,
        default=['completed']
    )
    
    # Load data
    with st.spinner("Loading data..."):
        # Get trips with pagination
        trips_data = get_vendor_trips(
            vendor_id, 
            start_date, 
            end_date,
            status_filter=selected_status if selected_status else None
        )
        
        # Calculate earnings
        earnings_data = calculate_earnings(
            trips_data,  # Add trips_data as first parameter
            vendor_id, 
            start_date, 
            end_date
        )
        
        # Calculate incentives
        incentives_data = calculate_incentives(
            vendor_id,
            start_date,
            end_date
        )
    
    # Dashboard Header
    st.header(f"Welcome, {username}!")
    
    # Key Metrics
    st.subheader("📊 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_earnings = earnings_data['status_breakdown']['total_amount'].sum()
        st.metric("Total Earnings", f"${total_earnings:,.2f}")
    with col2:
        total_trips = trips_data['total']
        st.metric("Total Trips", total_trips)
    with col3:
        completed_trips = len([t for t in trips_data['trips'] 
                             if t['trip_status'] == 'completed'])
        st.metric("Completed Trips", completed_trips)
    with col4:
        st.metric("Total Incentives", f"${incentives_data['total_incentives']:,.2f}")
    
    # Earnings Overview
    st.subheader("💵 Earnings Overview")
    if not earnings_data['weekly_earnings'].empty:
        # Weekly Earnings Chart
        fig = px.line(
            earnings_data['weekly_earnings'],
            x='week',
            y='total_earnings',
            title='Weekly Earnings Trend',
            labels={'week': 'Week', 'total_earnings': 'Earnings ($)'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Payment Status Distribution
        col1, col2 = st.columns(2)
        with col1:
            if not earnings_data['status_breakdown'].empty:
                fig = px.pie(
                    earnings_data['status_breakdown'],
                    values='total_amount',
                    names='payment_status',
                    title='Payment Status Distribution',
                    hole=0.4
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Recent Transactions
        with col2:
            st.subheader("Recent Transactions")
            if not earnings_data['recent_transactions'].empty:
                st.dataframe(
                    earnings_data['recent_transactions'],
                    column_config={
                        "trip_date": "Date",
                        "client_name": "Client",
                        "amount": st.column_config.NumberColumn("Amount", format="$%.2f"),
                        "payment_status": "Status"
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("No recent transactions found.")
    else:
        st.info("No earnings data available for the selected period.")
    
    # Incentives Section
    st.subheader("🎯 Incentives")
    if not incentives_data['incentive_breakdown'].empty:
        # Incentive Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Incentives", 
                     f"${incentives_data['total_incentives']:,.2f}")
        with col2:
            st.metric("Eligible Trips", 
                     len(incentives_data['eligible_trips']))
        with col3:
            avg_incentive = (incentives_data['total_incentives'] / 
                            len(incentives_data['eligible_trips']) 
                            if len(incentives_data['eligible_trips']) > 0 else 0)
            st.metric("Avg. Incentive per Trip", 
                     f"${avg_incentive:,.2f}")
        
        # Incentive Breakdown
        st.subheader("Incentive Breakdown")
        st.dataframe(
            incentives_data['incentive_breakdown'],
            column_config={
                "type": "Incentive Type",
                "amount": st.column_config.NumberColumn("Amount", format="$%.2f"),
                "description": "Description"
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Eligible Trips
        if not incentives_data['eligible_trips'].empty:
            st.subheader("Eligible Trips for Bonuses")
            st.dataframe(
                incentives_data['eligible_trips'],
                column_config={
                    "date": "Date",
                    "distance_km": st.column_config.NumberColumn("Distance (km)", format="%.1f"),
                    "duration_hours": st.column_config.NumberColumn("Duration (hrs)", format="%.2f"),
                    "fare": st.column_config.NumberColumn("Fare", format="$%.2f"),
                    "bonus_amount": st.column_config.NumberColumn("Bonus", format="$%.2f"),
                    "bonus_details": "Bonus Details"
                },
                hide_index=True,
                use_container_width=True
            )
    else:
        st.info("No incentives earned for the selected period.")
    
    # Trip History
    st.subheader("📋 Trip History")
    
    # Search and filter
    search_term = st.text_input("Search trips by client name or ID", "")
    
    # Apply search filter
    filtered_trips = trips_data['trips']
    if search_term:
        search_term = search_term.lower()
        filtered_trips = [
            t for t in filtered_trips 
            if (search_term in str(t['client_name']).lower() or 
                search_term in str(t['trip_id']).lower())
        ]
    
    # Display trips with pagination
    if filtered_trips:
        # Convert to DataFrame for display
        trips_df = pd.DataFrame(filtered_trips)
        
        # Format columns
        trips_df['trip_date'] = pd.to_datetime(trips_df['trip_date']).dt.strftime('%Y-%m-%d %H:%M')
        trips_df['duration_hours'] = trips_df['duration_hours'].round(2)
        
        # Display data table
        st.dataframe(
            trips_df[['trip_id', 'trip_date', 'client_name', 'distance_km', 
                     'duration_hours', 'trip_fare', 'trip_status', 'payment_status']],
            column_config={
                "trip_id": "Trip ID",
                "trip_date": "Date & Time",
                "client_name": "Client",
                "distance_km": st.column_config.NumberColumn("Distance (km)", format="%.1f"),
                "duration_hours": st.column_config.NumberColumn("Duration (hrs)", format="%.2f"),
                "trip_fare": st.column_config.NumberColumn("Fare", format="$%.2f"),
                "trip_status": "Status",
                "payment_status": "Payment"
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Pagination controls
        if trips_data['total_pages'] > 1:
            st.write(f"Page {trips_data['page']} of {trips_data['total_pages']}")
            col1, col2, _ = st.columns([1, 1, 3])
            with col1:
                if st.button("Previous", disabled=trips_data['page'] <= 1):
                    st.session_state.trip_page = max(1, trips_data['page'] - 1)
                    st.rerun()
            with col2:
                if st.button("Next", disabled=trips_data['page'] >= trips_data['total_pages']):
                    st.session_state.trip_page = min(trips_data['total_pages'], trips_data['page'] + 1)
                    st.rerun()
        
        # Export button
        csv = trips_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Export to CSV",
            data=csv,
            file_name=f"trips_{start_date}_to_{end_date}.csv",
            mime="text/csv"
        )
    else:
        st.info("No trips found for the selected criteria.")
    
    # Add some space at the bottom
    st.write("")  # Empty line for spacing

# Main function to run the dashboard
if __name__ == "__main__":
    # For testing
    st.set_page_config(layout="wide")
    render_vendor_dashboard("test_vendor")