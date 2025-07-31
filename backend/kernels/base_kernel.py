"""
Base Kernel - Abstract base class for all kernels
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession


class BaseKernel(ABC):
    """Abstract base class for all kernels in the Claude Platform"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._initialized = False

    async def initialize(self):
        """Initialize the kernel - called once during system startup"""
        if not self._initialized:
            await self._initialize_kernel()
            self._initialized = True

    @abstractmethod
    async def _initialize_kernel(self):
        """Kernel-specific initialization logic"""
        pass

    @abstractmethod
    async def validate_tenant_access(self, tenant_id: str, user_id: str) -> bool:
        """Validate that user has access to tenant resources"""
        pass

    def get_kernel_name(self) -> str:
        """Get the name of this kernel"""
        return self.__class__.__name__

    async def get_kernel_health(self) -> Dict[str, Any]:
        """Get health status of this kernel"""
        return {
            "kernel": self.get_kernel_name(),
            "initialized": self._initialized,
            "status": "healthy" if self._initialized else "not_initialized",
        }
