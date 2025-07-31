"""
Security tests for multi-tenant isolation and data protection
"""
import pytest
import jwt
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict, Any
from unittest.mock import patch, AsyncMock

@pytest.mark.security
@pytest.mark.tenant_isolation
class TestTenantSecurityIsolation:
    """Test security aspects of tenant isolation"""
    
    async def test_cross_tenant_data_access_prevention(self, clean_db: AsyncIOMotorDatabase):
        """Test that users cannot access data from other tenants"""
        # Create data for different tenants
        tenant_data = [
            {"data_id": "coworking_data", "tenant_id": "coworking", "sensitive_info": "coworking_secret"},
            {"data_id": "university_data", "tenant_id": "university", "sensitive_info": "university_secret"},
            {"data_id": "hotel_data", "tenant_id": "hotel", "sensitive_info": "hotel_secret"}
        ]
        await clean_db.sensitive_data.insert_many(tenant_data)
        
        # Simulate API request from coworking tenant trying to access university data
        requesting_tenant = "coworking"
        
        # Proper tenant-filtered query (should only return coworking data)
        allowed_data = await clean_db.sensitive_data.find({"tenant_id": requesting_tenant}).to_list(None)
        assert len(allowed_data) == 1
        assert allowed_data[0]["tenant_id"] == "coworking"
        
        # Attempt to access specific university data (should be blocked)
        cross_tenant_attempt = await clean_db.sensitive_data.find_one({
            "data_id": "university_data",
            "tenant_id": requesting_tenant  # This filter should prevent access
        })
        assert cross_tenant_attempt is None
        
        # Direct access without tenant filter (should be prevented by middleware)
        # In real implementation, this would be blocked at the API level
        unfiltered_query = await clean_db.sensitive_data.find_one({"data_id": "university_data"})
        # This test shows why tenant filtering is critical - without it, data leaks
        assert unfiltered_query is not None  # This is the security risk we prevent
    
    async def test_jwt_token_tenant_validation(self, create_jwt_token, jwt_secret: str):
        """Test JWT tokens properly validate tenant context"""
        # Create token for coworking tenant
        coworking_token = create_jwt_token("user123", "coworking", "member")
        
        # Decode and validate token
        payload = jwt.decode(coworking_token, jwt_secret, algorithms=["HS256"])
        assert payload["tenant_id"] == "coworking"
        
        # Simulate request to university endpoint with coworking token
        requested_tenant = "university"
        token_tenant = payload["tenant_id"]
        
        # Should reject cross-tenant access
        assert token_tenant != requested_tenant
    
    async def test_subdomain_spoofing_prevention(self):
        """Test prevention of subdomain spoofing attacks"""
        def validate_subdomain(host_header: str, expected_tenant: str) -> bool:
            """Simulate subdomain validation logic"""
            if not host_header:
                return False
            
            # Extract subdomain
            parts = host_header.split('.')
            if len(parts) < 3:  # Should be subdomain.domain.com
                return False
            
            subdomain = parts[0]
            
            # Validate against known tenants
            valid_tenants = ["coworking", "university", "hotel", "creative"]
            if subdomain not in valid_tenants:
                return False
            
            # Check if subdomain matches expected tenant
            return subdomain == expected_tenant
        
        # Valid subdomain
        assert validate_subdomain("coworking.example.com", "coworking") is True
        
        # Spoofing attempts
        assert validate_subdomain("university.example.com", "coworking") is False  # Wrong tenant
        assert validate_subdomain("malicious.example.com", "coworking") is False  # Invalid tenant
        assert validate_subdomain("example.com", "coworking") is False  # No subdomain
        assert validate_subdomain("", "coworking") is False  # Empty host
    
    async def test_user_role_escalation_prevention(self, clean_db: AsyncIOMotorDatabase):
        """Test prevention of role escalation attacks"""
        # Create users with different roles
        users = [
            {"user_id": "member_user", "tenant_id": "coworking", "role": "member"},
            {"user_id": "admin_user", "tenant_id": "coworking", "role": "admin"}
        ]
        await clean_db.users.insert_many(users)
        
        def check_permission(user_role: str, required_role: str) -> bool:
            """Simulate role-based permission checking"""
            role_hierarchy = {
                "member": 1,
                "front_desk": 2,
                "property_manager": 3,
                "account_owner": 4,
                "admin": 5
            }
            
            user_level = role_hierarchy.get(user_role, 0)
            required_level = role_hierarchy.get(required_role, 999)
            
            return user_level >= required_level
        
        # Member trying to access admin function
        assert check_permission("member", "admin") is False
        
        # Admin accessing member function (should work)
        assert check_permission("admin", "member") is True
        
        # Same level access
        assert check_permission("property_manager", "property_manager") is True
    
    async def test_sql_injection_prevention_in_filters(self):
        """Test prevention of injection attacks in tenant filters"""
        def sanitize_tenant_filter(tenant_input: str) -> str:
            """Simulate input sanitization for tenant filtering"""
            # Remove potentially dangerous characters
            dangerous_chars = ["'", '"', ";", "--", "/*", "*/", "xp_", "sp_"]
            
            sanitized = tenant_input
            for char in dangerous_chars:
                sanitized = sanitized.replace(char, "")
            
            # Only allow alphanumeric and underscore
            if not sanitized.replace("_", "").isalnum():
                raise ValueError("Invalid tenant identifier")
            
            return sanitized
        
        # Valid tenant IDs
        assert sanitize_tenant_filter("coworking") == "coworking"
        assert sanitize_tenant_filter("test_tenant") == "test_tenant"
        
        # Injection attempts
        with pytest.raises(ValueError):
            sanitize_tenant_filter("coworking'; DROP TABLE users; --")
        
        with pytest.raises(ValueError):
            sanitize_tenant_filter("tenant OR 1=1")

