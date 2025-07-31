#!/usr/bin/env python3

import asyncio
import os
from database.config.connection_pool import PostgreSQLConnectionManager
from claude_platform_core import get_platform_core

async def debug_permissions():
    # Connect to database
    database_url = os.environ.get('DATABASE_URL', 'postgresql://localhost:5432/claude_platform_dev')
    connection_manager = PostgreSQLConnectionManager()
    
    # Get platform core
    async with connection_manager.get_session() as session:
        core = await get_platform_core(session)
        identity_kernel = core.get_kernel('identity')
        
        # Find a test user (account owner from downtown-hub)
        from models.postgresql_models import User
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(
                User.email == "admin@downtownhub.com",
                User.role == "account_owner"
            )
        )
        user = result.scalar_one_or_none()
    
        if user:
            print(f"Found user: {user.email} with role: {user.role}")
            print(f"User ID: {user.id}")
            
            # Check permissions
            permissions = await identity_kernel.get_user_permissions(user.id)
            print(f"User permissions: {permissions}")
            
            # Test specific permission checks
            test_permissions = [
                "role.account_owner",
                "pages.manage",
                "leads.manage",
                "forms.manage"
            ]
            
            for perm in test_permissions:
                has_perm = await identity_kernel.check_permission(user.id, perm)
                print(f"Permission '{perm}': {has_perm}")
            
            # Test platform core permission check
            has_platform_perm = await core.check_user_permission(
                user.tenant_id, 
                user.id, 
                "role.account_owner"
            )
            print(f"Platform core permission check for 'role.account_owner': {has_platform_perm}")
            
        else:
            print("No test user found")

if __name__ == "__main__":
    asyncio.run(debug_permissions())
