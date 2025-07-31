"""
Communication and Automation API
Provides endpoints for messaging, workflows, and automation
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field

from kernels.communication_kernel import (
    CommunicationKernel,
    MessageChannel,
    TriggerEvent,
)
from middleware.tenant_middleware import get_tenant_id_from_request

router = APIRouter(prefix="/api/communication", tags=["communication"])


# Request/Response Models
class CreateTemplateRequest(BaseModel):
    name: str
    template_type: str
    channel: MessageChannel
    subject: str
    body: str
    description: Optional[str] = None


class TemplateResponse(BaseModel):
    id: str
    name: str
    template_type: str
    channel: MessageChannel
    subject: str
    body: str
    is_active: bool
    created_at: datetime


class CreateWorkflowRequest(BaseModel):
    name: str
    trigger_event: TriggerEvent
    description: Optional[str] = None
    actions: List[Dict[str, Any]]
    conditions: Optional[Dict[str, Any]] = None


class WorkflowResponse(BaseModel):
    id: str
    name: str
    trigger_event: TriggerEvent
    description: Optional[str]
    actions: List[Dict[str, Any]]
    is_active: bool
    created_at: datetime


class SendMessageRequest(BaseModel):
    template_id: str
    recipient: EmailStr
    context: Dict[str, Any] = Field(default_factory=dict)
    scheduled_for: Optional[datetime] = None


class BulkMessageRequest(BaseModel):
    template_id: str
    recipients: List[Dict[str, Any]]
    scheduled_for: Optional[datetime] = None


class MessageResponse(BaseModel):
    id: str
    channel: MessageChannel
    recipient: str
    subject: str
    status: str
    scheduled_for: datetime
    created_at: datetime


class NotificationPreferencesRequest(BaseModel):
    email_notifications: bool = True
    sms_notifications: bool = False
    push_notifications: bool = True
    booking_confirmations: bool = True
    booking_reminders: bool = True
    marketing_emails: bool = False
    system_updates: bool = True


class CommunicationStatsResponse(BaseModel):
    period: Dict[str, str]
    messages: Dict[str, Any]
    workflows: Dict[str, Any]


# Dependency injection
async def get_communication_kernel(request: Request) -> CommunicationKernel:
    """Get communication kernel from app state"""
    return request.app.state.platform_core.get_kernel("communication")


# Template Management Endpoints
@router.post(
    "/templates",
    response_model=TemplateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_template(
    request: CreateTemplateRequest,
    tenant_id: str = Depends(get_tenant_id_from_request),
    comm_kernel: CommunicationKernel = Depends(get_communication_kernel),
):
    """Create a new message template"""
    try:
        template_data = request.dict()
        template_data["id"] = f"tpl_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        template = await comm_kernel.create_message_template(tenant_id, template_data)

        return TemplateResponse(
            id=template["id"],
            name=template["name"],
            template_type=template["template_type"],
            channel=template["channel"],
            subject=template["subject"],
            body=template["body"],
            is_active=template["is_active"],
            created_at=template["created_at"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template: {str(e)}",
        )


@router.get("/templates", response_model=List[TemplateResponse])
async def list_templates(
    template_type: Optional[str] = None,
    tenant_id: str = Depends(get_tenant_id_from_request),
    comm_kernel: CommunicationKernel = Depends(get_communication_kernel),
):
    """List message templates"""
    try:
        templates = await comm_kernel.get_message_templates(tenant_id, template_type)

        return [
            TemplateResponse(
                id=template["id"],
                name=template["name"],
                template_type=template["template_type"],
                channel=template["channel"],
                subject=template["subject"],
                body=template["body"],
                is_active=template["is_active"],
                created_at=template["created_at"],
            )
            for template in templates
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list templates: {str(e)}",
        )


@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    tenant_id: str = Depends(get_tenant_id_from_request),
    comm_kernel: CommunicationKernel = Depends(get_communication_kernel),
):
    """Get template by ID"""
    try:
        from sqlalchemy import select

        from models.postgresql_models import MessageTemplate

        async with comm_kernel.connection_manager.get_session() as session:
            result = await session.execute(
                select(MessageTemplate).where(
                    MessageTemplate.id == template_id,
                    MessageTemplate.tenant_id == tenant_id,
                )
            )
            template = result.scalar_one_or_none()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found",
            )

        return TemplateResponse(
            id=template["id"],
            name=template["name"],
            template_type=template["template_type"],
            channel=template["channel"],
            subject=template["subject"],
            body=template["body"],
            is_active=template["is_active"],
            created_at=template["created_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get template: {str(e)}",
        )


# Workflow Management Endpoints
@router.post(
    "/workflows",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_workflow(
    request: CreateWorkflowRequest,
    tenant_id: str = Depends(get_tenant_id_from_request),
    comm_kernel: CommunicationKernel = Depends(get_communication_kernel),
):
    """Create a new automation workflow"""
    try:
        workflow_data = request.dict()
        workflow_data["id"] = f"wf_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        workflow = await comm_kernel.create_workflow(tenant_id, workflow_data)

        return WorkflowResponse(
            id=workflow["id"],
            name=workflow["name"],
            trigger_event=workflow["trigger_event"],
            description=workflow.get("description"),
            actions=workflow["actions"],
            is_active=workflow["is_active"],
            created_at=workflow["created_at"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workflow: {str(e)}",
        )


@router.get("/workflows", response_model=List[WorkflowResponse])
async def list_workflows(
    trigger_event: Optional[TriggerEvent] = None,
    tenant_id: str = Depends(get_tenant_id_from_request),
    comm_kernel: CommunicationKernel = Depends(get_communication_kernel),
):
    """List automation workflows"""
    try:
        workflows = await comm_kernel.get_workflows(
            tenant_id, trigger_event.value if trigger_event else None
        )

        return [
            WorkflowResponse(
                id=workflow["id"],
                name=workflow["name"],
                trigger_event=workflow["trigger_event"],
                description=workflow.get("description"),
                actions=workflow["actions"],
                is_active=workflow["is_active"],
                created_at=workflow["created_at"],
            )
            for workflow in workflows
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list workflows: {str(e)}",
        )


# Message Sending Endpoints
@router.post(
    "/messages/send",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    request: SendMessageRequest,
    tenant_id: str = Depends(get_tenant_id_from_request),
    comm_kernel: CommunicationKernel = Depends(get_communication_kernel),
):
    """Send a single message"""
    try:
        # Render template
        rendered = await comm_kernel.render_template(
            request.template_id, request.context
        )

        # Queue message
        message_data = {
            "id": f"msg_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "channel": rendered["channel"],
            "recipient": request.recipient,
            "subject": rendered["subject"],
            "body": rendered["body"],
            "template_id": request.template_id,
        }

        message = await comm_kernel.queue_message(
            tenant_id, message_data, request.scheduled_for
        )

        return MessageResponse(
            id=message["id"],
            channel=message["channel"],
            recipient=message["recipient"],
            subject=message["subject"],
            status=message["status"],
            scheduled_for=message["scheduled_for"],
            created_at=message["created_at"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}",
        )


@router.post("/messages/bulk")
async def send_bulk_message(
    request: BulkMessageRequest,
    tenant_id: str = Depends(get_tenant_id_from_request),
    comm_kernel: CommunicationKernel = Depends(get_communication_kernel),
):
    """Send bulk messages"""
    try:
        result = await comm_kernel.send_bulk_message(
            tenant_id=tenant_id,
            template_id=request.template_id,
            recipients=request.recipients,
            scheduled_for=request.scheduled_for,
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send bulk messages: {str(e)}",
        )


@router.get("/messages", response_model=List[MessageResponse])
async def list_messages(
    status_filter: Optional[str] = None,
    limit: int = Field(default=100, le=1000),
    tenant_id: str = Depends(get_tenant_id_from_request),
    comm_kernel: CommunicationKernel = Depends(get_communication_kernel),
):
    """List messages"""
    try:
        query = {"tenant_id": tenant_id}
        if status_filter:
            query["status"] = status_filter

        from sqlalchemy import select

        from models.postgresql_models import MessageQueue

        async with comm_kernel.connection_manager.get_session() as session:
            query_conditions = [MessageQueue.tenant_id == tenant_id]
            if status_filter:
                query_conditions.append(MessageQueue.status == status_filter)

            result = await session.execute(
                select(MessageQueue)
                .where(*query_conditions)
                .order_by(MessageQueue.created_at.desc())
                .limit(limit)
            )
            messages = result.scalars().all()

        return [
            MessageResponse(
                id=message["id"],
                channel=message["channel"],
                recipient=message["recipient"],
                subject=message.get("subject", ""),
                status=message["status"],
                scheduled_for=message["scheduled_for"],
                created_at=message["created_at"],
            )
            for message in messages
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list messages: {str(e)}",
        )


# Event Trigger Endpoints
@router.post("/events/trigger")
async def trigger_event(
    event: TriggerEvent,
    context: Dict[str, Any],
    tenant_id: str = Depends(get_tenant_id_from_request),
    comm_kernel: CommunicationKernel = Depends(get_communication_kernel),
):
    """Manually trigger an event"""
    try:
        await comm_kernel.trigger_event(tenant_id, event, context)

        return {
            "message": f"Event {event.value} triggered successfully",
            "event": event.value,
            "context": context,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger event: {str(e)}",
        )


# Notification Preferences Endpoints
@router.put("/preferences/{user_id}")
async def update_notification_preferences(
    user_id: str,
    request: NotificationPreferencesRequest,
    tenant_id: str = Depends(get_tenant_id_from_request),
    comm_kernel: CommunicationKernel = Depends(get_communication_kernel),
):
    """Update user notification preferences"""
    try:
        success = await comm_kernel.update_notification_preferences(
            tenant_id, user_id, request.dict()
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update preferences",
            )

        return {"message": "Notification preferences updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update preferences: {str(e)}",
        )


@router.get("/preferences/{user_id}")
async def get_notification_preferences(
    user_id: str,
    tenant_id: str = Depends(get_tenant_id_from_request),
    comm_kernel: CommunicationKernel = Depends(get_communication_kernel),
):
    """Get user notification preferences"""
    try:
        preferences = await comm_kernel.get_notification_preferences(tenant_id, user_id)
        return preferences

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get preferences: {str(e)}",
        )


# Analytics Endpoints
@router.get("/stats", response_model=CommunicationStatsResponse)
async def get_communication_stats(
    days: int = Field(default=30, ge=1, le=365),
    tenant_id: str = Depends(get_tenant_id_from_request),
    comm_kernel: CommunicationKernel = Depends(get_communication_kernel),
):
    """Get communication statistics"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        end_date = datetime.utcnow()

        stats = await comm_kernel.get_communication_stats(
            tenant_id, start_date, end_date
        )

        return CommunicationStatsResponse(
            period=stats["period"],
            messages=stats["messages"],
            workflows=stats["workflows"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get communication stats: {str(e)}",
        )


# Queue Management Endpoints
@router.post("/queue/process")
async def process_message_queue(
    limit: int = Field(default=100, ge=1, le=1000),
    comm_kernel: CommunicationKernel = Depends(get_communication_kernel),
):
    """Process message queue (admin endpoint)"""
    try:
        result = await comm_kernel.process_message_queue(limit)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message queue: {str(e)}",
        )


@router.get("/queue/status")
async def get_queue_status(
    tenant_id: str = Depends(get_tenant_id_from_request),
    comm_kernel: CommunicationKernel = Depends(get_communication_kernel),
):
    """Get message queue status"""
    try:
        from sqlalchemy import func, select

        from models.postgresql_models import MessageQueue

        async with comm_kernel.connection_manager.get_session() as session:
            queued_result = await session.execute(
                select(func.count(MessageQueue.id)).where(
                    MessageQueue.tenant_id == tenant_id,
                    MessageQueue.status == "queued",
                )
            )
            queued_count = queued_result.scalar()

            processing_result = await session.execute(
                select(func.count(MessageQueue.id)).where(
                    MessageQueue.tenant_id == tenant_id,
                    MessageQueue.status == "processing",
                )
            )
            processing_count = processing_result.scalar()

            failed_result = await session.execute(
                select(func.count(MessageQueue.id)).where(
                    MessageQueue.tenant_id == tenant_id,
                    MessageQueue.status == "failed",
                )
            )
            failed_count = failed_result.scalar()

        return {
            "queued": queued_count,
            "processing": processing_count,
            "failed": failed_count,
            "total": queued_count + processing_count + failed_count,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue status: {str(e)}",
        )
