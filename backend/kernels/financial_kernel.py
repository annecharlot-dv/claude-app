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