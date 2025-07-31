"""
Base Module - Abstract base class for all industry modules
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime


class BaseModule(ABC):
    """Abstract base class for all industry modules in the Claude Platform"""

    def __init__(self, tenant_data: Dict[str, Any]):
        self.tenant_data = tenant_data
        self.tenant_id = tenant_data["id"]
        self.industry_module = tenant_data["industry_module"]
        self.feature_toggles = tenant_data.get("feature_toggles", {})
        self.branding = tenant_data.get("branding", {})
        self.settings = tenant_data.get("settings", {})

    # Core Module Identity
    @abstractmethod
    def get_module_name(self) -> str:
        """Get the name of this module"""
        pass

    @abstractmethod
    def get_module_version(self) -> str:
        """Get the version of this module"""
        pass

    def get_industry_type(self) -> str:
        """Get the industry this module serves"""
        return self.industry_module

    # Terminology System
    @abstractmethod
    def get_terminology_dictionary(self) -> Dict[str, str]:
        """Get terminology overrides for this industry"""
        pass

    def translate_term(self, core_term: str) -> str:
        """Translate a core platform term to industry-specific terminology"""
        dictionary = self.get_terminology_dictionary()
        return dictionary.get(core_term, core_term)

    def translate_multiple(self, terms: List[str]) -> List[str]:
        """Translate multiple terms at once"""
        return [self.translate_term(term) for term in terms]

    def translate_object(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively translate string values in an object"""
        if isinstance(obj, dict):
            return {key: self.translate_object(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.translate_object(item) for item in obj]
        elif isinstance(obj, str):
            return self.translate_term(obj)
        else:
            return obj

    # Feature Management
    @abstractmethod
    def get_enabled_features(self) -> List[str]:
        """Get list of features enabled for this module"""
        pass

    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a specific feature is enabled"""
        return self.feature_toggles.get(feature_name, False)

    def get_feature_config(self, feature_name: str) -> Dict[str, Any]:
        """Get configuration for a specific feature"""
        if not self.is_feature_enabled(feature_name):
            return {}
        return self.settings.get(f"{feature_name}_config", {})

    # Workflow Configuration
    @abstractmethod
    def get_active_workflows(self) -> List[Dict[str, Any]]:
        """Get workflows that should be activated for this module"""
        pass

    def get_workflow_config(self, workflow_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific workflow"""
        workflows = self.get_active_workflows()
        for workflow in workflows:
            if workflow.get("name") == workflow_name:
                return workflow
        return None

    # User Role Configuration
    @abstractmethod
    def get_role_hierarchy(self) -> Dict[str, Dict[str, Any]]:
        """Get role definitions and hierarchy for this industry"""
        pass

    def get_role_permissions(self, role: str) -> List[str]:
        """Get permissions for a specific role"""
        hierarchy = self.get_role_hierarchy()
        role_config = hierarchy.get(role, {})
        return role_config.get("permissions", [])

    def get_role_display_name(self, role: str) -> str:
        """Get display name for a role"""
        hierarchy = self.get_role_hierarchy()
        role_config = hierarchy.get(role, {})
        return role_config.get("display_name", role.replace("_", " ").title())

    # UI/UX Configuration
    @abstractmethod
    def get_navigation_structure(self) -> List[Dict[str, Any]]:
        """Get navigation menu structure for this module"""
        pass

    @abstractmethod
    def get_dashboard_layout(self) -> Dict[str, Any]:
        """Get dashboard layout configuration"""
        pass

    def get_color_scheme(self) -> Dict[str, str]:
        """Get color scheme for this module"""
        return {
            "primary": self.branding.get("primary_color", "#3B82F6"),
            "secondary": self.branding.get("secondary_color", "#1E40AF"),
            "accent": self.branding.get("accent_color", "#EF4444"),
            "background": self.branding.get("background_color", "#F9FAFB"),
            "text": self.branding.get("text_color", "#111827"),
        }

    # Content & Templates
    @abstractmethod
    def get_default_page_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get default page templates for this industry"""
        pass

    @abstractmethod
    def get_form_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get form templates for this industry"""
        pass

    def get_email_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get email templates for this industry"""
        return {}

    # Booking & Resource Configuration
    def get_resource_types(self) -> List[Dict[str, Any]]:
        """Get resource types supported by this module"""
        return []

    def get_booking_rules(self) -> Dict[str, Any]:
        """Get booking rules and constraints"""
        return {
            "advance_booking_days": 30,
            "min_booking_duration": 30,  # minutes
            "max_booking_duration": 480,  # minutes
            "allow_recurring": True,
            "require_approval": False,
        }

    # Integration Hooks
    def get_webhook_endpoints(self) -> Dict[str, str]:
        """Get webhook endpoints for this module"""
        return {}

    def get_api_extensions(self) -> List[str]:
        """Get additional API routes for this module"""
        return []

    # Validation & Business Logic
    def validate_user_data(self, user_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate user data according to module rules"""
        errors = []
        # Basic validation - modules can override for specific rules
        required_fields = ["email", "first_name", "last_name"]
        for field in required_fields:
            if not user_data.get(field):
                errors.append(f"Field '{field}' is required")

        return len(errors) == 0, errors

    def validate_booking_data(
        self, booking_data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Validate booking data according to module rules"""
        errors = []
        # Basic validation - modules can override for specific rules
        required_fields = ["resource_id", "start_time", "end_time"]
        for field in required_fields:
            if not booking_data.get(field):
                errors.append(f"Field '{field}' is required")

        return len(errors) == 0, errors

    # Reporting & Analytics
    def get_dashboard_metrics(self) -> List[Dict[str, Any]]:
        """Get metrics to display on dashboard"""
        return [
            {
                "name": "total_users",
                "display_name": self.translate_term("Total Users"),
                "type": "count",
                "importance": "high",
            },
            {
                "name": "active_bookings",
                "display_name": self.translate_term("Active Bookings"),
                "type": "count",
                "importance": "high",
            },
        ]

    def get_report_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get report templates for this module"""
        return {}

    # Module Health & Status
    def get_module_status(self) -> Dict[str, Any]:
        """Get current status of this module"""
        return {
            "module_name": self.get_module_name(),
            "version": self.get_module_version(),
            "industry": self.get_industry_type(),
            "tenant_id": self.tenant_id,
            "enabled_features": self.get_enabled_features(),
            "active_workflows": len(self.get_active_workflows()),
            "last_updated": datetime.utcnow().isoformat(),
        }

    # Configuration Export/Import
    def export_configuration(self) -> Dict[str, Any]:
        """Export module configuration for backup/migration"""
        return {
            "module_name": self.get_module_name(),
            "version": self.get_module_version(),
            "tenant_data": self.tenant_data,
            "terminology": self.get_terminology_dictionary(),
            "features": self.get_enabled_features(),
            "workflows": self.get_active_workflows(),
            "navigation": self.get_navigation_structure(),
            "dashboard": self.get_dashboard_layout(),
            "exported_at": datetime.utcnow().isoformat(),
        }
