"""
Government Module - Industry-specific experience for government facilities
Transforms the universal platform into a public facility management solution
"""

from typing import Any, Dict, List

from modules.base_module import BaseModule


class GovernmentModule(BaseModule):
    """Government industry module - public facility management"""

    def get_module_name(self) -> str:
        return "Public Facility Management System"

    def get_module_version(self) -> str:
        return "1.0.0"

    def get_terminology_dictionary(self) -> Dict[str, str]:
        """Government-specific terminology"""
        return {
            # Core platform terms -> Government terms
            "users": "citizens",
            "user": "citizen",
            "customers": "residents",
            "customer": "resident",
            "clients": "community members",
            "client": "community member",
            "members": "residents",
            "member": "resident",
            "bookings": "reservations",
            "booking": "reservation",
            "resources": "public facilities",
            "resource": "public facility",
            "spaces": "public spaces",
            "space": "public space",
            "tours": "facility tours",
            "tour": "facility tour",
            "leads": "inquiries",
            "lead": "inquiry",
            "staff": "facility coordinators",
            "administrator": "facility manager",
            "front_desk": "public services clerk",
            "revenue": "facility fees",
            "payments": "service fees",
            "subscription": "permit",
            "subscriptions": "permits",
            "invoices": "fee notices",
            "invoice": "fee notice",
        }

    def get_enabled_features(self) -> List[str]:
        """Features enabled for government facilities"""
        return [
            "website_builder",
            "lead_management",
            "approval_workflows",
            "public_transparency",
            "accessibility_features",
            "booking_system",
            "permit_management",
            "public_calendar",
            "meeting_minutes",
            "document_library",
            "citizen_portal",
            "foia_requests",
            "complaint_tracking",
            "multi_language",
            "ada_compliance",
            "security_screening",
            "background_checks",
            "insurance_requirements",
            "public_notices",
        ]

    def get_active_workflows(self) -> List[Dict[str, Any]]:
        """Government-specific automation workflows"""
        return [
            {
                "name": "reservation_approval",
                "trigger_event": "booking_created",
                "actions": [
                    {
                        "type": "update_status",
                        "entity_type": "booking",
                        "status": "pending_approval",
                    },
                    {
                        "type": "send_message",
                        "template_id": "reservation_submitted",
                        "recipient": "requester",
                    },
                    {
                        "type": "send_message",
                        "template_id": "approval_request",
                        "recipient": "facility_manager",
                    },
                ],
            },
            {
                "name": "approval_granted",
                "trigger_event": "booking_approved",
                "actions": [
                    {
                        "type": "send_message",
                        "template_id": "reservation_approved",
                        "recipient": "requester",
                    },
                    {
                        "type": "send_message",
                        "template_id": "setup_instructions",
                        "recipient": "requester",
                        "delay_minutes": 60,
                    },
                    {
                        "type": "webhook",
                        "url": "/api/public/calendar/update",
                        "method": "POST",
                    },
                ],
            },
            {
                "name": "public_notice",
                "trigger_event": "event_published",
                "conditions": [{"field": "public_notice_required", "value": True}],
                "actions": [
                    {
                        "type": "webhook",
                        "url": "/api/public/notices/create",
                        "method": "POST",
                    },
                    {
                        "type": "send_message",
                        "template_id": "public_meeting_notice",
                        "recipient": "all_subscribers",
                    },
                ],
            },
            {
                "name": "insurance_verification",
                "trigger_event": "lead_created",
                "conditions": [{"field": "event_type", "value": "private_event"}],
                "actions": [
                    {
                        "type": "send_message",
                        "template_id": "insurance_requirements",
                        "recipient": "requester",
                    },
                    {
                        "type": "update_status",
                        "entity_type": "lead",
                        "status": "awaiting_documentation",
                    },
                ],
            },
        ]

    def get_role_hierarchy(self) -> Dict[str, Dict[str, Any]]:
        """Government role structure"""
        return {
            "account_owner": {
                "display_name": "Facility Director",
                "description": "Overall facility management and oversight",
                "permissions": ["*"],
                "level": 5,
            },
            "administrator": {
                "display_name": "Facility Manager",
                "description": "Daily operations and staff management",
                "permissions": [
                    "residents.manage",
                    "facilities.manage",
                    "events.manage",
                    "reservations.manage",
                    "approvals.manage",
                    "reports.view",
                ],
                "level": 4,
            },
            "front_desk": {
                "display_name": "Public Services Clerk",
                "description": ("Assists citizens with reservations and inquiries"),
                "permissions": [
                    "residents.view",
                    "reservations.view",
                    "reservations.create",
                    "tours.manage",
                    "inquiries.manage",
                    "documents.view",
                ],
                "level": 3,
            },
            "security": {
                "display_name": "Security Officer",
                "description": "Facility security and access control",
                "permissions": [
                    "access.manage",
                    "security.monitor",
                    "incidents.report",
                ],
                "level": 2,
            },
            "maintenance": {
                "display_name": "Facilities Maintenance",
                "description": "Maintains public facilities and equipment",
                "permissions": [
                    "facilities.view",
                    "facilities.update",
                    "maintenance.manage",
                ],
                "level": 2,
            },
            "member": {
                "display_name": "Citizen",
                "description": "Member of the public using facilities",
                "permissions": [
                    "reservations.create",
                    "reservations.view_own",
                    "events.view",
                    "documents.view_public",
                    "complaints.submit",
                ],
                "level": 1,
            },
        }

    def get_navigation_structure(self) -> List[Dict[str, Any]]:
        """Government navigation menu"""
        return [
            {
                "name": "Facility Dashboard",
                "path": "/dashboard",
                "icon": "home",
                "roles": ["*"],
            },
            {
                "name": "Public Calendar",
                "path": "/calendar",
                "icon": "calendar",
                "roles": ["*"],
            },
            {
                "name": "Reserve Facility",
                "path": "/booking",
                "icon": "calendar-plus",
                "roles": ["member"],
            },
            {
                "name": "My Reservations",
                "path": "/my-reservations",
                "icon": "clock",
                "roles": ["member"],
            },
            {
                "name": "Public Documents",
                "path": "/documents",
                "icon": "file-text",
                "roles": ["*"],
            },
            {
                "name": "Submit Request",
                "path": "/submit-request",
                "icon": "mail",
                "roles": ["member"],
            },
            {
                "name": "Facility Management",
                "path": "/admin/facilities",
                "icon": "building",
                "roles": ["administrator", "account_owner"],
            },
            {
                "name": "Reservation Management",
                "path": "/admin/reservations",
                "icon": "calendar-check",
                "roles": ["front_desk", "administrator", "account_owner"],
            },
            {
                "name": "Approval Queue",
                "path": "/admin/approvals",
                "icon": "check-circle",
                "roles": ["administrator", "account_owner"],
            },
            {
                "name": "Citizen Inquiries",
                "path": "/leads",
                "icon": "user-plus",
                "roles": ["front_desk", "administrator", "account_owner"],
            },
            {
                "name": "Public Website",
                "path": "/cms/pages",
                "icon": "globe",
                "roles": ["administrator", "account_owner"],
            },
            {
                "name": "Usage Reports",
                "path": "/analytics",
                "icon": "bar-chart",
                "roles": ["administrator", "account_owner"],
            },
        ]

    def get_dashboard_layout(self) -> Dict[str, Any]:
        """Government dashboard configuration"""
        return {
            "widgets": [
                {
                    "type": "facility_status",
                    "title": "Facility Status",
                    "position": {"row": 1, "col": 1, "span": 2},
                    "metrics": [
                        "facilities_available",
                        "maintenance_scheduled",
                        "accessibility_status",
                    ],
                },
                {
                    "type": "reservation_overview",
                    "title": "Today's Reservations",
                    "position": {"row": 1, "col": 3, "span": 2},
                    "metrics": [
                        "today_reservations",
                        "pending_approvals",
                        "utilization_rate",
                    ],
                },
                {
                    "type": "citizen_engagement",
                    "title": "Citizen Engagement",
                    "position": {"row": 2, "col": 1, "span": 2},
                    "metrics": [
                        "monthly_reservations",
                        "new_citizens",
                        "satisfaction_rating",
                    ],
                },
                {
                    "type": "compliance_status",
                    "title": "Compliance & Safety",
                    "position": {"row": 2, "col": 3, "span": 1},
                    "metrics": [
                        "safety_inspections",
                        "ada_compliance",
                        "security_incidents",
                    ],
                },
                {
                    "type": "public_calendar",
                    "title": "Public Events Calendar",
                    "position": {"row": 3, "col": 1, "span": 3},
                },
                {
                    "type": "pending_approvals",
                    "title": "Pending Approvals",
                    "position": {"row": 2, "col": 4, "span": 1},
                    "roles": ["administrator", "account_owner"],
                },
            ],
            "quick_actions": [
                {
                    "name": "Approve Reservation",
                    "action": "approve_reservation",
                    "icon": "check",
                },
                {
                    "name": "Schedule Maintenance",
                    "action": "schedule_maintenance",
                    "icon": "tool",
                },
                {
                    "name": "Post Public Notice",
                    "action": "public_notice",
                    "icon": "megaphone",
                },
                {
                    "name": "Generate Report",
                    "action": "generate_report",
                    "icon": "file-text",
                },
            ],
        }

    def get_default_page_templates(self) -> Dict[str, Dict[str, Any]]:
        """Government page templates"""
        return {
            "homepage": {
                "name": "Government Facility Homepage",
                "blocks": [
                    {
                        "type": "hero_banner",
                        "config": {
                            "title": "Public Facility Reservations",
                            "subtitle": (
                                "Reserve community spaces for meetings, "
                                "events, and public gatherings"
                            ),
                            "cta_text": "View Available Facilities",
                            "cta_action": "view_facilities",
                        },
                    },
                    {
                        "type": "facility_grid",
                        "config": {
                            "title": "Our Public Facilities",
                            "show_availability": True,
                            "show_capacity": True,
                        },
                    },
                    {
                        "type": "public_notices",
                        "config": {
                            "title": "Public Notices & Announcements",
                            "show_date": True,
                            "auto_archive": True,
                        },
                    },
                    {
                        "type": "contact_info",
                        "config": {
                            "title": "Contact Information",
                            "show_office_hours": True,
                            "show_ada_info": True,
                        },
                    },
                ],
            },
            "facilities": {
                "name": "Facility Directory",
                "blocks": [
                    {
                        "type": "facility_search",
                        "config": {
                            "allow_filtering": True,
                            "show_capacity": True,
                            "show_amenities": True,
                        },
                    },
                    {
                        "type": "reservation_calendar",
                        "config": {
                            "public_view": True,
                            "show_availability": True,
                        },
                    },
                ],
            },
        }

    def get_form_templates(self) -> Dict[str, Dict[str, Any]]:
        """Government form templates"""
        return {
            "facility_request": {
                "name": "Facility Reservation Request",
                "fields": [
                    {
                        "label": "Organization Name",
                        "type": "text",
                        "required": True,
                    },
                    {
                        "label": "Contact Person",
                        "type": "text",
                        "required": True,
                    },
                    {
                        "label": "Email Address",
                        "type": "email",
                        "required": True,
                    },
                    {
                        "label": "Phone Number",
                        "type": "phone",
                        "required": True,
                    },
                    {
                        "label": "Event Type",
                        "type": "select",
                        "required": True,
                        "options": [
                            "Community Meeting",
                            "Non-profit Event",
                            "Educational Workshop",
                            "Public Hearing",
                            "Government Meeting",
                            "Other",
                        ],
                    },
                    {
                        "label": "Requested Facility",
                        "type": "select",
                        "required": True,
                        "options": [
                            "Council Chambers",
                            "Community Room",
                            "Conference Room",
                            "Auditorium",
                            "Recreation Center",
                        ],
                    },
                    {"label": "Event Date", "type": "date", "required": True},
                    {"label": "Start Time", "type": "time", "required": True},
                    {"label": "End Time", "type": "time", "required": True},
                    {
                        "label": "Expected Attendance",
                        "type": "number",
                        "required": True,
                    },
                    {
                        "label": "Setup Requirements",
                        "type": "textarea",
                        "required": False,
                    },
                    {
                        "label": "Insurance Provider",
                        "type": "text",
                        "required": False,
                    },
                    {
                        "label": "Event Description",
                        "type": "textarea",
                        "required": True,
                    },
                ],
            },
            "public_inquiry": {
                "name": "General Public Inquiry",
                "fields": [
                    {"label": "Name", "type": "text", "required": True},
                    {"label": "Email", "type": "email", "required": True},
                    {"label": "Phone", "type": "phone", "required": False},
                    {
                        "label": "Subject",
                        "type": "select",
                        "required": True,
                        "options": [
                            "Facility Information",
                            "Reservation Question",
                            "Complaint",
                            "Suggestion",
                            "ADA Accommodation",
                            "Other",
                        ],
                    },
                    {"label": "Message", "type": "textarea", "required": True},
                    {
                        "label": "Preferred Response Method",
                        "type": "select",
                        "required": True,
                        "options": ["Email", "Phone", "Mail"],
                    },
                ],
            },
            "maintenance_request": {
                "name": "Facility Maintenance Request",
                "fields": [
                    {
                        "label": "Reporter Name",
                        "type": "text",
                        "required": True,
                    },
                    {"label": "Email", "type": "email", "required": True},
                    {
                        "label": "Facility/Location",
                        "type": "select",
                        "required": True,
                        "options": [
                            "Council Chambers",
                            "Community Room",
                            "Lobby",
                            "Parking Lot",
                            "Restrooms",
                            "Other",
                        ],
                    },
                    {
                        "label": "Issue Type",
                        "type": "select",
                        "required": True,
                        "options": [
                            "Electrical",
                            "Plumbing",
                            "HVAC",
                            "Structural",
                            "Accessibility",
                            "Cleanliness",
                            "Other",
                        ],
                    },
                    {
                        "label": "Priority Level",
                        "type": "select",
                        "required": True,
                        "options": ["Low", "Medium", "High", "Emergency"],
                    },
                    {
                        "label": "Description",
                        "type": "textarea",
                        "required": True,
                    },
                    {
                        "label": "Safety Concern",
                        "type": "checkbox",
                        "required": False,
                    },
                ],
            },
        }

    def get_resource_types(self) -> List[Dict[str, Any]]:
        """Government facility types"""
        return [
            {
                "type": "council_chambers",
                "display_name": "Council Chambers",
                "description": "Main meeting room for city council",
                "pricing_type": "none",
                "bookable": True,
                "requires_approval": True,
                "advance_booking_days": 30,
            },
            {
                "type": "community_room",
                "display_name": "Community Meeting Room",
                "description": "Multi-purpose room for community events",
                "pricing_type": "none",
                "bookable": True,
                "requires_approval": True,
                "advance_booking_days": 60,
            },
            {
                "type": "conference_room",
                "display_name": "Conference Room",
                "description": "Smaller meeting space for committees",
                "pricing_type": "none",
                "bookable": True,
                "requires_approval": True,
                "advance_booking_days": 14,
            },
            {
                "type": "auditorium",
                "display_name": "Public Auditorium",
                "description": "Large venue for public hearings and events",
                "pricing_type": "fee_based",
                "bookable": True,
                "requires_approval": True,
                "advance_booking_days": 90,
            },
            {
                "type": "recreation_center",
                "display_name": "Recreation Center",
                "description": "Community recreation and sports facility",
                "pricing_type": "fee_based",
                "bookable": True,
                "requires_approval": True,
                "advance_booking_days": 30,
            },
        ]

    def get_booking_rules(self) -> Dict[str, Any]:
        """Government booking rules"""
        return {
            "advance_booking_days": 60,
            "min_booking_duration": 60,  # 1 hour
            "max_booking_duration": 480,  # 8 hours
            "allow_recurring": True,
            "require_approval": True,
            "approval_workflow": {
                "auto_approve": False,
                "approval_required_roles": ["administrator", "account_owner"],
                "approval_time_limit_hours": 72,
            },
            "insurance_requirements": {
                "private_events": True,
                "minimum_coverage": 1000000,
                "additional_insured_required": True,
            },
            "cancellation_policy": {
                "free_cancellation_hours": 48,
                "penalty_fee": 0,
            },
            "public_notice_requirements": {
                "government_meetings": True,
                "notice_days": 3,
                "posting_locations": [
                    "website",
                    "bulletin_board",
                    "local_paper",
                ],
            },
        }

    def get_dashboard_metrics(self) -> List[Dict[str, Any]]:
        """Government dashboard metrics"""
        return [
            {
                "name": "citizen_reservations",
                "display_name": "Citizen Reservations",
                "type": "count",
                "importance": "high",
                "description": "Total reservations by citizens this month",
            },
            {
                "name": "facility_utilization",
                "display_name": "Facility Utilization",
                "type": "percentage",
                "importance": "high",
                "description": "Percentage of time facilities are in use",
            },
            {
                "name": "approval_time",
                "display_name": "Average Approval Time",
                "type": "duration",
                "importance": "high",
                "description": "Average time to approve reservations",
            },
            {
                "name": "citizen_satisfaction",
                "display_name": "Citizen Satisfaction",
                "type": "rating",
                "importance": "high",
                "description": "Average satisfaction rating from citizens",
            },
            {
                "name": "maintenance_requests",
                "display_name": "Maintenance Requests",
                "type": "count",
                "importance": "medium",
                "description": "Open maintenance requests",
            },
            {
                "name": "ada_compliance",
                "display_name": "ADA Compliance",
                "type": "percentage",
                "importance": "high",
                "description": "Percentage of facilities ADA compliant",
            },
            {
                "name": "public_engagement",
                "display_name": "Public Engagement",
                "type": "score",
                "importance": "medium",
                "description": "Overall citizen engagement score",
            },
        ]
