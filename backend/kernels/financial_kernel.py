"""
Financial Kernel (The "Ledger")
Universal financial management and billing engine
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from kernels.base_kernel import BaseKernel


class FinancialKernel(BaseKernel):
    """Universal financial management system"""
    
    async def _initialize_kernel(self):
        """Initialize financial kernel"""
        # Ensure indexes exist
        await self.db.invoices.create_index([("tenant_id", 1), ("status", 1)])
        await self.db.line_items.create_index([("tenant_id", 1), ("invoice_id", 1)])
        await self.db.transactions.create_index([("tenant_id", 1), ("transaction_date", -1)])
        await self.db.subscriptions.create_index([("tenant_id", 1), ("customer_id", 1)])
        await self.db.products.create_index([("tenant_id", 1), ("is_active", 1)])
    
    async def validate_tenant_access(self, tenant_id: str, user_id: str) -> bool:
        """Validate user belongs to tenant"""
        user = await self.db.users.find_one({"id": user_id, "tenant_id": tenant_id})
        return user is not None
    
    # Product/Service Management
    async def create_product(self, tenant_id: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new product/service"""
        product_doc = {
            **product_data,
            "tenant_id": tenant_id,
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        await self.db.products.insert_one(product_doc)
        return product_doc
    
    async def get_products(self, tenant_id: str, is_active: bool = True) -> List[Dict[str, Any]]:
        """Get products for tenant"""
        query = {"tenant_id": tenant_id, "is_active": is_active}
        products = await self.db.products.find(query).to_list(1000)
        return products
    
    # Invoice Management
    async def create_invoice(self, tenant_id: str, customer_id: str, line_items: List[Dict[str, Any]], 
                           due_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Create a new invoice"""
        # Calculate totals
        subtotal = sum(Decimal(str(item["quantity"])) * Decimal(str(item["unit_price"])) for item in line_items)
        tax_amount = subtotal * Decimal("0.0")  # Default no tax, can be configured per tenant
        total_amount = subtotal + tax_amount
        
        invoice_doc = {
            "id": self._generate_invoice_id(),
            "tenant_id": tenant_id,
            "customer_id": customer_id,
            "subtotal": float(subtotal),
            "tax_amount": float(tax_amount),
            "total_amount": float(total_amount),
            "status": "draft",
            "due_date": due_date or (datetime.utcnow() + timedelta(days=30)),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await self.db.invoices.insert_one(invoice_doc)
        
        # Create line items
        for item in line_items:
            line_item_doc = {
                **item,
                "id": f"li_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{len(line_items)}",
                "tenant_id": tenant_id,
                "invoice_id": invoice_doc["id"],
                "line_total": float(Decimal(str(item["quantity"])) * Decimal(str(item["unit_price"]))),
                "created_at": datetime.utcnow()
            }
            await self.db.line_items.insert_one(line_item_doc)
        
        return invoice_doc
    
    def _generate_invoice_id(self) -> str:
        """Generate unique invoice ID"""
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        return f"INV-{timestamp}"
    
    async def get_invoices(self, tenant_id: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get invoices for tenant"""
        query = {"tenant_id": tenant_id}
        if filters:
            query.update(filters)
        
        invoices = await self.db.invoices.find(query).sort("created_at", -1).to_list(1000)
        
        # Attach line items to each invoice
        for invoice in invoices:
            line_items = await self.db.line_items.find({"invoice_id": invoice["id"]}).to_list(100)
            invoice["line_items"] = line_items
        
        return invoices
    
    async def update_invoice_status(self, invoice_id: str, status: str) -> bool:
        """Update invoice status"""
        valid_statuses = ["draft", "sent", "paid", "overdue", "cancelled"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        
        result = await self.db.invoices.update_one(
            {"id": invoice_id},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    
    # Transaction Management
    async def create_transaction(self, tenant_id: str, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record a new transaction"""
        transaction_doc = {
            **transaction_data,
            "tenant_id": tenant_id,
            "transaction_date": transaction_data.get("transaction_date", datetime.utcnow()),
            "created_at": datetime.utcnow()
        }
        await self.db.transactions.insert_one(transaction_doc)
        return transaction_doc
    
    async def get_transactions(self, tenant_id: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get transactions for tenant"""
        query = {"tenant_id": tenant_id}
        if filters:
            query.update(filters)
        
        transactions = await self.db.transactions.find(query).sort("transaction_date", -1).to_list(1000)
        return transactions
    
    # Subscription Management
    async def create_subscription(self, tenant_id: str, subscription_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a recurring subscription"""
        subscription_doc = {
            **subscription_data,
            "tenant_id": tenant_id,
            "status": "active",
            "created_at": datetime.utcnow(),
            "next_billing_date": subscription_data.get("start_date", datetime.utcnow())
        }
        await self.db.subscriptions.insert_one(subscription_doc)
        return subscription_doc
    
    async def get_subscriptions(self, tenant_id: str, customer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get subscriptions for tenant"""
        query = {"tenant_id": tenant_id}
        if customer_id:
            query["customer_id"] = customer_id
        
        subscriptions = await self.db.subscriptions.find(query).to_list(1000)
        return subscriptions
    
    # Financial Reports
    async def get_revenue_report(self, tenant_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate revenue report"""
        # Get paid invoices in date range
        paid_invoices = await self.db.invoices.find({
            "tenant_id": tenant_id,
            "status": "paid",
            "created_at": {"$gte": start_date, "$lte": end_date}
        }).to_list(1000)
        
        total_revenue = sum(invoice["total_amount"] for invoice in paid_invoices)
        invoice_count = len(paid_invoices)
        
        # Get transactions for the period
        transactions = await self.db.transactions.find({
            "tenant_id": tenant_id,
            "transaction_date": {"$gte": start_date, "$lte": end_date},
            "type": "payment"
        }).to_list(1000)
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "total_revenue": total_revenue,
            "invoice_count": invoice_count,
            "average_invoice_value": total_revenue / invoice_count if invoice_count > 0 else 0,
            "transaction_count": len(transactions)
        }
    
    async def get_outstanding_balance(self, tenant_id: str) -> Dict[str, Any]:
        """Get outstanding balance from unpaid invoices"""
        unpaid_invoices = await self.db.invoices.find({
            "tenant_id": tenant_id,
            "status": {"$in": ["sent", "overdue"]}
        }).to_list(1000)
        
        total_outstanding = sum(invoice["total_amount"] for invoice in unpaid_invoices)
        overdue_invoices = [inv for inv in unpaid_invoices if inv.get("due_date", datetime.utcnow()) < datetime.utcnow()]
        overdue_amount = sum(invoice["total_amount"] for invoice in overdue_invoices)
        
        return {
            "total_outstanding": total_outstanding,
            "overdue_amount": overdue_amount,
            "unpaid_invoice_count": len(unpaid_invoices),
            "overdue_invoice_count": len(overdue_invoices)
        }
    
    # Payment Processing
    async def process_payment(self, tenant_id: str, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a payment for an invoice"""
        invoice_id = payment_data.get("invoice_id")
        amount = Decimal(str(payment_data.get("amount", 0)))
        payment_method = payment_data.get("payment_method", "unknown")
        
        # Get invoice
        invoice = await self.db.invoices.find_one({
            "tenant_id": tenant_id,
            "id": invoice_id
        })
        
        if not invoice:
            raise ValueError("Invoice not found")
        
        if invoice["status"] == "paid":
            raise ValueError("Invoice already paid")
        
        # Create payment record
        payment_doc = {
            "id": f"PAY-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "tenant_id": tenant_id,
            "invoice_id": invoice_id,
            "amount": float(amount),
            "payment_method": payment_method,
            "status": "completed",
            "processed_at": datetime.utcnow(),
            "created_at": datetime.utcnow()
        }
        
        await self.db.payments.insert_one(payment_doc)
        
        # Update invoice status
        if amount >= Decimal(str(invoice["total_amount"])):
            await self.update_invoice_status(invoice_id, "paid")
        else:
            await self.update_invoice_status(invoice_id, "partially_paid")
        
        # Create transaction record
        await self.create_transaction(tenant_id, {
            "id": f"TXN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "type": "payment",
            "amount": float(amount),
            "description": f"Payment for invoice {invoice_id}",
            "reference_id": invoice_id,
            "payment_method": payment_method
        })
        
        return payment_doc
    
    async def get_payments(self, tenant_id: str, invoice_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get payments for tenant or specific invoice"""
        query = {"tenant_id": tenant_id}
        if invoice_id:
            query["invoice_id"] = invoice_id
        
        payments = await self.db.payments.find(query).sort("processed_at", -1).to_list(1000)
        return payments
    
    # Subscription Billing
    async def process_subscription_billing(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Process billing for due subscriptions"""
        # Find subscriptions due for billing
        due_subscriptions = await self.db.subscriptions.find({
            "tenant_id": tenant_id,
            "status": "active",
            "next_billing_date": {"$lte": datetime.utcnow()}
        }).to_list(1000)
        
        processed_invoices = []
        
        for subscription in due_subscriptions:
            # Create invoice for subscription
            line_items = [{
                "description": subscription.get("description", "Subscription"),
                "quantity": 1,
                "unit_price": subscription["amount"]
            }]
            
            invoice = await self.create_invoice(
                tenant_id=tenant_id,
                customer_id=subscription["customer_id"],
                line_items=line_items
            )
            
            # Update next billing date
            billing_cycle = subscription.get("billing_cycle", "monthly")
            if billing_cycle == "monthly":
                next_billing = subscription["next_billing_date"] + timedelta(days=30)
            elif billing_cycle == "yearly":
                next_billing = subscription["next_billing_date"] + timedelta(days=365)
            else:
                next_billing = subscription["next_billing_date"] + timedelta(days=30)
            
            await self.db.subscriptions.update_one(
                {"id": subscription["id"]},
                {"$set": {"next_billing_date": next_billing}}
            )
            
            processed_invoices.append(invoice)
        
        return processed_invoices
    
    # Financial Analytics
    async def get_financial_dashboard(self, tenant_id: str) -> Dict[str, Any]:
        """Get financial dashboard data"""
        # Current month revenue
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        monthly_revenue = await self.get_revenue_report(tenant_id, start_of_month, end_of_month)
        outstanding = await self.get_outstanding_balance(tenant_id)
        
        # Recent transactions
        recent_transactions = await self.get_transactions(tenant_id, {
            "transaction_date": {"$gte": datetime.utcnow() - timedelta(days=30)}
        })
        
        # Active subscriptions
        active_subscriptions = await self.get_subscriptions(tenant_id)
        active_subscriptions = [s for s in active_subscriptions if s["status"] == "active"]
        
        return {
            "monthly_revenue": monthly_revenue["total_revenue"],
            "outstanding_balance": outstanding["total_outstanding"],
            "overdue_amount": outstanding["overdue_amount"],
            "active_subscriptions": len(active_subscriptions),
            "recent_transactions": len(recent_transactions),
            "monthly_invoice_count": monthly_revenue["invoice_count"]
        }
    
    async def get_kernel_health(self) -> Dict[str, Any]:
        """Get kernel health status"""
        try:
            # Test database connectivity
            await self.db.invoices.find_one({"tenant_id": "health_check"})
            
            return {
                "status": "healthy",
                "collections": ["invoices", "line_items", "transactions", "subscriptions", "products", "payments"],
                "last_check": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }