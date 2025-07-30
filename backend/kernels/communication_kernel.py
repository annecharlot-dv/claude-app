"""
Automation & Communication Kernel (The "Messenger")
Universal communication and workflow automation engine
"""
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum
from kernels.base_kernel import BaseKernel


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
    
    def __init__(self, db):
        super().__init__(db)
        self.workflows = {}
        self.message_handlers = {}
        self.triggers = {}
    
    async def _initialize_kernel(self):
        """Initialize communication kernel"""
        # Ensure indexes exist
        await self.db.message_templates.create_index([("tenant_id", 1), ("template_type", 1)])
        await self.db.workflows.create_index([("tenant_id", 1), ("trigger_event", 1)])
        await self.db.message_queue.create_index([("tenant_id", 1), ("status", 1), ("scheduled_for", 1)])
        await self.db.automation_logs.create_index([("tenant_id", 1), ("created_at", -1)])
    
    async def validate_tenant_access(self, tenant_id: str, user_id: str) -> bool:
        """Validate user belongs to tenant"""
        user = await self.db.users.find_one({"id": user_id, "tenant_id": tenant_id})
        return user is not None
    
    # Message Template Management
    async def create_message_template(self, tenant_id: str, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new message template"""
        template_doc = {
            **template_data,
            "tenant_id": tenant_id,
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        await self.db.message_templates.insert_one(template_doc)
        return template_doc
    
    async def get_message_templates(self, tenant_id: str, template_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get message templates for tenant"""
        query = {"tenant_id": tenant_id, "is_active": True}
        if template_type:
            query["template_type"] = template_type
        
        templates = await self.db.message_templates.find(query).to_list(1000)
        return templates
    
    async def render_template(self, template_id: str, context: Dict[str, Any]) -> Dict[str, str]:
        """Render a message template with context data"""
        template = await self.db.message_templates.find_one({"id": template_id})
        if not template:
            raise ValueError("Template not found")
        
        # Simple template rendering (in production, use a proper template engine)
        subject = template.get("subject", "")
        body = template.get("body", "")
        
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            subject = subject.replace(placeholder, str(value))
            body = body.replace(placeholder, str(value))
        
        return {
            "subject": subject,
            "body": body,
            "channel": template.get("channel", MessageChannel.EMAIL)
        }
    
    # Workflow Management
    async def create_workflow(self, tenant_id: str, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an automation workflow"""
        workflow_doc = {
            **workflow_data,
            "tenant_id": tenant_id,
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        await self.db.workflows.insert_one(workflow_doc)
        return workflow_doc
    
    async def get_workflows(self, tenant_id: str, trigger_event: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get workflows for tenant"""
        query = {"tenant_id": tenant_id, "is_active": True}
        if trigger_event:
            query["trigger_event"] = trigger_event
        
        workflows = await self.db.workflows.find(query).to_list(1000)
        return workflows
    
    # Message Queue Management
    async def queue_message(self, tenant_id: str, message_data: Dict[str, Any], 
                          scheduled_for: Optional[datetime] = None) -> Dict[str, Any]:
        """Queue a message for delivery"""
        message_doc = {
            **message_data,
            "tenant_id": tenant_id,
            "status": "queued",
            "scheduled_for": scheduled_for or datetime.utcnow(),
            "attempts": 0,
            "max_attempts": 3,
            "created_at": datetime.utcnow()
        }
        await self.db.message_queue.insert_one(message_doc)
        return message_doc
    
    async def get_queued_messages(self, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get messages ready for delivery"""
        query = {
            "status": "queued",
            "scheduled_for": {"$lte": datetime.utcnow()}
        }
        if tenant_id:
            query["tenant_id"] = tenant_id
        
        messages = await self.db.message_queue.find(query).limit(100).to_list(100)
        return messages
    
    async def update_message_status(self, message_id: str, status: str, error: Optional[str] = None):
        """Update message delivery status"""
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow(),
            "$inc": {"attempts": 1}
        }
        if error:
            update_data["last_error"] = error
        
        await self.db.message_queue.update_one(
            {"id": message_id},
            {"$set": update_data}
        )
    
    # Event Triggers
    async def trigger_event(self, tenant_id: str, event: TriggerEvent, context: Dict[str, Any]):
        """Trigger an event and execute associated workflows"""
        # Get workflows for this event
        workflows = await self.get_workflows(tenant_id, event.value)
        
        for workflow in workflows:
            await self._execute_workflow(tenant_id, workflow, context)
    
    async def _execute_workflow(self, tenant_id: str, workflow: Dict[str, Any], context: Dict[str, Any]):
        """Execute a workflow"""
        try:
            # Log workflow execution
            log_entry = {
                "id": f"log_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                "tenant_id": tenant_id,
                "workflow_id": workflow["id"],
                "trigger_event": workflow["trigger_event"],
                "context": context,
                "status": "started",
                "created_at": datetime.utcnow()
            }
            await self.db.automation_logs.insert_one(log_entry)
            
            # Execute workflow actions
            for action in workflow.get("actions", []):
                await self._execute_action(tenant_id, action, context)
            
            # Update log status
            await self.db.automation_logs.update_one(
                {"id": log_entry["id"]},
                {"$set": {"status": "completed", "completed_at": datetime.utcnow()}}
            )
            
        except Exception as e:
            # Log error
            await self.db.automation_logs.update_one(
                {"id": log_entry["id"]},
                {"$set": {"status": "failed", "error": str(e), "completed_at": datetime.utcnow()}}
            )
    
    async def _execute_action(self, tenant_id: str, action: Dict[str, Any], context: Dict[str, Any]):
        """Execute a single workflow action"""
        action_type = action.get("type")
        
        if action_type == "send_message":
            template_id = action.get("template_id")
            recipient = action.get("recipient", context.get("user_email"))
            
            if template_id and recipient:
                rendered = await self.render_template(template_id, context)
                
                message_data = {
                    "id": f"msg_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    "channel": rendered["channel"],
                    "recipient": recipient,
                    "subject": rendered["subject"],
                    "body": rendered["body"],
                    "template_id": template_id
                }
                
                await self.queue_message(tenant_id, message_data)
        
        elif action_type == "update_status":
            # Update status of related entity
            entity_type = action.get("entity_type")
            entity_id = context.get(f"{entity_type}_id")
            new_status = action.get("status")
            
            if entity_type and entity_id and new_status:
                collection = getattr(self.db, f"{entity_type}s", None)
                if collection:
                    await collection.update_one(
                        {"id": entity_id},
                        {"$set": {"status": new_status, "updated_at": datetime.utcnow()}}
                    )
        
        elif action_type == "webhook":
            # Queue webhook call
            webhook_url = action.get("url")
            if webhook_url:
                webhook_data = {
                    "id": f"hook_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    "channel": MessageChannel.WEBHOOK,
                    "url": webhook_url,
                    "payload": context,
                    "method": action.get("method", "POST")
                }
                await self.queue_message(tenant_id, webhook_data)
    
    # Analytics and Reporting
    async def get_communication_stats(self, tenant_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get communication statistics"""
        # Message delivery stats
        total_messages = await self.db.message_queue.count_documents({
            "tenant_id": tenant_id,
            "created_at": {"$gte": start_date, "$lte": end_date}
        })
        
        delivered_messages = await self.db.message_queue.count_documents({
            "tenant_id": tenant_id,
            "created_at": {"$gte": start_date, "$lte": end_date},
            "status": "delivered"
        })
        
        failed_messages = await self.db.message_queue.count_documents({
            "tenant_id": tenant_id,
            "created_at": {"$gte": start_date, "$lte": end_date},
            "status": "failed"
        })
        
        # Workflow execution stats
        workflow_executions = await self.db.automation_logs.count_documents({
            "tenant_id": tenant_id,
            "created_at": {"$gte": start_date, "$lte": end_date}
        })
        
        successful_workflows = await self.db.automation_logs.count_documents({
            "tenant_id": tenant_id,
            "created_at": {"$gte": start_date, "$lte": end_date},
            "status": "completed"
        })
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "messages": {
                "total": total_messages,
                "delivered": delivered_messages,
                "failed": failed_messages,
                "delivery_rate": (delivered_messages / total_messages * 100) if total_messages > 0 else 0
            },
            "workflows": {
                "total_executions": workflow_executions,
                "successful_executions": successful_workflows,
                "success_rate": (successful_workflows / workflow_executions * 100) if workflow_executions > 0 else 0
            }
        }