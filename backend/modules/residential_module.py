"""
Residential Module - Industry-specific experience for residential lofts and home offices
Transforms the universal platform into a residential space management solution
"""

from typing import Any, Dict, List

from .base_module import BaseModule


class ResidentialModule(BaseModule):
    """Residential industry module - home office and residential space management"""

    def get_module_name(self) -> str:
        return "Residential Space Management Hub"

    def get_module_version(self) -> str:
        return "1.0.0"

    def get_terminology_dictionary(self) -> Dict[str, str]:
        """Residential-specific terminology"""
        return {
            # Core platform terms -> Residential terms
            "users": "residents",
            "user": "resident",
            "customers": "tenants",
            "customer": "tenant",
            "clients": "residents",
            "client": "resident",
            "members": "community residents",
            "member": "community resident",
            "bookings": "reservations",
            "booking": "reservation",
            "resources": "amenities",
            "resource": "amenity",
            "spaces": "common areas",
            "space": "common area",
            "tours": "property tours",
            "tour": "property tour",
            "leads": "prospective residents",
            "lead": "prospective resident",
            "staff": "property coordinators",
            "administrator": "property manager",
            "front_desk": "concierge",
            "revenue": "amenity fees",
            "payments": "resident fees",
            "subscription": "resident access",
            "subscriptions": "resident access",
            "invoices": "resident bills",
            "invoice": "resident bill",
        }

    def get_enabled_features(self) -> List[str]:
        """Features enabled for residential properties"""
        return [
            "website_builder",
            "lead_management",
            "booking_system",
            "resident_portal",
            "amenity_management",
            "maintenance_requests",
            "package_management",
            "community_events",
            "noise_complaints",
            "visitor_management",
            "home_office_spaces",
            "meeting_rooms",
            "fitness_center",
            "rooftop_access",
            "resident_directory",
            "community_board",
            "resident_services",
            "parking_management",
            "utility_monitoring",
        ]

    def get_active_workflows(self) -> List[Dict[str, Any]]:
        """Residential-specific automation workflows"""
        return [
            {
                "name": "resident_welcome",
                "trigger_event": "user_created",
                "actions": [
                    {
                        "type": "send_message",
                        "template_id": "resident_welcome_package",
                        "delay_minutes": 0,
                    },
                    {
                        "type": "send_message",
                        "template_id": "amenity_guide",
                        "delay_minutes": 60,
                    },
                    {
                        "type": "send_message",
                        "template_id": "community_guidelines",
                        "delay_minutes": 1440,
                    },
                ],
            },
            {
                "name": "maintenance_workflow",
                "trigger_event": "maintenance_request",
                "actions": [
                    {
                        "type": "send_message",
                        "template_id": "maintenance_confirmation",
                        "recipient": "resident",
                    },
                    {
                        "type": "send_message",
                        "template_id": "work_order_created",
                        "recipient": "maintenance_team",
                    },
                ],
            },
            {
                "name": "amenity_reminder",
                "trigger_event": "booking_created",
                "conditions": [{"field": "hours_until", "operator": "<=", "value": 2}],
                "actions": [
                    {
                        "type": "send_message",
                        "template_id": "amenity_reminder",
                        "recipient": "resident",
                    }
                ],
            },
            {
                "name": "community_engagement",
                "trigger_event": "event_published",
                "actions": [
                    {
                        "type": "send_message",
                        "template_id": "community_event_notice",
                        "recipient": "all_residents",
                    }
                ],
            },
        ]

    def get_role_hierarchy(self) -> Dict[str, Dict[str, Any]]:
        """Residential role structure"""
        return {
            "account_owner": {
                "display_name": "Property Owner",
                "description": "Owns the residential property",
                "permissions": ["*"],
                "level": 5,
            },
            "administrator": {
                "display_name": "Property Manager",
                "description": "Manages residential property operations",
                "permissions": [
                    "residents.manage",
                    "amenities.manage",
                    "events.manage",
                    "reservations.manage",
                    "maintenance.coordinate",
                    "reports.view",
                ],
                "level": 4,
            },
            "front_desk": {
                "display_name": "Concierge",
                "description": "Provides resident services and assistance",
                "permissions": [
                    "residents.assist",
                    "reservations.view",
                    "reservations.create",
                    "visitor.manage",
                    "packages.coordinate",
                    "services.provide",
                ],
                "level": 3,
            },
            "maintenance": {
                "display_name": "Maintenance Coordinator",
                "description": "Handles property maintenance and repairs",
                "permissions": [
                    "maintenance.manage",
                    "work_orders.process",
                    "amenities.maintain",
                ],
                "level": 2,
            },
            "security": {
                "display_name": "Security Personnel",
                "description": "Provides security and access control",
                "permissions": ["security.monitor", "visitor.screen", "access.control"],
                "level": 2,
            },
            "member": {
                "display_name": "Resident",
                "description": "Lives in the residential property",
                "permissions": [
                    "reservations.create",
                    "reservations.view_own",
                    "amenities.use",
                    "maintenance.request",
                    "events.view",
                    "community.participate",
                ],
                "level": 1,
            },
        }

    def get_navigation_structure(self) -> List[Dict[str, Any]]:
        """Residential navigation menu"""
        return [
            {
                "name": "Resident Dashboard",
                "path": "/dashboard",
                "icon": "home",
                "roles": ["*"],
            },
            {
                "name": "My Reservations",
                "path": "/reservations",
                "icon": "calendar",
                "roles": ["member"],
            },
            {
                "name": "Book Amenity",
                "path": "/booking",
                "icon": "calendar-plus",
                "roles": ["member"],
            },
            {
                "name": "Maintenance Requests",
                "path": "/maintenance",
                "icon": "tool",
                "roles": ["member"],
            },
            {
                "name": "Community Events",
                "path": "/events",
                "icon": "users",
                "roles": ["*"],
            },
            {
                "name": "Resident Directory",
                "path": "/directory",
                "icon": "user-group",
                "roles": ["member"],
            },
            {
                "name": "Community Board",
                "path": "/community",
                "icon": "message-square",
                "roles": ["member"],
            },
            {
                "name": "Building Services",
                "path": "/services",
                "icon": "bell",
                "roles": ["member"],
            },
            {
                "name": "Property Management",
                "path": "/admin/property",
                "icon": "building",
                "roles": ["administrator", "account_owner"],
            },
            {
                "name": "Resident Management",
                "path": "/admin/residents",
                "icon": "users",
                "roles": ["front_desk", "administrator", "account_owner"],
            },
            {
                "name": "Prospective Residents",
                "path": "/leads",
                "icon": "user-plus",
                "roles": ["front_desk", "administrator", "account_owner"],
            },
            {
                "name": "Property Website",
                "path": "/cms/pages",
                "icon": "globe",
                "roles": ["administrator", "account_owner"],
            },
            {
                "name": "Property Analytics",
                "path": "/analytics",
                "icon": "bar-chart",
                "roles": ["administrator", "account_owner"],
            },
        ]

    def get_dashboard_layout(self) -> Dict[str, Any]:
        """Residential dashboard configuration"""
        return {
            "widgets": [
                {
                    "type": "resident_satisfaction",
                    "title": "Resident Satisfaction",
                    "position": {"row": 1, "col": 1, "span": 2},
                    "metrics": ["satisfaction_score", "retention_rate", "referrals"],
                },
                {
                    "type": "amenity_usage",
                    "title": "Amenity Usage",
                    "position": {"row": 1, "col": 3, "span": 2},
                    "metrics": ["popular_amenities", "peak_times", "utilization_rate"],
                },
                {
                    "type": "maintenance_overview",
                    "title": "Maintenance Status",
                    "position": {"row": 2, "col": 1, "span": 2},
                    "metrics": ["open_requests", "response_time", "completion_rate"],
                },
                {
                    "type": "community_engagement",
                    "title": "Community Activity",
                    "position": {"row": 2, "col": 3, "span": 2},
                    "metrics": [
                        "event_attendance",
                        "community_posts",
                        "resident_participation",
                    ],
                },
                {
                    "type": "building_operations",
                    "title": "Building Operations",
                    "position": {"row": 3, "col": 1, "span": 3},
                    "roles": ["administrator", "account_owner"],
                },
            ],
            "quick_actions": [
                {
                    "name": "Book Home Office",
                    "action": "book_office",
                    "icon": "briefcase",
                },
                {
                    "name": "Report Maintenance",
                    "action": "maintenance_request",
                    "icon": "tool",
                },
                {
                    "name": "Plan Community Event",
                    "action": "create_event",
                    "icon": "users",
                },
                {
                    "name": "Resident Survey",
                    "action": "satisfaction_survey",
                    "icon": "star",
                },
            ],
        }

    def get_default_page_templates(self) -> Dict[str, Dict[str, Any]]:
        """Residential page templates"""
        return {
            "homepage": {
                "name": "Residential Property Homepage",
                "blocks": [
                    {
                        "type": "hero_banner",
                        "config": {
                            "title": "Your Home, Enhanced by Community",
                            "subtitle": "Modern living with premium amenities and a vibrant resident community",
                            "cta_text": "Schedule Property Tour",
                            "cta_action": "schedule_tour",
                        },
                    },
                    {
                        "type": "amenity_showcase",
                        "config": {
                            "title": "Premium Amenities",
                            "show_availability": True,
                            "focus": "lifestyle",
                        },
                    },
                    {
                        "type": "community_highlights",
                        "config": {
                            "title": "Resident Community",
                            "show_events": True,
                            "show_testimonials": True,
                        },
                    },
                    {
                        "type": "floor_plans",
                        "config": {"title": "Available Units", "show_pricing": True},
                    },
                ],
            }
        }

    def get_form_templates(self) -> Dict[str, Dict[str, Any]]:
        """Residential form templates"""
        return {
            "lease_inquiry": {
                "name": "Apartment Inquiry",
                "fields": [
                    {"label": "Name", "type": "text", "required": True},
                    {"label": "Email", "type": "email", "required": True},
                    {"label": "Phone", "type": "phone", "required": True},
                    {"label": "Desired Move-in Date", "type": "date", "required": True},
                    {
                        "label": "Unit Type",
                        "type": "select",
                        "required": True,
                        "options": [
                            "Studio",
                            "1 Bedroom",
                            "2 Bedroom",
                            "3 Bedroom",
                            "Penthouse",
                        ],
                    },
                    {
                        "label": "Budget Range",
                        "type": "select",
                        "required": False,
                        "options": [
                            "Under $2,000",
                            "$2,000-$3,000",
                            "$3,000-$4,000",
                            "$4,000-$5,000",
                            "$5,000+",
                        ],
                    },
                    {
                        "label": "Employment Status",
                        "type": "select",
                        "required": True,
                        "options": ["Employed", "Self-employed", "Student", "Retired"],
                    },
                    {
                        "label": "Additional Information",
                        "type": "textarea",
                        "required": False,
                    },
                ],
            },
            "maintenance_request": {
                "name": "Maintenance Request Form",
                "fields": [
                    {"label": "Unit Number", "type": "text", "required": True},
                    {
                        "label": "Issue Category",
                        "type": "select",
                        "required": True,
                        "options": [
                            "Plumbing",
                            "Electrical",
                            "HVAC",
                            "Appliances",
                            "General Repair",
                            "Emergency",
                        ],
                    },
                    {
                        "label": "Priority Level",
                        "type": "select",
                        "required": True,
                        "options": ["Low", "Medium", "High", "Emergency"],
                    },
                    {
                        "label": "Issue Description",
                        "type": "textarea",
                        "required": True,
                    },
                    {
                        "label": "Best Time to Access",
                        "type": "select",
                        "required": False,
                        "options": [
                            "Weekday Morning",
                            "Weekday Afternoon",
                            "Weekend",
                            "Anytime",
                        ],
                    },
                ],
            },
        }

    def get_resource_types(self) -> List[Dict[str, Any]]:
        """Residential amenity types"""
        return [
            {
                "type": "home_office",
                "display_name": "Home Office Space",
                "description": "Private office for remote work",
                "pricing_type": "hourly",
                "bookable": True,
                "requires_approval": False,
                "advance_booking_days": 7,
            },
            {
                "type": "meeting_room",
                "display_name": "Meeting Room",
                "description": "Small meeting space for professional use",
                "pricing_type": "hourly",
                "bookable": True,
                "requires_approval": False,
                "advance_booking_days": 14,
            },
            {
                "type": "fitness_center",
                "display_name": "Fitness Center",
                "description": "Fully equipped fitness facility",
                "pricing_type": "free",
                "bookable": True,
                "requires_approval": False,
                "advance_booking_days": 3,
            },
            {
                "type": "rooftop_terrace",
                "display_name": "Rooftop Terrace",
                "description": "Outdoor space with city views",
                "pricing_type": "free",
                "bookable": True,
                "requires_approval": True,
                "advance_booking_days": 30,
            },
            {
                "type": "party_room",
                "display_name": "Community Room",
                "description": "Event space for resident gatherings",
                "pricing_type": "fee_based",
                "bookable": True,
                "requires_approval": True,
                "advance_booking_days": 14,
            },
        ]

    def get_dashboard_metrics(self) -> List[Dict[str, Any]]:
        """Residential dashboard metrics"""
        return [
            {
                "name": "active_residents",
                "display_name": "Active Residents",
                "type": "count",
                "importance": "high",
            },
            {
                "name": "amenity_utilization",
                "display_name": "Amenity Usage",
                "type": "percentage",
                "importance": "high",
            },
            {
                "name": "maintenance_requests",
                "display_name": "Maintenance Requests",
                "type": "count",
                "importance": "high",
            },
            {
                "name": "resident_satisfaction",
                "display_name": "Resident Satisfaction",
                "type": "rating",
                "importance": "high",
            },
            {
                "name": "community_events",
                "display_name": "Community Events",
                "type": "count",
                "importance": "medium",
            },
            {
                "name": "occupancy_rate",
                "display_name": "Occupancy Rate",
                "type": "percentage",
                "importance": "medium",
            },
        ]