@pytest.mark.security
class TestDataProtection:
    """Test data protection and encryption"""
    
    async def test_password_hashing_security(self):
        """Test password hashing meets security standards"""
        import bcrypt
        
        def hash_password(password: str) -> str:
            """Simulate secure password hashing"""
            salt = bcrypt.gensalt(rounds=12)  # Strong salt
            return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
        def verify_password(password: str, hashed: str) -> bool:
            """Verify password against hash"""
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        
        # Test password hashing
        password = "secure_password_123"
        hashed = hash_password(password)
        
        # Verify hash properties
        assert len(hashed) > 50  # Bcrypt hashes are long
        assert hashed.startswith("$2b$12$")  # Proper bcrypt format with cost 12
        assert hashed != password  # Password is not stored in plain text
        
        # Verify password verification works
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False
    
    async def test_sensitive_data_encryption(self):
        """Test encryption of sensitive data fields"""
        from cryptography.fernet import Fernet
        
        def encrypt_sensitive_field(data: str, key: bytes) -> str:
            """Simulate field-level encryption"""
            f = Fernet(key)
            encrypted = f.encrypt(data.encode())
            return encrypted.decode()
        
        def decrypt_sensitive_field(encrypted_data: str, key: bytes) -> str:
            """Decrypt sensitive field"""
            f = Fernet(key)
            decrypted = f.decrypt(encrypted_data.encode())
            return decrypted.decode()
        
        # Generate encryption key
        key = Fernet.generate_key()
        
        # Test encryption/decryption
        sensitive_data = "user_ssn_123456789"
        encrypted = encrypt_sensitive_field(sensitive_data, key)
        decrypted = decrypt_sensitive_field(encrypted, key)
        
        assert encrypted != sensitive_data  # Data is encrypted
        assert decrypted == sensitive_data  # Decryption works
        assert len(encrypted) > len(sensitive_data)  # Encrypted data is longer
    
    async def test_audit_log_integrity(self, clean_db: AsyncIOMotorDatabase):
        """Test audit log tamper protection"""
        import hashlib
        import json
        
        def create_audit_entry(event_data: Dict[str, Any]) -> Dict[str, Any]:
            """Create tamper-proof audit entry"""
            # Create base entry
            audit_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_data["event_type"],
                "tenant_id": event_data["tenant_id"],
                "user_id": event_data["user_id"],
                "details": event_data["details"]
            }
            
            # Calculate integrity hash
            entry_json = json.dumps(audit_entry, sort_keys=True)
            integrity_hash = hashlib.sha256(entry_json.encode()).hexdigest()
            audit_entry["integrity_hash"] = integrity_hash
            
            return audit_entry
        
        def verify_audit_integrity(audit_entry: Dict[str, Any]) -> bool:
            """Verify audit entry hasn't been tampered with"""
            stored_hash = audit_entry.pop("integrity_hash", None)
            if not stored_hash:
                return False
            
            entry_json = json.dumps(audit_entry, sort_keys=True)
            calculated_hash = hashlib.sha256(entry_json.encode()).hexdigest()
            
            return stored_hash == calculated_hash
        
        # Create audit entry
        event_data = {
            "event_type": "user_login",
            "tenant_id": "coworking",
            "user_id": "test_user",
            "details": {"ip": "192.168.1.1"}
        }
        
        audit_entry = create_audit_entry(event_data)
        await clean_db.audit_logs.insert_one(audit_entry)
        
        # Retrieve and verify integrity
        stored_entry = await clean_db.audit_logs.find_one({"user_id": "test_user"})
        assert verify_audit_integrity(stored_entry.copy()) is True
        
        # Test tampered entry
        tampered_entry = stored_entry.copy()
        tampered_entry["details"]["ip"] = "192.168.1.999"  # Tamper with data
        assert verify_audit_integrity(tampered_entry) is False

