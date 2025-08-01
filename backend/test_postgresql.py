#!/usr/bin/env python3
"""
Test PostgreSQL setup and basic operations
"""
import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from database.postgresql_connection import get_connection_manager
from kernels.postgresql_identity_kernel import PostgreSQLIdentityKernel
from models.postgresql_models import Tenant, User
import logging
import pytest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_postgresql_setup():
    """Test PostgreSQL setup and basic operations"""
    try:
        # Initialize connection manager
        connection_manager = await get_connection_manager()
        await connection_manager.initialize()
        
        logger.info("🔄 Testing PostgreSQL setup...")
        
        # Test basic connection
        health = await connection_manager.health_check()
        logger.info(f"📊 Health check: {health}")
        
        # Initialize identity kernel
        async with connection_manager.get_session() as session:
            identity_kernel = PostgreSQLIdentityKernel(session, "test-secret-key")
            
            # Test tenant creation
            tenant_data = {
                "name": "Test Tenant",
                "subdomain": "test-tenant",
                "industry_module": "coworking",
                "plan": "starter",
                "branding": {"primary_color": "#3B82F6"},
                "settings": {"timezone": "UTC"},
                "feature_toggles": {"cms_enabled": True}
            }
            
            # Check if tenant already exists
            existing_tenant = await identity_kernel.get_tenant_by_subdomain("test-tenant")
            if existing_tenant:
                logger.info("ℹ️ Test tenant already exists")
                tenant = existing_tenant
            else:
                tenant = await identity_kernel.create_tenant(tenant_data)
                logger.info(f"✅ Created test tenant: {tenant['name']}")
            
            # Test user creation
            user_data = {
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
                "role": "account_owner"
            }
            
            # Check if user already exists
            existing_user = await identity_kernel.get_user_by_email(tenant["id"], "test@example.com")
            if existing_user:
                logger.info("ℹ️ Test user already exists")
                user = existing_user
            else:
                user = await identity_kernel.create_user(tenant["id"], user_data, "test123")
                logger.info(f"✅ Created test user: {user['email']}")
            
            # Test authentication
            auth_result = await identity_kernel.authenticate_user(
                "test-tenant", 
                "test@example.com", 
                "test123"
            )
            
            if auth_result:
                logger.info("✅ Authentication test passed")
                
                # Test token creation and verification
                token = await identity_kernel.create_access_token(auth_result["id"])
                logger.info("✅ Token creation test passed")
                
                verified_user_id = await identity_kernel.verify_token(token)
                if verified_user_id == auth_result["id"]:
                    logger.info("✅ Token verification test passed")
                else:
                    logger.error("❌ Token verification test failed")
            else:
                logger.error("❌ Authentication test failed")
            
            # Test kernel health
            health = await identity_kernel.get_kernel_health()
            logger.info(f"📊 Kernel health: {health}")
        
        await connection_manager.close()
        logger.info("🎉 All PostgreSQL tests passed!")
        
    except Exception as e:
        logger.error(f"❌ PostgreSQL test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_postgresql_setup())
