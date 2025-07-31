"""
University Module - Industry-specific experience for university campus facilities
Transforms the universal platform into an academic facility management solution
"""

from typing import Any, Dict, List

from .base_module import BaseModule


class UniversityModule(BaseModule):
    """University industry module - academic campus facility management"""

    def get_module_name(self) -> str:
        return "Campus Resource Management System"

    def get_module_version(self) -> str:
        return "1.0.0"

    def get_terminology_dictionary(self) -> Dict[str, str]:
        """University-specific terminology"""
        return {
            # Core platform terms -> University terms
            "users": "students",
            "user": "student",
            "customers": "students",
            "customer": "student",
            "clients": "faculty and students",
            "client": "faculty member",
            "members": "campus community",
            "member": "community member",
            "bookings": "reservations",
            "booking": "reservation",
            "resources": "campus facilities",
            "resource": "campus facility",
            "spaces": "study spaces",
            "space": "study space",
            "tours": "campus tours",
            "tour": "campus tour",
            "leads": "prospective students",
            "lead": "prospective student",
            "staff": "faculty coordinators",
            "administrator": "facility coordinator",
            "front_desk": "campus services",
            "revenue": "facility fees",
            "payments": "student fees",
            "subscription": "semester access",
            "subscriptions": "semester access",
            "invoices": "billing statements",
            "invoice": "billing statement",
        }

    def get_enabled_features(self) -> List[str]:
        """Features enabled for university campuses"""
        return [
            "website_builder",
            "lead_management",
            "academic_calendar",
            "student_portal",
            "booking_system",
            "study_rooms",
            "lecture_halls",
            "lab_reservations",
            "sso_integration",
            "academic_workflows",
            "semester_management",
            "course_integration",
            "thesis_defenses",
            "research_spaces",
            "library_integration",
            "academic_events",
            "student_organizations",
            "campus_announcements",
            "accessibility_services",
        ]

    def get_active_workflows(self) -> List[Dict[str, Any]]:
        """University-specific automation workflows"""
        return [
            {
                "name": "student_orientation",
                "trigger_event": "user_created",
                "conditions": [{"field": "role", "value": "student"}],
                "actions": [
                    {
                        "type": "send_message",
                        "template_id": "campus_welcome",
                        "delay_minutes": 0,
                    },
                    {
                        "type": "send_message",
                        "template_id": "campus_resources_guide",
                        "delay_minutes": 60,
                    },
                ],
            },
            {
                "name": "semester_reminder",
                "trigger_event": "semester_start",
                "actions": [
                    {
                        "type": "send_message",
                        "template_id": "semester_resources",
                        "recipient": "all_students",
                    }
                ],
            },
            {
                "name": "thesis_defense_coordination",
                "trigger_event": "booking_created",
                "conditions": [
                    {"field": "resource_type", "value": "thesis_defense_room"}
                ],
                "actions": [
                    {
                        "type": "send_message",
                        "template_id": "thesis_coordinator_notification",
                        "recipient": "thesis_coordinator",
                    },
                    {
                        "type": "send_message",
                        "template_id": "av_setup_request",
                        "recipient": "av_support",
                    },
                ],
            },
        ]

    def get_role_hierarchy(self) -> Dict[str, Dict[str, Any]]:
        """University role structure"""
        return {
            "account_owner": {
                "display_name": "Campus Administrator",
                "description": "Overall campus facility management",
                "permissions": ["*"],
                "level": 5,
            },
            "administrator": {
                "display_name": "Facility Coordinator",
                "description": "Manages campus facilities and reservations",
                "permissions": [
                    "students.manage",
                    "facilities.manage",
                    "events.manage",
                    "reservations.manage",
                    "reports.view",
                    "academic_calendar.manage",
                ],
                "level": 4,
            },
            "front_desk": {
                "display_name": "Campus Services",
                "description": "Assists students with reservations and campus services",
                "permissions": [
                    "students.view",
                    "reservations.view",
                    "reservations.create",
                    "tours.manage",
                    "campus_info.provide",
                ],
                "level": 3,
            },
            "faculty": {
                "display_name": "Faculty Member",
                "description": "Teaching staff with enhanced booking privileges",
                "permissions": [
                    "reservations.create",
                    "lecture_halls.book",
                    "lab_spaces.book",
                    "student_groups.manage",
                    "course_events.create",
                ],
                "level": 2,
            },
            "student": {
                "display_name": "Student",
                "description": "Enrolled student with campus facility access",
                "permissions": [
                    "reservations.create",
                    "reservations.view_own",
                    "study_rooms.book",
                    "events.view",
                    "campus_events.register",
                ],
                "level": 1,
            },
            "graduate_student": {
                "display_name": "Graduate Student",
                "description": "Graduate student with extended privileges",
                "permissions": [
                    "reservations.create",
                    "study_rooms.book",
                    "research_spaces.book",
                    "thesis_defense.schedule",
                    "lab_access.extended",
                ],
                "level": 1,
            },
        }

    def get_navigation_structure(self) -> List[Dict[str, Any]]:
        """University navigation menu"""
        return [
            {
                "name": "Campus Dashboard",
                "path": "/dashboard",
                "icon": "home",
                "roles": ["*"],
            },
            {
                "name": "My Reservations",
                "path": "/reservations",
                "icon": "calendar",
                "roles": ["student", "graduate_student", "faculty"],
            },
            {
                "name": "Book Study Space",
                "path": "/booking",
                "icon": "calendar-plus",
                "roles": ["student", "graduate_student", "faculty"],
            },
            {
                "name": "Academic Calendar",
                "path": "/calendar",
                "icon": "calendar-check",
                "roles": ["*"],
            },
            {
                "name": "Campus Events",
                "path": "/events",
                "icon": "users",
                "roles": ["*"],
            },
            {
                "name": "Research Resources",
                "path": "/research",
                "icon": "briefcase",
                "roles": ["graduate_student", "faculty"],
            },
            {
                "name": "Campus Directory",
                "path": "/directory",
                "icon": "user-group",
                "roles": ["*"],
            },
            {
                "name": "Facility Management",
                "path": "/admin/facilities",
                "icon": "building",
                "roles": ["administrator", "account_owner"],
            },
            {
                "name": "Student Services",
                "path": "/admin/students",
                "icon": "users",
                "roles": ["front_desk", "administrator", "account_owner"],
            },
            {
                "name": "Prospective Students",
                "path": "/leads",
                "icon": "user-plus",
                "roles": ["front_desk", "administrator", "account_owner"],
            },
            {
                "name": "Campus Website",
                "path": "/cms/pages",
                "icon": "globe",
                "roles": ["administrator", "account_owner"],
            },
            {
                "name": "Usage Analytics",
                "path": "/analytics",
                "icon": "bar-chart",
                "roles": ["administrator", "account_owner"],
            },
        ]

    def get_dashboard_layout(self) -> Dict[str, Any]:
        """University dashboard configuration"""
        return {
            "widgets": [
                {
                    "type": "student_stats",
                    "title": "Student Engagement",
                    "position": {"row": 1, "col": 1, "span": 2},
                    "metrics": ["active_students", "facility_usage", "study_sessions"],
                },
                {
                    "type": "facility_overview",
                    "title": "Campus Facilities",
                    "position": {"row": 1, "col": 3, "span": 2},
                    "metrics": [
                        "available_spaces",
                        "peak_usage_times",
                        "popular_facilities",
                    ],
                },
                {
                    "type": "academic_calendar",
                    "title": "Academic Events",
                    "position": {"row": 2, "col": 1, "span": 3},
                },
                {
                    "type": "research_activity",
                    "title": "Research Usage",
                    "position": {"row": 2, "col": 4, "span": 1},
                    "roles": ["administrator", "account_owner"],
                },
            ],
            "quick_actions": [
                {
                    "name": "Schedule Study Room",
                    "action": "book_study_room",
                    "icon": "book",
                },
                {"name": "Campus Event", "action": "create_event", "icon": "calendar"},
                {
                    "name": "Student Support",
                    "action": "student_help",
                    "icon": "help-circle",
                },
                {
                    "name": "Facility Report",
                    "action": "usage_report",
                    "icon": "file-text",
                },
            ],
        }

    def get_default_page_templates(self) -> Dict[str, Dict[str, Any]]:
        """University page templates"""
        return {
            "homepage": {
                "name": "Campus Resource Center",
                "blocks": [
                    {
                        "type": "hero_banner",
                        "config": {
                            "title": "Campus Facility Resources",
                            "subtitle": "Book study spaces, labs, and meeting rooms for your academic success",
                            "cta_text": "Reserve Study Space",
                            "cta_action": "book_space",
                        },
                    },
                    {
                        "type": "facility_grid",
                        "config": {
                            "title": "Campus Facilities",
                            "show_availability": True,
                            "show_capacity": True,
                            "academic_focus": True,
                        },
                    },
                    {
                        "type": "academic_calendar",
                        "config": {
                            "title": "Academic Calendar & Events",
                            "show_semester_dates": True,
                        },
                    },
                ],
            }
        }

    def get_form_templates(self) -> Dict[str, Dict[str, Any]]:
        """University form templates"""
        return {
            "prospective_student": {
                "name": "Campus Visit Request",
                "fields": [
                    {"label": "Full Name", "type": "text", "required": True},
                    {"label": "Email", "type": "email", "required": True},
                    {"label": "High School", "type": "text", "required": False},
                    {
                        "label": "Intended Major",
                        "type": "select",
                        "required": False,
                        "options": [
                            "Engineering",
                            "Liberal Arts",
                            "Sciences",
                            "Business",
                            "Undecided",
                        ],
                    },
                    {"label": "Campus Tour Date", "type": "date", "required": True},
                    {
                        "label": "Areas of Interest",
                        "type": "textarea",
                        "required": False,
                    },
                ],
            },
            "research_space_request": {
                "name": "Research Space Booking",
                "fields": [
                    {"label": "Researcher Name", "type": "text", "required": True},
                    {"label": "Department", "type": "text", "required": True},
                    {"label": "Research Project", "type": "text", "required": True},
                    {
                        "label": "Space Type",
                        "type": "select",
                        "required": True,
                        "options": [
                            "Lab Space",
                            "Clean Room",
                            "Conference Room",
                            "Study Room",
                        ],
                    },
                    {
                        "label": "Equipment Needed",
                        "type": "textarea",
                        "required": False,
                    },
                    {
                        "label": "Duration",
                        "type": "select",
                        "required": True,
                        "options": [
                            "1 hour",
                            "2-4 hours",
                            "Half day",
                            "Full day",
                            "Multi-day",
                        ],
                    },
                ],
            },
        }

    def get_resource_types(self) -> List[Dict[str, Any]]:
        """University facility types"""
        return [
            {
                "type": "study_room",
                "display_name": "Study Room",
                "description": "Individual and group study spaces",
                "pricing_type": "free",
                "bookable": True,
                "requires_approval": False,
                "advance_booking_days": 7,
            },
            {
                "type": "lecture_hall",
                "display_name": "Lecture Hall",
                "description": "Large classroom for lectures and presentations",
                "pricing_type": "free",
                "bookable": True,
                "requires_approval": True,
                "advance_booking_days": 30,
            },
            {
                "type": "computer_lab",
                "display_name": "Computer Lab",
                "description": "Computer lab with specialized software",
                "pricing_type": "free",
                "bookable": True,
                "requires_approval": False,
                "advance_booking_days": 14,
            },
            {
                "type": "research_lab",
                "display_name": "Research Laboratory",
                "description": "Specialized research facilities",
                "pricing_type": "fee_based",
                "bookable": True,
                "requires_approval": True,
                "advance_booking_days": 30,
            },
        ]

    def get_dashboard_metrics(self) -> List[Dict[str, Any]]:
        """University dashboard metrics"""
        return [
            {
                "name": "active_students",
                "display_name": "Active Students",
                "type": "count",
                "importance": "high",
            },
            {
                "name": "facility_utilization",
                "display_name": "Facility Utilization",
                "type": "percentage",
                "importance": "high",
            },
            {
                "name": "study_sessions",
                "display_name": "Study Sessions",
                "type": "count",
                "importance": "medium",
            },
            {
                "name": "research_bookings",
                "display_name": "Research Bookings",
                "type": "count",
                "importance": "medium",
            },
        ]
