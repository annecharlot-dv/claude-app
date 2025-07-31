"""
Financial Management API
Provides endpoints for billing, invoicing, payments, and financial reporting
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from kernels.financial_kernel import FinancialKernel
from middleware.tenant_middleware import get_tenant_id_from_request

router = APIRouter(prefix="/api/financial", tags=["financial"])


# Request/Response Models
class LineItemRequest(BaseModel):
    description: str
    quantity: int = Field(ge=1)
    unit_price: float = Field(ge=0)


class CreateInvoiceRequest(BaseModel):
    customer_id: str
    line_items: List[LineItemRequest]
    due_date: Optional[datetime] = None
    notes: Optional[str] = None


class InvoiceResponse(BaseModel):
    id: str
    customer_id: str
    subtotal: float
    tax_amount: float
    total_amount: float
    status: str
    due_date: datetime
    created_at: datetime
    line_items: List[Dict[str, Any]]


class ProcessPaymentRequest(BaseModel):
    invoice_id: str
    amount: float = Field(ge=0)
    payment_method: str
    reference: Optional[str] = None


class PaymentResponse(BaseModel):
    id: str
    invoice_id: str
    amount: float
    payment_method: str
    status: str
    processed_at: datetime


class CreateProductRequest(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(ge=0)
    category: Optional[str] = None
    is_recurring: bool = False
    billing_cycle: Optional[str] = None  # monthly, yearly


class ProductResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    price: float
    category: Optional[str]
    is_recurring: bool
    is_active: bool
    created_at: datetime


class CreateSubscriptionRequest(BaseModel):
    customer_id: str
    product_id: str
    start_date: datetime
    billing_cycle: str = "monthly"  # monthly, yearly
    amount: float = Field(ge=0)


class SubscriptionResponse(BaseModel):
    id: str
    customer_id: str
    product_id: str
    amount: float
    billing_cycle: str
    status: str
    next_billing_date: datetime
    created_at: datetime


class RevenueReportResponse(BaseModel):
    period: Dict[str, str]
    total_revenue: float
    invoice_count: int
    average_invoice_value: float
    transaction_count: int


class FinancialDashboardResponse(BaseModel):
    monthly_revenue: float
    outstanding_balance: float
    overdue_amount: float
    active_subscriptions: int
    recent_transactions: int
    monthly_invoice_count: int


# Dependency injection
async def get_financial_kernel(request: Request) -> FinancialKernel:
    """Get financial kernel from app state"""
    return request.app.state.platform_core.get_kernel("financial")


# Product Management Endpoints
@router.post(
    "/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    request: CreateProductRequest,
    tenant_id: str = Depends(get_tenant_id_from_request),
    financial_kernel: FinancialKernel = Depends(get_financial_kernel),
):
    """Create a new product or service"""
    try:
        product_data = request.dict()
        product_data["id"] = f"prod_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        product = await financial_kernel.create_product(tenant_id, product_data)

        return ProductResponse(
            id=product["id"],
            name=product["name"],
            description=product.get("description"),
            price=product["price"],
            category=product.get("category"),
            is_recurring=product.get("is_recurring", False),
            is_active=product["is_active"],
            created_at=product["created_at"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create product: {str(e)}",
        )


@router.get("/products", response_model=List[ProductResponse])
async def list_products(
    active_only: bool = True,
    tenant_id: str = Depends(get_tenant_id_from_request),
    financial_kernel: FinancialKernel = Depends(get_financial_kernel),
):
    """List products and services"""
    try:
        products = await financial_kernel.get_products(tenant_id, active_only)

        return [
            ProductResponse(
                id=product["id"],
                name=product["name"],
                description=product.get("description"),
                price=product["price"],
                category=product.get("category"),
                is_recurring=product.get("is_recurring", False),
                is_active=product["is_active"],
                created_at=product["created_at"],
            )
            for product in products
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list products: {str(e)}",
        )


# Invoice Management Endpoints
@router.post(
    "/invoices",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_invoice(
    request: CreateInvoiceRequest,
    tenant_id: str = Depends(get_tenant_id_from_request),
    financial_kernel: FinancialKernel = Depends(get_financial_kernel),
):
    """Create a new invoice"""
    try:
        line_items = [item.dict() for item in request.line_items]

        invoice = await financial_kernel.create_invoice(
            tenant_id=tenant_id,
            customer_id=request.customer_id,
            line_items=line_items,
            due_date=request.due_date,
        )

        # Get line items for response
        line_items_docs = await financial_kernel.get_line_items(invoice["id"])

        return InvoiceResponse(
            id=invoice["id"],
            customer_id=invoice["customer_id"],
            subtotal=invoice["subtotal"],
            tax_amount=invoice["tax_amount"],
            total_amount=invoice["total_amount"],
            status=invoice["status"],
            due_date=invoice["due_date"],
            created_at=invoice["created_at"],
            line_items=line_items_docs,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create invoice: {str(e)}",
        )


@router.get("/invoices", response_model=List[InvoiceResponse])
async def list_invoices(
    status_filter: Optional[str] = None,
    customer_id: Optional[str] = None,
    limit: int = Field(default=100, le=1000),
    tenant_id: str = Depends(get_tenant_id_from_request),
    financial_kernel: FinancialKernel = Depends(get_financial_kernel),
):
    """List invoices with filtering"""
    try:
        filters = {}
        if status_filter:
            filters["status"] = status_filter
        if customer_id:
            filters["customer_id"] = customer_id

        invoices = await financial_kernel.get_invoices(tenant_id, filters)

        return [
            InvoiceResponse(
                id=invoice["id"],
                customer_id=invoice["customer_id"],
                subtotal=invoice["subtotal"],
                tax_amount=invoice["tax_amount"],
                total_amount=invoice["total_amount"],
                status=invoice["status"],
                due_date=invoice["due_date"],
                created_at=invoice["created_at"],
                line_items=invoice.get("line_items", []),
            )
            for invoice in invoices[:limit]
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list invoices: {str(e)}",
        )


@router.put("/invoices/{invoice_id}/status")
async def update_invoice_status(
    invoice_id: str,
    new_status: str,
    tenant_id: str = Depends(get_tenant_id_from_request),
    financial_kernel: FinancialKernel = Depends(get_financial_kernel),
):
    """Update invoice status"""
    try:
        success = await financial_kernel.update_invoice_status(invoice_id, new_status)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found",
            )

        return {"message": f"Invoice status updated to {new_status}"}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update invoice status: {str(e)}",
        )


# Payment Processing Endpoints
@router.post(
    "/payments",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def process_payment(
    request: ProcessPaymentRequest,
    tenant_id: str = Depends(get_tenant_id_from_request),
    financial_kernel: FinancialKernel = Depends(get_financial_kernel),
):
    """Process a payment for an invoice"""
    try:
        payment_data = request.dict()
        payment = await financial_kernel.process_payment(tenant_id, payment_data)

        return PaymentResponse(
            id=payment["id"],
            invoice_id=payment["invoice_id"],
            amount=payment["amount"],
            payment_method=payment["payment_method"],
            status=payment["status"],
            processed_at=payment["processed_at"],
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process payment: {str(e)}",
        )


@router.get("/payments", response_model=List[PaymentResponse])
async def list_payments(
    invoice_id: Optional[str] = None,
    tenant_id: str = Depends(get_tenant_id_from_request),
    financial_kernel: FinancialKernel = Depends(get_financial_kernel),
):
    """List payments"""
    try:
        payments = await financial_kernel.get_payments(tenant_id, invoice_id)

        return [
            PaymentResponse(
                id=payment["id"],
                invoice_id=payment["invoice_id"],
                amount=payment["amount"],
                payment_method=payment["payment_method"],
                status=payment["status"],
                processed_at=payment["processed_at"],
            )
            for payment in payments
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list payments: {str(e)}",
        )


# Subscription Management Endpoints
@router.post(
    "/subscriptions",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_subscription(
    request: CreateSubscriptionRequest,
    tenant_id: str = Depends(get_tenant_id_from_request),
    financial_kernel: FinancialKernel = Depends(get_financial_kernel),
):
    """Create a new subscription"""
    try:
        subscription_data = request.dict()
        subscription_data["id"] = f"sub_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        subscription = await financial_kernel.create_subscription(
            tenant_id, subscription_data
        )

        return SubscriptionResponse(
            id=subscription["id"],
            customer_id=subscription["customer_id"],
            product_id=subscription.get("product_id", ""),
            amount=subscription["amount"],
            billing_cycle=subscription.get("billing_cycle", "monthly"),
            status=subscription["status"],
            next_billing_date=subscription["next_billing_date"],
            created_at=subscription["created_at"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create subscription: {str(e)}",
        )


@router.get("/subscriptions", response_model=List[SubscriptionResponse])
async def list_subscriptions(
    customer_id: Optional[str] = None,
    tenant_id: str = Depends(get_tenant_id_from_request),
    financial_kernel: FinancialKernel = Depends(get_financial_kernel),
):
    """List subscriptions"""
    try:
        subscriptions = await financial_kernel.get_subscriptions(tenant_id, customer_id)

        return [
            SubscriptionResponse(
                id=subscription["id"],
                customer_id=subscription["customer_id"],
                product_id=subscription.get("product_id", ""),
                amount=subscription["amount"],
                billing_cycle=subscription.get("billing_cycle", "monthly"),
                status=subscription["status"],
                next_billing_date=subscription["next_billing_date"],
                created_at=subscription["created_at"],
            )
            for subscription in subscriptions
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list subscriptions: {str(e)}",
        )


@router.post("/subscriptions/process-billing")
async def process_subscription_billing(
    tenant_id: str = Depends(get_tenant_id_from_request),
    financial_kernel: FinancialKernel = Depends(get_financial_kernel),
):
    """Process billing for due subscriptions"""
    try:
        processed_invoices = await financial_kernel.process_subscription_billing(
            tenant_id
        )  # noqa: E501

        return {
            "message": (f"Processed {len(processed_invoices)} subscription billings"),
            "invoices_created": len(processed_invoices),
            "invoice_ids": [inv["id"] for inv in processed_invoices],
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process subscription billing: {str(e)}",
        )


# Reporting Endpoints
@router.get("/reports/revenue", response_model=RevenueReportResponse)
async def get_revenue_report(
    start_date: datetime,
    end_date: datetime,
    tenant_id: str = Depends(get_tenant_id_from_request),
    financial_kernel: FinancialKernel = Depends(get_financial_kernel),
):
    """Get revenue report for date range"""
    try:
        report = await financial_kernel.get_revenue_report(
            tenant_id, start_date, end_date
        )

        return RevenueReportResponse(
            period=report["period"],
            total_revenue=report["total_revenue"],
            invoice_count=report["invoice_count"],
            average_invoice_value=report["average_invoice_value"],
            transaction_count=report["transaction_count"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate revenue report: {str(e)}",
        )


@router.get("/reports/outstanding")
async def get_outstanding_balance(
    tenant_id: str = Depends(get_tenant_id_from_request),
    financial_kernel: FinancialKernel = Depends(get_financial_kernel),
):
    """Get outstanding balance report"""
    try:
        report = await financial_kernel.get_outstanding_balance(tenant_id)
        return report

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get outstanding balance: {str(e)}",
        )


@router.get("/dashboard", response_model=FinancialDashboardResponse)
async def get_financial_dashboard(
    tenant_id: str = Depends(get_tenant_id_from_request),
    financial_kernel: FinancialKernel = Depends(get_financial_kernel),
):
    """Get financial dashboard data"""
    try:
        dashboard = await financial_kernel.get_financial_dashboard(tenant_id)

        return FinancialDashboardResponse(
            monthly_revenue=dashboard["monthly_revenue"],
            outstanding_balance=dashboard["outstanding_balance"],
            overdue_amount=dashboard["overdue_amount"],
            active_subscriptions=dashboard["active_subscriptions"],
            recent_transactions=dashboard["recent_transactions"],
            monthly_invoice_count=dashboard["monthly_invoice_count"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get financial dashboard: {str(e)}",
        )
