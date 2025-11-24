"""
[BACKEND] Core Business Logic (Billing/Reporting)
Handles billing operations, invoice generation, and reporting functionality.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from backend.database_connector import DatabaseConnector


class BillingAPI:
    """Core API for billing and reporting operations."""
    
    def __init__(self, db_connector: DatabaseConnector):
        """
        Initialize BillingAPI with database connector.
        
        Args:
            db_connector: DatabaseConnector instance for database operations
        """
        self.db = db_connector
        self.logger = logging.getLogger(__name__)
    
    def create_customer(self, name: str, email: str, phone: str, address: str) -> Optional[int]:
        """
        Create a new customer.
        
        Args:
            name: Customer name
            email: Customer email
            phone: Customer phone number
            address: Customer address
            
        Returns:
            Customer ID if successful, None otherwise
        """
        try:
            query = """
                INSERT INTO customers (name, email, phone, address, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            customer_id = self.db.execute_insert(
                query, (name, email, phone, address, datetime.now())
            )
            self.logger.info(f"Customer created: {name} (ID: {customer_id})")
            return customer_id
        except Exception as e:
            self.logger.error(f"Error creating customer: {str(e)}")
            return None
    
    def create_invoice(
        self, 
        customer_id: int, 
        items: List[Dict], 
        due_date: Optional[datetime] = None
    ) -> Optional[int]:
        """
        Create a new invoice with line items.
        
        Args:
            customer_id: ID of the customer
            items: List of items with 'description', 'quantity', 'unit_price'
            due_date: Optional due date (defaults to 30 days from now)
            
        Returns:
            Invoice ID if successful, None otherwise
        """
        try:
            if due_date is None:
                due_date = datetime.now() + timedelta(days=30)
            
            # Calculate total amount
            total_amount = sum(item['quantity'] * item['unit_price'] for item in items)
            
            # Create invoice
            invoice_query = """
                INSERT INTO invoices (customer_id, total_amount, due_date, status, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            invoice_id = self.db.execute_insert(
                invoice_query, 
                (customer_id, total_amount, due_date, 'pending', datetime.now())
            )
            
            # Create invoice items
            for item in items:
                item_query = """
                    INSERT INTO invoice_items (invoice_id, description, quantity, unit_price, total_price)
                    VALUES (%s, %s, %s, %s, %s)
                """
                total_price = item['quantity'] * item['unit_price']
                self.db.execute_insert(
                    item_query,
                    (invoice_id, item['description'], item['quantity'], 
                     item['unit_price'], total_price)
                )
            
            self.logger.info(f"Invoice created: ID {invoice_id} for customer {customer_id}")
            return invoice_id
        except Exception as e:
            self.logger.error(f"Error creating invoice: {str(e)}")
            return None
    
    def record_payment(
        self, 
        invoice_id: int, 
        amount: float, 
        payment_method: str = 'cash',
        payment_date: Optional[datetime] = None
    ) -> Optional[int]:
        """
        Record a payment for an invoice.
        
        Args:
            invoice_id: ID of the invoice
            amount: Payment amount
            payment_method: Payment method (cash, card, bank_transfer, etc.)
            payment_date: Payment date (defaults to now)
            
        Returns:
            Payment ID if successful, None otherwise
        """
        try:
            if payment_date is None:
                payment_date = datetime.now()
            
            # Record payment
            payment_query = """
                INSERT INTO payments (invoice_id, amount, payment_method, payment_date, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            payment_id = self.db.execute_insert(
                payment_query,
                (invoice_id, amount, payment_method, payment_date, datetime.now())
            )
            
            # Update invoice status
            invoice = self.get_invoice(invoice_id)
            if invoice:
                total_paid = self.get_total_paid(invoice_id)
                new_status = 'paid' if total_paid >= invoice['total_amount'] else 'partial'
                
                update_query = """
                    UPDATE invoices SET status = %s WHERE invoice_id = %s
                """
                self.db.execute_update(update_query, (new_status, invoice_id))
            
            self.logger.info(f"Payment recorded: ID {payment_id} for invoice {invoice_id}")
            return payment_id
        except Exception as e:
            self.logger.error(f"Error recording payment: {str(e)}")
            return None
    
    def get_customer(self, customer_id: int) -> Optional[Dict]:
        """Get customer details by ID."""
        query = "SELECT * FROM customers WHERE customer_id = %s"
        return self.db.fetch_one(query, (customer_id,))
    
    def get_invoice(self, invoice_id: int) -> Optional[Dict]:
        """Get invoice details by ID."""
        query = """
            SELECT i.*, c.name as customer_name, c.email as customer_email
            FROM invoices i
            JOIN customers c ON i.customer_id = c.customer_id
            WHERE i.invoice_id = %s
        """
        return self.db.fetch_one(query, (invoice_id,))
    
    def get_invoice_items(self, invoice_id: int) -> List[Dict]:
        """Get all items for an invoice."""
        query = "SELECT * FROM invoice_items WHERE invoice_id = %s"
        return self.db.fetch_all(query, (invoice_id,))
    
    def get_total_paid(self, invoice_id: int) -> float:
        """Get total amount paid for an invoice."""
        query = "SELECT COALESCE(SUM(amount), 0) as total FROM payments WHERE invoice_id = %s"
        result = self.db.fetch_one(query, (invoice_id,))
        return result['total'] if result else 0.0
    
    def get_all_customers(self) -> List[Dict]:
        """Get all customers."""
        query = "SELECT * FROM customers ORDER BY created_at DESC"
        return self.db.fetch_all(query)
    
    def get_customer_invoices(self, customer_id: int) -> List[Dict]:
        """Get all invoices for a customer."""
        query = """
            SELECT i.*, 
                   COALESCE(SUM(p.amount), 0) as total_paid,
                   (i.total_amount - COALESCE(SUM(p.amount), 0)) as balance_due
            FROM invoices i
            LEFT JOIN payments p ON i.invoice_id = p.invoice_id
            WHERE i.customer_id = %s
            GROUP BY i.invoice_id
            ORDER BY i.created_at DESC
        """
        return self.db.fetch_all(query, (customer_id,))
    
    def get_all_invoices(
        self, 
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Get all invoices with optional filters.
        
        Args:
            status: Filter by status (pending, partial, paid, overdue)
            start_date: Filter invoices from this date
            end_date: Filter invoices until this date
        """
        query = """
            SELECT i.*, 
                   c.name as customer_name,
                   COALESCE(SUM(p.amount), 0) as total_paid,
                   (i.total_amount - COALESCE(SUM(p.amount), 0)) as balance_due
            FROM invoices i
            JOIN customers c ON i.customer_id = c.customer_id
            LEFT JOIN payments p ON i.invoice_id = p.invoice_id
            WHERE 1=1
        """
        params = []
        
        if status:
            query += " AND i.status = %s"
            params.append(status)
        
        if start_date:
            query += " AND i.created_at >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND i.created_at <= %s"
            params.append(end_date)
        
        query += " GROUP BY i.invoice_id ORDER BY i.created_at DESC"
        
        return self.db.fetch_all(query, tuple(params) if params else None)
    
    def get_revenue_report(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict:
        """
        Generate revenue report for a date range.
        
        Returns:
            Dictionary with total_revenue, total_invoices, total_payments, etc.
        """
        try:
            # Total revenue (paid amount)
            revenue_query = """
                SELECT COALESCE(SUM(amount), 0) as total_revenue
                FROM payments
                WHERE payment_date BETWEEN %s AND %s
            """
            revenue_result = self.db.fetch_one(revenue_query, (start_date, end_date))
            total_revenue = revenue_result['total_revenue'] if revenue_result else 0.0
            
            # Total invoices created
            invoices_query = """
                SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total_amount
                FROM invoices
                WHERE created_at BETWEEN %s AND %s
            """
            invoices_result = self.db.fetch_one(invoices_query, (start_date, end_date))
            
            # Payments by method
            payments_by_method_query = """
                SELECT payment_method, COALESCE(SUM(amount), 0) as total
                FROM payments
                WHERE payment_date BETWEEN %s AND %s
                GROUP BY payment_method
            """
            payments_by_method = self.db.fetch_all(payments_by_method_query, (start_date, end_date))
            
            return {
                'start_date': start_date,
                'end_date': end_date,
                'total_revenue': total_revenue,
                'total_invoices': invoices_result['count'] if invoices_result else 0,
                'total_invoiced_amount': invoices_result['total_amount'] if invoices_result else 0.0,
                'payments_by_method': {p['payment_method']: p['total'] for p in payments_by_method},
                'outstanding_balance': invoices_result['total_amount'] - total_revenue if invoices_result else 0.0
            }
        except Exception as e:
            self.logger.error(f"Error generating revenue report: {str(e)}")
            return {}
    
    def update_invoice_status(self, invoice_id: int, status: str) -> bool:
        """Update invoice status."""
        try:
            query = "UPDATE invoices SET status = %s WHERE invoice_id = %s"
            self.db.execute_update(query, (status, invoice_id))
            return True
        except Exception as e:
            self.logger.error(f"Error updating invoice status: {str(e)}")
            return False
    
    def delete_customer(self, customer_id: int) -> bool:
        """Delete a customer (only if no invoices exist)."""
        try:
            # Check if customer has invoices
            invoice_check = "SELECT COUNT(*) as count FROM invoices WHERE customer_id = %s"
            result = self.db.fetch_one(invoice_check, (customer_id,))
            
            if result and result['count'] > 0:
                self.logger.warning(f"Cannot delete customer {customer_id}: has existing invoices")
                return False
            
            query = "DELETE FROM customers WHERE customer_id = %s"
            self.db.execute_update(query, (customer_id,))
            self.logger.info(f"Customer deleted: ID {customer_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting customer: {str(e)}")
            return False

