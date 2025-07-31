"""
Comprehensive audit logging system for compliance and security monitoring
"""
import asyncio
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class AuditEventType(Enum):
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    BOOKING_CREATED = "booking_created"
    BOOKING_UPDATED = "booking_updated"
    BOOKING_CANCELLED = "booking_cancelled"
    PAYMENT_PROCESSED = "payment_processed"
    DATA_EXPORT = "data_export"
    ADMIN_ACTION = "admin_action"
    SECURITY_VIOLATION = "security_violation"
    TENANT_CREATED = "tenant_created"
    TENANT_UPDATED = "tenant_updated"
    PERMISSION_CHANGED = "permission_changed"

class AuditSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AuditLogger:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.audit_logs
        
    async def log_event(
        self,
        event_type: AuditEventType,
        tenant_id: str,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: AuditSeverity = AuditSeverity.LOW,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """Log an audit event with tamper-proof integrity"""
        
        timestamp = datetime.now(timezone.utc)
        
        # Create base audit record
        audit_record = {
            "_id": ObjectId(),
            "event_type": event_type.value,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "resource_id": resource_id,
            "resource_type": resource_type,
            "timestamp": timestamp,
            "severity": severity.value,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "session_id": session_id,
            "details": details or {},
            "compliance_flags": self._get_compliance_flags(event_type),
        }
        
        # Add integrity hash
        audit_record["integrity_hash"] = self._calculate_integrity_hash(audit_record)
        
        try:
            # Insert audit record
            result = await self.collection.insert_one(audit_record)
            
            # Check for security violations that need immediate attention
            if severity in [AuditSeverity.HIGH, AuditSeverity.CRITICAL]:
                await self._trigger_security_alert(audit_record)
            
            logger.info(f"Audit event logged: {event_type.value} for tenant {tenant_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            # In production, you might want to send this to a backup logging system
            raise
    
    def _calculate_integrity_hash(self, record: Dict[str, Any]) -> str:
        """Calculate tamper-proof hash for audit record"""
        # Remove fields that shouldn't be part of the hash
        hash_data = {k: v for k, v in record.items() 
                    if k not in ['_id', 'integrity_hash']}
        
        # Convert to deterministic JSON string
        json_str = json.dumps(hash_data, sort_keys=True, default=str)
        
        # Calculate SHA-256 hash
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def _get_compliance_flags(self, event_type: AuditEventType) -> List[str]:
        """Get compliance framework flags for the event type"""
        flags = []
        
        # GDPR flags
        gdpr_events = [
            AuditEventType.USER_CREATED,
            AuditEventType.USER_UPDATED,
            AuditEventType.USER_DELETED,
            AuditEventType.DATA_EXPORT
        ]
        if event_type in gdpr_events:
            flags.append("GDPR")
        
        # SOC 2 flags
        soc2_events = [
            AuditEventType.USER_LOGIN,
            AuditEventType.USER_LOGOUT,
            AuditEventType.ADMIN_ACTION,
            AuditEventType.SECURITY_VIOLATION,
            AuditEventType.PERMISSION_CHANGED
        ]
        if event_type in soc2_events:
            flags.append("SOC2")
        
        # HIPAA flags (if applicable)
        hipaa_events = [
            AuditEventType.DATA_EXPORT,
            AuditEventType.USER_DELETED,
            AuditEventType.SECURITY_VIOLATION
        ]
        if event_type in hipaa_events:
            flags.append("HIPAA")
        
        return flags
    
    async def _trigger_security_alert(self, audit_record: Dict[str, Any]):
        """Trigger immediate security alert for high-severity events"""
        alert_data = {
            "timestamp": audit_record["timestamp"].isoformat(),
            "event_type": audit_record["event_type"],
            "tenant_id": audit_record["tenant_id"],
            "severity": audit_record["severity"],
            "details": audit_record["details"],
            "ip_address": audit_record["ip_address"]
        }
        
        # Send to security monitoring system
        # This could be Slack, PagerDuty, email, etc.
        logger.critical(f"SECURITY ALERT: {json.dumps(alert_data)}")
    
    async def verify_integrity(self, audit_id: str) -> bool:
        """Verify the integrity of an audit record"""
        try:
            record = await self.collection.find_one({"_id": ObjectId(audit_id)})
            if not record:
                return False
            
            stored_hash = record.pop("integrity_hash", None)
            calculated_hash = self._calculate_integrity_hash(record)
            
            return stored_hash == calculated_hash
            
        except Exception as e:
            logger.error(f"Failed to verify audit record integrity: {e}")
            return False
    
    async def get_audit_trail(
        self,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[AuditEventType]] = None,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get audit trail with filtering options"""
        
        query = {"tenant_id": tenant_id}
        
        # Date range filter
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            query["timestamp"] = date_filter
        
        # Event type filter
        if event_types:
            query["event_type"] = {"$in": [et.value for et in event_types]}
        
        # User filter
        if user_id:
            query["user_id"] = user_id
        
        try:
            cursor = self.collection.find(query).sort("timestamp", -1).limit(limit)
            records = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string for JSON serialization
            for record in records:
                record["_id"] = str(record["_id"])
                if isinstance(record["timestamp"], datetime):
                    record["timestamp"] = record["timestamp"].isoformat()
            
            return records
            
        except Exception as e:
            logger.error(f"Failed to retrieve audit trail: {e}")
            return []
    
    async def generate_compliance_report(
        self,
        tenant_id: str,
        compliance_framework: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate compliance report for specific framework"""
        
        query = {
            "tenant_id": tenant_id,
            "timestamp": {"$gte": start_date, "$lte": end_date},
            "compliance_flags": compliance_framework
        }
        
        try:
            # Get all relevant audit records
            cursor = self.collection.find(query).sort("timestamp", 1)
            records = await cursor.to_list(length=None)
            
            # Generate report statistics
            report = {
                "tenant_id": tenant_id,
                "compliance_framework": compliance_framework,
                "report_period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "total_events": len(records),
                "event_breakdown": {},
                "security_incidents": 0,
                "data_access_events": 0,
                "user_management_events": 0,
                "high_risk_events": []
            }
            
            # Analyze events
            for record in records:
                event_type = record["event_type"]
                report["event_breakdown"][event_type] = report["event_breakdown"].get(event_type, 0) + 1
                
                if record["severity"] in ["high", "critical"]:
                    report["security_incidents"] += 1
                    report["high_risk_events"].append({
                        "timestamp": record["timestamp"].isoformat(),
                        "event_type": event_type,
                        "severity": record["severity"],
                        "details": record["details"]
                    })
                
                if event_type in ["data_export", "user_deleted"]:
                    report["data_access_events"] += 1
                
                if event_type in ["user_created", "user_updated", "user_deleted", "permission_changed"]:
                    report["user_management_events"] += 1
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate compliance report: {e}")
            return {"error": str(e)}

# Decorator for automatic audit logging
def audit_action(event_type: AuditEventType, severity: AuditSeverity = AuditSeverity.LOW):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract audit context from function arguments
            # This assumes certain parameter names - adjust as needed
            tenant_id = kwargs.get('tenant_id') or getattr(args[0], 'tenant_id', None)
            user_id = kwargs.get('user_id') or getattr(args[0], 'user_id', None)
            
            try:
                result = await func(*args, **kwargs)
                
                # Log successful action
                if hasattr(args[0], 'audit_logger'):
                    await args[0].audit_logger.log_event(
                        event_type=event_type,
                        tenant_id=tenant_id,
                        user_id=user_id,
                        severity=severity,
                        details={"function": func.__name__, "success": True}
                    )
                
                return result
                
            except Exception as e:
                # Log failed action
                if hasattr(args[0], 'audit_logger'):
                    await args[0].audit_logger.log_event(
                        event_type=event_type,
                        tenant_id=tenant_id,
                        user_id=user_id,
                        severity=AuditSeverity.HIGH,
                        details={"function": func.__name__, "success": False, "error": str(e)}
                    )
                raise
        
        return wrapper
    return decorator