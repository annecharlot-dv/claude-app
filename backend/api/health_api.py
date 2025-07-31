"""
Health Check API
Provides comprehensive health monitoring for all platform components
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Request

from middleware.tenant_middleware import get_tenant_id_from_request

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("/")
async def basic_health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Claude Platform API",
    }


@router.get("/detailed")
async def detailed_health_check(request: Request):
    """Detailed health check for all platform components"""
    try:
        platform_core = request.app.state.platform_core

        # Check all kernels
        kernel_health = {}
        for kernel_name, kernel in platform_core.kernels.items():
            try:
                health = await kernel.get_kernel_health()
                kernel_health[kernel_name] = health
            except Exception as e:
                kernel_health[kernel_name] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "last_check": datetime.utcnow().isoformat(),
                }

        # Check database connectivity
        try:
            from database.config.connection_pool import PostgreSQLConnectionManager

            connection_manager = PostgreSQLConnectionManager()
            health_result = await connection_manager.health_check()

            if health_result["status"] == "healthy":
                db_status = "healthy"
                db_error = None
            else:
                db_status = "unhealthy"
                db_error = health_result.get("error", "Unknown error")
        except Exception as e:
            db_status = "unhealthy"
            db_error = str(e)

        # Overall platform health
        overall_status = "healthy"
        if (
            any(k["status"] != "healthy" for k in kernel_health.values())
            or db_status != "healthy"
        ):
            overall_status = "unhealthy"

        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "database": {"status": db_status, "error": db_error},
                "kernels": kernel_health,
                "active_modules": len(platform_core.active_modules),
                "platform_core": {"status": "healthy", "initialized": True},
            },
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
        }


@router.get("/tenant")
async def tenant_health_check(
    request: Request, tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Health check for specific tenant"""
    try:
        platform_core = request.app.state.platform_core

        # Get tenant information
        tenant_repo = request.app.state.tenant_repo
        tenant = await tenant_repo.get_tenant_by_id(tenant_id)

        if not tenant:
            return {
                "status": "unhealthy",
                "error": "Tenant not found",
                "tenant_id": tenant_id,
            }

        # Check tenant-specific data
        tenant_stats = await tenant_repo.get_tenant_stats(tenant_id)

        # Get tenant module health
        try:
            module = await platform_core.load_tenant_module(tenant_id)
            module_status = "healthy"
            module_info = {
                "name": module.get_module_name(),
                "version": module.get_module_version(),
                "industry": module.get_industry_type(),
            }
        except Exception as e:
            module_status = "unhealthy"
            module_info = {"error": str(e)}

        return {
            "status": "healthy" if tenant.status == "active" else "warning",
            "timestamp": datetime.utcnow().isoformat(),
            "tenant": {
                "id": tenant.id,
                "name": tenant.name,
                "subdomain": tenant.subdomain,
                "status": tenant.status,
                "subscription_plan": tenant.subscription_plan,
                "industry": tenant.industry,
            },
            "module": {"status": module_status, "info": module_info},
            "stats": tenant_stats,
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "tenant_id": tenant_id,
            "error": str(e),
        }


@router.get("/kernels")
async def kernels_health_check(request: Request):
    """Health check for all kernels"""
    try:
        platform_core = request.app.state.platform_core

        kernel_health = {}
        for kernel_name, kernel in platform_core.kernels.items():
            try:
                health = await kernel.get_kernel_health()
                kernel_health[kernel_name] = health
            except Exception as e:
                kernel_health[kernel_name] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "last_check": datetime.utcnow().isoformat(),
                }

        overall_status = "healthy"
        if any(k["status"] != "healthy" for k in kernel_health.values()):
            overall_status = "unhealthy"

        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "kernels": kernel_health,
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
        }


@router.get("/database")
async def database_health_check(request: Request):
    """Database connectivity and performance check"""
    try:
        # Test basic connectivity
        from database.config.connection_pool import PostgreSQLConnectionManager

        connection_manager = PostgreSQLConnectionManager()

        start_time = datetime.utcnow()
        health_result = await connection_manager.health_check()
        ping_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        tables_status = {}
        test_tables = ["tenants", "users", "leads", "forms", "pages"]

        async with connection_manager.get_session() as session:
            from sqlalchemy import text

            for table_name in test_tables:
                try:
                    result = await session.execute(
                        text(f"SELECT COUNT(*) FROM {table_name}")
                    )
                    count = result.scalar()
                    tables_status[table_name] = {
                        "status": "healthy",
                        "record_count": count,
                    }
                except Exception as e:
                    tables_status[table_name] = {"status": "unhealthy", "error": str(e)}

        return {
            "status": (
                "healthy" if health_result["status"] == "healthy" else "unhealthy"
            ),
            "timestamp": datetime.utcnow().isoformat(),
            "ping_time_ms": round(ping_time, 2),
            "database_stats": {
                "connection_pools": health_result.get("pools", {}),
                "active_connections": health_result.get("active_connections", 0),
                "pool_status": health_result.get("pool_status", "unknown"),
            },
            "tables": tables_status,
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
        }
