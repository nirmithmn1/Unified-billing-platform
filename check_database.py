def check_dashboard_requirements():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        print("\n🔍 Checking dashboard requirements...")
        
        # 1. Check Admin Dashboard requirements
        print("\n📊 Admin Dashboard:")
        # Check trips summary
        cursor.execute("SELECT COUNT(*) as total_trips, SUM(total_fare) as total_revenue FROM trips")
        trips = cursor.fetchone()
        print(f"  • Total Trips: {trips['total_trips'] or 0}")
        print(f"  • Total Revenue: ${trips['total_revenue'] or 0:.2f}")
        
        # Check billing models
        cursor.execute("SELECT COUNT(*) as model_count FROM billing_models")
        models = cursor.fetchone()
        print(f"  • Billing Models: {models['model_count']}")
        
        # 2. Check Vendor Dashboard requirements
        print("\n🏪 Vendor Dashboard:")
        cursor.execute("""
            SELECT 
                COUNT(*) as completed_trips,
                SUM(total_fare) as total_earnings
            FROM trips 
            WHERE status = 'completed'
        """)
        vendor_stats = cursor.fetchone()
        print(f"  • Completed Trips: {vendor_stats['completed_trips'] or 0}")
        print(f"  • Total Earnings: ${vendor_stats['total_earnings'] or 0:.2f}")
        
        # 3. Check Employee Dashboard requirements
        print("\n👥 Employee Dashboard:")
        cursor.execute("""
            SELECT 
                COUNT(*) as total_trips,
                AVG(total_fare) as avg_trip_value
            FROM trips
            WHERE created_by IS NOT NULL
        """)
        employee_stats = cursor.fetchone()
        print(f"  • Total Trips by Employees: {employee_stats['total_trips'] or 0}")
        print(f"  • Average Trip Value: ${employee_stats['avg_trip_value'] or 0:.2f}")
        
        # 4. Check for required tables and columns
        required_tables = ['trips', 'billing_models', 'users', 'customers', 'payments']
        missing_tables = []
        
        for table in required_tables:
            cursor.execute(f"SHOW TABLES LIKE '{table}'")
            if not cursor.fetchone():
                missing_tables.append(table)
        
        if missing_tables:
            print("\n❌ Missing required tables:", ", ".join(missing_tables))
            return False
        
        print("\n✅ All dashboard requirements checked successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error checking dashboard requirements: {e}")
        return False
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def main():
    print("🔍 Starting database check...")
    
    # Check basic database connection and structure
    if not check_database():
        print("\n❌ Database check failed. Please fix the issues above.")
        return
    
    # Check dashboard requirements
    if not check_dashboard_requirements():
        print("\n⚠️ Some dashboard features may not work as expected.")
    
    print("\n✅ Database check completed!")

if __name__ == "__main__":
    main()