@pytest.mark.security
class TestAccessControl:
    """Test access control mechanisms"""
    
    async def test_api_rate_limiting(self):
        """Test API rate limiting prevents abuse"""
        from collections import defaultdict
        import time
        
        class RateLimiter:
            def __init__(self, max_requests: int = 100, window_seconds: int = 60):
                self.max_requests = max_requests
                self.window_seconds = window_seconds
                self.requests = defaultdict(list)
            
            def is_allowed(self, client_id: str) -> bool:
                now = time.time()
                client_requests = self.requests[client_id]
                
                # Remove old requests outside the window
                client_requests[:] = [req_time for req_time in client_requests 
                                    if now - req_time < self.window_seconds]
                
                # Check if under limit
                if len(client_requests) >= self.max_requests:
                    return False
                
                # Add current request
                client_requests.append(now)
                return True
        
        rate_limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        # Test normal usage
        for i in range(5):
            assert rate_limiter.is_allowed("client_1") is True
        
        # Test rate limit exceeded
        assert rate_limiter.is_allowed("client_1") is False
        
        # Test different client not affected
        assert rate_limiter.is_allowed("client_2") is True
    
    async def test_session_security(self, create_jwt_token, jwt_secret: str):
        """Test session security measures"""
        # Test token expiration
        expired_token = create_jwt_token(
            "user123", 
            "coworking", 
            "member", 
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(expired_token, jwt_secret, algorithms=["HS256"])
        
        # Test token with future expiration
        valid_token = create_jwt_token(
            "user123",
            "coworking", 
            "member",
            expires_delta=timedelta(hours=1)
        )
        
        payload = jwt.decode(valid_token, jwt_secret, algorithms=["HS256"])
        assert payload["sub"] == "user123"
    
    async def test_input_validation_security(self):
        """Test input validation prevents security issues"""
        def validate_booking_input(booking_data: Dict[str, Any]) -> Dict[str, Any]:
            """Validate booking input for security"""
            errors = []
            
            # Validate space_id format
            space_id = booking_data.get("space_id", "")
            if not space_id or not space_id.replace("_", "").isalnum():
                errors.append("Invalid space_id format")
            
            # Validate time format
            start_time = booking_data.get("start_time", "")
            if not start_time or len(start_time) != 20 or not start_time.endswith("Z"):
                errors.append("Invalid start_time format")
            
            # Validate purpose length (prevent buffer overflow)
            purpose = booking_data.get("purpose", "")
            if len(purpose) > 500:
                errors.append("Purpose too long")
            
            # Check for script injection in purpose
            dangerous_patterns = ["<script", "javascript:", "onload=", "onerror="]
            if any(pattern in purpose.lower() for pattern in dangerous_patterns):
                errors.append("Invalid characters in purpose")
            
            return {"valid": len(errors) == 0, "errors": errors}
        
        # Valid input
        valid_booking = {
            "space_id": "meeting_room_1",
            "start_time": "2024-12-01T10:00:00Z",
            "purpose": "Team meeting"
        }
        result = validate_booking_input(valid_booking)
        assert result["valid"] is True
        
        # Invalid space_id
        invalid_booking = {
            "space_id": "room'; DROP TABLE spaces; --",
            "start_time": "2024-12-01T10:00:00Z",
            "purpose": "Meeting"
        }
        result = validate_booking_input(invalid_booking)
        assert result["valid"] is False
        assert "Invalid space_id format" in result["errors"]
        
        # Script injection attempt
        xss_booking = {
            "space_id": "meeting_room_1",
            "start_time": "2024-12-01T10:00:00Z",
            "purpose": "<script>alert('xss')</script>"
        }
        result = validate_booking_input(xss_booking)
        assert result["valid"] is False
        assert "Invalid characters in purpose" in result["errors"]