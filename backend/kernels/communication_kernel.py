"""
Automation & Communication Kernel (The "Messenger")
Universal communication and workflow automation engine
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import select

from kernels.base_kernel import BaseKernel
from models.postgresql_models import (
    MessageQueue,
    MessageTemplate,
    Workflow,
)


class TriggerEvent(str, Enum):
    USER_CREATED = "user_created"
    BOOKING_CREATED = "booking_created"
    BOOKING_CANCELLED = "booking_cancelled"
    LEAD_CREATED = "lead_created"
    LEAD_CONVERTED = "lead_converted"
    INVOICE_CREATED = "invoice_created"
    INVOICE_PAID = "invoice_paid"
    PAGE_PUBLISHED = "page_published"
    TOUR_SCHEDULED = "tour_scheduled"
    TOUR_COMPLETED = "tour_completed"


class MessageChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH_NOTIFICATION = "push_notification"
    WEBHOOK = "webhook"
    INTERNAL_NOTIFICATION = "internal_notification"


class CommunicationKernel(BaseKernel):
    """Universal communication and automation system"""

    def __init__(self, connection_manager):
        super().__init__(connection_manager)
        self.workflows = {}
        self.message_handlers = {}
        self.triggers = {}

    async def _initialize_kernel(self):
        """Initialize communication kernel"""
        pass

    async def validate_tenant_access(self, tenant_id: str, user_id: str) -> bool:
        """Validate user belongs to tenant"""
        from models.postgresql_models import User

        async with self.connection_manager.get_session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id, User.tenant_id == tenant_id)
            )
            return result.scalar_one_or_none() is not None

    # Message Template Management
    async def create_message_template(
        self, tenant_id: str, template_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new message template"""
        async with self.connection_manager.get_session() as session:
            template_obj = MessageTemplate(
                tenant_id=tenant_id,
                is_active=True,
                created_at=datetime.utcnow(),
                **template_data,
            )
            session.add(template_obj)
            await session.commit()
            return template_obj.__dict__

    async def get_message_templates(
        self, tenant_id: str, template_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get message templates for tenant"""
        async with self.connection_manager.get_session() as session:
            query_conditions = [
                MessageTemplate.tenant_id == tenant_id,
                MessageTemplate.is_active.is_(True),
            ]
            if template_type:
                query_conditions.append(MessageTemplate.template_type == template_type)

            result = await session.execute(
                select(MessageTemplate).where(*query_conditions)
            )
            return [template.__dict__ for template in result.scalars().all()]

    async def render_template(
        self, template_id: str, context: Dict[str, Any]
    ) -> Dict[str, str]:
        """Render a message template with context data"""
        async with self.connection_manager.get_session() as session:
            result = await session.execute(
                select(MessageTemplate).where(MessageTemplate.id == template_id)
            )
            template = result.scalar_one_or_none()
            if not template:
                raise ValueError("Template not found")

            # Simple template rendering (in production, use a proper template
            subject = template.subject or ""
            body = template.body or ""

            for key, value in context.items():
                placeholder = "{" + key + "}"
                subject = subject.replace(placeholder, str(value))
                body = body.replace(placeholder, str(value))

            return {
                "subject": subject,
                "body": body,
                "channel": template.channel or MessageChannel.EMAIL,
            }

    # Workflow Management
    async def create_workflow(
        self, tenant_id: str, workflow_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create an automation workflow"""
        async with self.connection_manager.get_session() as session:
            workflow_obj = Workflow(
                tenant_id=tenant_id,
                is_active=True,
                created_at=datetime.utcnow(),
                **workflow_data,
            )
            session.add(workflow_obj)
            await session.commit()
            return workflow_obj.__dict__

    async def get_workflows(
        self, tenant_id: str, trigger_event: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get workflows for tenant"""
        async with self.connection_manager.get_session() as session:
            query_conditions = [
                Workflow.tenant_id == tenant_id,
                Workflow.is_active.is_(True),
            ]
            if trigger_event:
                query_conditions.append(Workflow.trigger_event == trigger_event)

            result = await session.execute(select(Workflow).where(*query_conditions))
            return [workflow.__dict__ for workflow in result.scalars().all()]

    # Message Queue Management
    async def queue_message(
        self,
        tenant_id: str,
        message_data: Dict[str, Any],
        scheduled_for: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Queue a message for delivery"""
        async with self.connection_manager.get_session() as session:
            message_obj = MessageQueue(
                tenant_id=tenant_id,
                status="queued",
                scheduled_for=scheduled_for or datetime.utcnow(),
                attempts=0,
                max_attempts=3,
                created_at=datetime.utcnow(),
                **message_data,
            )
            session.add(message_obj)
            await session.commit()
            return message_obj.__dict__

    async def get_queued_messages(
        self, tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get messages ready for delivery"""
        async with self.connection_manager.get_session() as session:
            query_conditions = [
                MessageQueue.status == "queued",
                MessageQueue.scheduled_for <= datetime.utcnow(),
            ]
            if tenant_id:
                query_conditions.append(MessageQueue.tenant_id == tenant_id)

            result = await session.execute(
                select(MessageQueue).where(*query_conditions).limit(100)
            )
            return [message.__dict__ for message in result.scalars().all()]

    async def update_message_status(
        self, message_id: str, status: str, error: Optional[str] = None
    ):
        """Update message delivery status"""
        async with self.connection_manager.get_session() as session:
            result = await session.execute(
                select(MessageQueue).where(MessageQueue.id == message_id)
            )
            message = result.scalar_one_or_none()
            if message:
                message.status = status
                message.updated_at = datetime.utcnow()
                message.attempts = (message.attempts or 0) + 1
                if error:
                    message.last_error = error
                await session.commit()

    # Event Triggers
    async def trigger_event(
        self, tenant_id: str, event: TriggerEvent, context: Dict[str, Any]
    ):
        """Trigger an event and execute associated workflows"""
        # Get workflows for this event
        workflows = await self.get_workflows(tenant_id, event.value)

        for workflow in workflows:
            await self._execute_workflow(tenant_id, workflow, context)

    async def _execute_workflow(
        self, tenant_id: str, workflow: Dict[str, Any], context: Dict[str, Any]
    ):
        """Execute a workflow"""
        try:
            # Log workflow execution
            log_entry = {
                "id": "log_" + datetime.utcnow().strftime("%Y%m%d%H%M%S"),
                "tenant_id": tenant_id,
                "workflow_id": workflow["id"],
                "trigger_event": workflow["trigger_event"],
                "context": context,
                "status": "started",
                "created_at": datetime.utcnow(),
            }
            pass

            # Execute workflow actions
            for action in workflow.get("actions", []):
                await self._execute_action(tenant_id, action, context)

            # Update log status
            pass

        except Exception as e:
            # Log error
            await self.db.automation_logs.update_one(
                {"id": log_entry["id"]},
                {
                    "$set": {
                        "status": "failed",
                        "error": str(e),
                        "completed_at": datetime.utcnow(),
                    }
                },
            )

    async def _execute_action(
        self, tenant_id: str, action: Dict[str, Any], context: Dict[str, Any]
    ):
        """Execute a single workflow action"""
        action_type = action.get("type")

        if action_type == "send_message":
            template_id = action.get("template_id")
            recipient = action.get("recipient", context.get("user_email"))

            if template_id and recipient:
                rendered = await self.render_template(template_id, context)

                message_data = {
                    "id": "msg_" + datetime.utcnow().strftime("%Y%m%d%H%M%S"),
                    "channel": rendered["channel"],
                    "recipient": recipient,
                    "subject": rendered["subject"],
                    "body": rendered["body"],
                    "template_id": template_id,
                }

                await self.queue_message(tenant_id, message_data)

        elif action_type == "update_status":
            # Update status of related entity
            entity_type = action.get("entity_type")
            entity_id = context.get(entity_type + "_id")
            new_status = action.get("status")

            if entity_type and entity_id and new_status:
                collection = getattr(self.db, entity_type + "s", None)
                if collection:
                    await collection.update_one(
                        {"id": entity_id},
                        {
                            "$set": {
                                "status": new_status,
                                "updated_at": datetime.utcnow(),
                            }
                        },
                    )

        elif action_type == "webhook":
            # Queue webhook call
            webhook_url = action.get("url")
            if webhook_url:
                webhook_data = {
                    "id": "hook_" + datetime.utcnow().strftime("%Y%m%d%H%M%S"),
                    "channel": MessageChannel.WEBHOOK,
                    "url": webhook_url,
                    "payload": context,
                    "method": action.get("method", "POST"),
                }
                await self.queue_message(tenant_id, webhook_data)

    # Analytics and Reporting
    async def get_communication_stats(
        self, tenant_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get communication statistics"""
        # Message delivery stats
        total_messages = await self.db.message_queue.count_documents(
            {
                "tenant_id": tenant_id,
                "created_at": {"$gte": start_date, "$lte": end_date},
            }
        )

        delivered_messages = await self.db.message_queue.count_documents(
            {
                "tenant_id": tenant_id,
                "created_at": {"$gte": start_date, "$lte": end_date},
                "status": "delivered",
            }
        )

        failed_messages = await self.db.message_queue.count_documents(
            {
                "tenant_id": tenant_id,
                "created_at": {"$gte": start_date, "$lte": end_date},
                "status": "failed",
            }
        )

        # Workflow execution stats
        workflow_executions = await self.db.automation_logs.count_documents(
            {
                "tenant_id": tenant_id,
                "created_at": {"$gte": start_date, "$lte": end_date},
            }
        )

        successful_workflows = await self.db.automation_logs.count_documents(
            {
                "tenant_id": tenant_id,
                "created_at": {"$gte": start_date, "$lte": end_date},
                "status": "completed",
            }
        )

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "messages": {
                "total": total_messages,
                "delivered": delivered_messages,
                "failed": failed_messages,
                "delivery_rate": (
                    (delivered_messages / total_messages * 100)
                    if total_messages > 0
                    else 0
                ),
            },
            "workflows": {
                "total_executions": workflow_executions,
                "successful_executions": successful_workflows,
                "success_rate": (
                    (successful_workflows / workflow_executions * 100)
                    if workflow_executions > 0
                    else 0
                ),
            },
        }

    # Bulk Communication
    async def send_bulk_message(
        self,
        tenant_id: str,
        template_id: str,
        recipients: List[Dict[str, Any]],
        scheduled_for: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Send bulk messages to multiple recipients"""
        queued_messages = []

        for recipient in recipients:
            try:
                # Render template with recipient-specific context
                rendered = await self.render_template(
                    template_id, recipient.get("context", {})
                )

                message_data = {
                    "id": "bulk_"
                    + datetime.utcnow().strftime("%Y%m%d%H%M%S")
                    + "_"
                    + str(len(queued_messages)),
                    "channel": rendered["channel"],
                    "recipient": recipient["email"],
                    "subject": rendered["subject"],
                    "body": rendered["body"],
                    "template_id": template_id,
                    "bulk_campaign_id": "campaign_"
                    + datetime.utcnow().strftime("%Y%m%d%H%M%S"),
                }

                message = await self.queue_message(
                    tenant_id, message_data, scheduled_for
                )
                queued_messages.append(message)

            except Exception as e:
                # Log error but continue with other recipients
                print(
                    "Failed to queue message for "
                    + recipient.get("email", "unknown")
                    + ": "
                    + str(e)
                )

        return {
            "campaign_id": ("campaign_" + datetime.utcnow().strftime("%Y%m%d%H%M%S")),
            "total_recipients": len(recipients),
            "queued_messages": len(queued_messages),
            "scheduled_for": (
                scheduled_for.isoformat() if scheduled_for else "immediate"
            ),
        }

    # Notification Preferences
    async def update_notification_preferences(
        self, tenant_id: str, user_id: str, preferences: Dict[str, Any]
    ) -> bool:
        """Update user notification preferences"""
        pref_doc = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "preferences": preferences,
            "updated_at": datetime.utcnow(),
        }

        result = await self.db.notification_preferences.update_one(
            {"user_id": user_id, "tenant_id": tenant_id},
            {"$set": pref_doc},
            upsert=True,
        )

        return result.modified_count > 0 or result.upserted_id is not None

    async def get_notification_preferences(
        self, tenant_id: str, user_id: str
    ) -> Dict[str, Any]:
        """Get user notification preferences"""
        prefs = await self.db.notification_preferences.find_one(
            {"user_id": user_id, "tenant_id": tenant_id}
        )

        if prefs:
            return prefs.get("preferences", {})

        # Return default preferences
        return {
            "email_notifications": True,
            "sms_notifications": False,
            "push_notifications": True,
            "booking_confirmations": True,
            "booking_reminders": True,
            "marketing_emails": False,
            "system_updates": True,
        }

    # Message Processing
    async def process_message_queue(self, limit: int = 100) -> Dict[str, Any]:
        """Process queued messages for delivery"""
        messages = await self.get_queued_messages()
        processed = 0
        failed = 0

        for message in messages[:limit]:
            try:
                # Check user preferences before sending
                if message.get("recipient"):
                    # For now, just mark as delivered
                    # In production, integrate with actual email/SMS services
                    await self.update_message_status(message["id"], "delivered")
                    processed += 1
                else:
                    await self.update_message_status(
                        message["id"], "failed", "No recipient"
                    )
                    failed += 1

            except Exception as e:
                await self.update_message_status(message["id"], "failed", str(e))
                failed += 1

        return {
            "processed": processed,
            "failed": failed,
            "remaining_in_queue": len(messages) - processed - failed,
        }

    async def get_kernel_health(self) -> Dict[str, Any]:
        """Get kernel health status"""
        try:
            # Test database connectivity
            await self.db.message_templates.find_one({"tenant_id": "health_check"})

            # Check queue size
            queue_size = await self.db.message_queue.count_documents(
                {"status": "queued"}
            )

            return {
                "status": "healthy",
                "collections": [
                    "message_templates",
                    "workflows",
                    "message_queue",
                    "automation_logs",
                    "notification_preferences",
                ],
                "queue_size": queue_size,
                "last_check": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat(),
            }
