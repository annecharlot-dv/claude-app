"""
Module Registry - Runtime module loading and management
"""

from typing import Any, Dict, Optional

from modules.base_module import BaseModule
from modules.coworking_module import CoworkingModule
from modules.creative_studio_module import CreativeStudioModule
from modules.government_module import GovernmentModule
from modules.hotel_module import HotelModule
from modules.residential_module import ResidentialModule
from modules.university_module import UniversityModule


class ModuleRegistry:
    """Registry for managing and loading industry modules"""

    def __init__(self):
        self._modules = {}
        self._register_default_modules()

    def _register_default_modules(self):
        """Register default modules"""
        self._modules["coworking"] = CoworkingModule
        self._modules["government"] = GovernmentModule
        self._modules["hotel"] = HotelModule
        self._modules["university"] = UniversityModule
        self._modules["creative_studio"] = CreativeStudioModule
        self._modules["residential"] = ResidentialModule

    def register_module(self, industry_type: str, module_class: type):
        """Register a new module"""
        if not issubclass(module_class, BaseModule):
            raise ValueError("Module must inherit from BaseModule")
        self._modules[industry_type] = module_class

    def get_available_modules(self) -> Dict[str, str]:
        """Get list of available modules"""
        return {
            industry: module_class.__name__
            for industry, module_class in self._modules.items()
        }

    def load_module(self, tenant_data: Dict[str, Any]) -> BaseModule:
        """Load and instantiate module for tenant"""
        industry_module = tenant_data.get("industry_module")

        if industry_module not in self._modules:
            raise ValueError(f"Unknown industry module: {industry_module}")

        module_class = self._modules[industry_module]
        return module_class(tenant_data)

    def validate_module_config(
        self, industry_type: str, config: Dict[str, Any]
    ) -> tuple[bool, list[str]]:
        """Validate module configuration"""
        if industry_type not in self._modules:
            return False, [f"Unknown module type: {industry_type}"]

        # Additional validation can be added here
        return True, []


# Global module registry instance
module_registry = ModuleRegistry()


def get_module_registry() -> ModuleRegistry:
    """Get the global module registry"""
    return module_registry


def load_tenant_module(tenant_data: Dict[str, Any]) -> BaseModule:
    """Convenience function to load module for tenant"""
    return module_registry.load_module(tenant_data)
