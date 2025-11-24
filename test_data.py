from dashboard_queries import get_db_connection

def add_test_incentives():
    test_data = [
        (1, 100.00, "Outstanding performance"),
        (1, 50.00, "Customer satisfaction"),
        (2, 75.00, "On-time delivery"),
        (1, 200.00, "Top performer of the month")
    ]
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT INTO incentives (employee_id, incentive_amount, reason)
            VALUES (%s, %s, %s)
        """, test_data)
        conn.commit()
        print(f"Added {len(test_data)} test incentive records.")

if __name__ == "__main__":
    add_test_incentives()