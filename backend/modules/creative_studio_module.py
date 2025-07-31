"""
Creative Studio Module - Industry-specific experience for creative/production studios
Transforms the universal platform into a creative studio management solution
"""

from typing import Dict, Any, List
from .base_module import BaseModule


class CreativeStudioModule(BaseModule):
    """Creative Studio industry module - creative space and production management"""

    def get_module_name(self) -> str:
        return "Creative Studio Management Platform"

    def get_module_version(self) -> str:
        return "1.0.0"

    def get_terminology_dictionary(self) -> Dict[str, str]:
        """Creative studio-specific terminology"""
        return {
            # Core platform terms -> Creative studio terms
            "users": "creatives",
            "user": "creative",
            "customers": "artists",
            "customer": "artist",
            "clients": "creative professionals",
            "client": "creative professional",
            "members": "studio members",
            "member": "studio member",
            "bookings": "studio sessions",
            "booking": "studio session",
            "resources": "creative spaces",
            "resource": "creative space",
            "spaces": "studios",
            "space": "studio",
            "tours": "studio tours",
            "tour": "studio tour",
            "leads": "prospective artists",
            "lead": "prospective artist",
            "staff": "studio coordinators",
            "administrator": "studio manager",
            "front_desk": "studio host",
            "revenue": "studio revenue",
            "payments": "session fees",
            "subscription": "studio membership",
            "subscriptions": "studio memberships",
            "invoices": "session invoices",
            "invoice": "session invoice",
        }

    def get_enabled_features(self) -> List[str]:
        """Features enabled for creative studios"""
        return [
            "website_builder",
            "lead_management",
            "booking_system",
            "equipment_management",
            "portfolio_showcase",
            "artist_directory",
            "project_collaboration",
            "creative_workshops",
            "equipment_rental",
            "studio_memberships",
            "production_calendar",
            "client_galleries",
            "creative_community",
            "skill_sharing",
            "mentor_program",
            "exhibition_planning",
            "digital_portfolio",
            "creative_networking",
            "studio_showcases",
        ]

    def get_active_workflows(self) -> List[Dict[str, Any]]:
        """Creative studio-specific automation workflows"""
        return [
            {
                "name": "artist_welcome",
                "trigger_event": "user_created",
                "actions": [
                    {
                        "type": "send_message",
                        "template_id": "creative_welcome",
                        "delay_minutes": 0,
                    },
                    {
                        "type": "send_message",
                        "template_id": "studio_orientation_guide",
                        "delay_minutes": 30,
                    },
                ],
            },
            {
                "name": "session_preparation",
                "trigger_event": "booking_created",
                "actions": [
                    {
                        "type": "send_message",
                        "template_id": "session_confirmation",
                        "recipient": "artist",
                    },
                    {
                        "type": "send_message",
                        "template_id": "equipment_setup_notice",
                        "recipient": "studio_technician",
                    },
                ],
            },
            {
                "name": "portfolio_review",
                "trigger_event": "booking_completed",
                "actions": [
                    {
                        "type": "send_message",
                        "template_id": "session_feedback",
                        "recipient": "artist",
                        "delay_minutes": 60,
                    },
                    {
                        "type": "send_message",
                        "template_id": "portfolio_tips",
                        "recipient": "artist",
                        "delay_minutes": 1440,
                    },
                ],
            },
            {
                "name": "exhibition_promotion",
                "trigger_event": "event_published",
                "conditions": [{"field": "event_type", "value": "exhibition"}],
                "actions": [
                    {
                        "type": "send_message",
                        "template_id": "exhibition_announcement",
                        "recipient": "all_members",
                    }
                ],
            },
        ]

    def get_role_hierarchy(self) -> Dict[str, Dict[str, Any]]:
        """Creative studio role structure"""
        return {
            "account_owner": {
                "display_name": "Studio Owner",
                "description": "Owns and operates the creative studio",
                "permissions": ["*"],
                "level": 5,
            },
            "administrator": {
                "display_name": "Studio Manager",
                "description": "Manages studio operations and creative programs",
                "permissions": [
                    "artists.manage",
                    "studios.manage",
                    "events.manage",
                    "sessions.manage",
                    "equipment.manage",
                    "revenue.view",
                ],
                "level": 4,
            },
            "front_desk": {
                "display_name": "Studio Host",
                "description": "Welcomes artists and manages studio access",
                "permissions": [
                    "artists.view",
                    "sessions.view",
                    "sessions.create",
                    "equipment.assist",
                    "tours.manage",
                ],
                "level": 3,
            },
            "instructor": {
                "display_name": "Creative Instructor",
                "description": "Teaches workshops and mentors artists",
                "permissions": [
                    "workshops.create",
                    "workshops.manage",
                    "mentoring.provide",
                    "artist_development.guide",
                ],
                "level": 3,
            },
            "technician": {
                "display_name": "Studio Technician",
                "description": "Maintains equipment and provides technical support",
                "permissions": [
                    "equipment.maintain",
                    "technical_support.provide",
                    "setup.assist",
                ],
                "level": 2,
            },
            "member": {
                "display_name": "Studio Member",
                "description": "Creative professional with studio access",
                "permissions": [
                    "sessions.create",
                    "sessions.view_own",
                    "equipment.use",
                    "workshops.attend",
                    "community.participate",
                    "portfolio.manage",
                ],
                "level": 1,
            },
            "artist": {
                "display_name": "Creative Artist",
                "description": "Individual artist with studio privileges",
                "permissions": [
                    "sessions.create",
                    "portfolio.create",
                    "exhibitions.participate",
                ],
                "level": 1,
            },
        }

    def get_navigation_structure(self) -> List[Dict[str, Any]]:
        """Creative studio navigation menu"""
        return [
            {
                "name": "Creative Dashboard",
                "path": "/dashboard",
                "icon": "home",
                "roles": ["*"],
            },
            {
                "name": "My Studio Sessions",
                "path": "/sessions",
                "icon": "calendar",
                "roles": ["member", "artist"],
            },
            {
                "name": "Book Studio",
                "path": "/booking",
                "icon": "calendar-plus",
                "roles": ["member", "artist"],
            },
            {
                "name": "Creative Workshops",
                "path": "/workshops",
                "icon": "users",
                "roles": ["*"],
            },
            {
                "name": "Artist Directory",
                "path": "/artists",
                "icon": "user-group",
                "roles": ["*"],
            },
            {
                "name": "Equipment Rental",
                "path": "/equipment",
                "icon": "tool",
                "roles": ["member", "artist"],
            },
            {
                "name": "Portfolio Showcase",
                "path": "/portfolio",
                "icon": "image",
                "roles": ["member", "artist"],
            },
            {
                "name": "Creative Community",
                "path": "/community",
                "icon": "message-square",
                "roles": ["member", "artist"],
            },
            {
                "name": "Studio Management",
                "path": "/admin/studios",
                "icon": "building",
                "roles": ["administrator", "account_owner"],
            },
            {
                "name": "Artist Management",
                "path": "/admin/artists",
                "icon": "users",
                "roles": ["front_desk", "administrator", "account_owner"],
            },
            {
                "name": "Prospective Artists",
                "path": "/leads",
                "icon": "user-plus",
                "roles": ["front_desk", "administrator", "account_owner"],
            },
            {
                "name": "Studio Website",
                "path": "/cms/pages",
                "icon": "globe",
                "roles": ["administrator", "account_owner"],
            },
            {
                "name": "Creative Analytics",
                "path": "/analytics",
                "icon": "bar-chart",
                "roles": ["administrator", "account_owner"],
            },
        ]

    def get_dashboard_layout(self) -> Dict[str, Any]:
        """Creative studio dashboard configuration"""
        return {
            "widgets": [
                {
                    "type": "creative_activity",
                    "title": "Creative Activity",
                    "position": {"row": 1, "col": 1, "span": 2},
                    "metrics": ["active_artists", "studio_sessions", "creative_hours"],
                },
                {
                    "type": "studio_utilization",
                    "title": "Studio Usage",
                    "position": {"row": 1, "col": 3, "span": 2},
                    "metrics": ["studio_bookings", "equipment_usage", "peak_times"],
                },
                {
                    "type": "creative_community",
                    "title": "Community Engagement",
                    "position": {"row": 2, "col": 1, "span": 2},
                    "metrics": [
                        "workshop_attendance",
                        "portfolio_uploads",
                        "collaborations",
                    ],
                },
                {
                    "type": "upcoming_workshops",
                    "title": "Upcoming Workshops",
                    "position": {"row": 2, "col": 3, "span": 2},
                },
                {
                    "type": "featured_portfolios",
                    "title": "Featured Work",
                    "position": {"row": 3, "col": 1, "span": 3},
                },
            ],
            "quick_actions": [
                {"name": "Book Studio Time", "action": "book_studio", "icon": "camera"},
                {
                    "name": "Schedule Workshop",
                    "action": "create_workshop",
                    "icon": "users",
                },
                {"name": "Upload Portfolio", "action": "upload_work", "icon": "upload"},
                {
                    "name": "Equipment Check",
                    "action": "equipment_status",
                    "icon": "settings",
                },
            ],
        }

    def get_default_page_templates(self) -> Dict[str, Dict[str, Any]]:
        """Creative studio page templates"""
        return {
            "homepage": {
                "name": "Creative Studio Homepage",
                "blocks": [
                    {
                        "type": "hero_banner",
                        "config": {
                            "title": "Unleash Your Creative Potential",
                            "subtitle": "Professional studios, expert guidance, and a vibrant creative community",
                            "cta_text": "Tour Our Studios",
                            "cta_action": "schedule_tour",
                            "creative_focus": True,
                        },
                    },
                    {
                        "type": "studio_showcase",
                        "config": {
                            "title": "Our Creative Spaces",
                            "show_equipment": True,
                            "show_pricing": True,
                            "visual_emphasis": True,
                        },
                    },
                    {
                        "type": "artist_galleries",
                        "config": {
                            "title": "Featured Artist Work",
                            "rotating_showcase": True,
                        },
                    },
                    {
                        "type": "workshop_calendar",
                        "config": {
                            "title": "Creative Workshops & Events",
                            "show_instructors": True,
                        },
                    },
                ],
            }
        }

    def get_form_templates(self) -> Dict[str, Dict[str, Any]]:
        """Creative studio form templates"""
        return {
            "artist_application": {
                "name": "Studio Membership Application",
                "fields": [
                    {"label": "Artist Name", "type": "text", "required": True},
                    {"label": "Email", "type": "email", "required": True},
                    {
                        "label": "Creative Medium",
                        "type": "select",
                        "required": True,
                        "options": [
                            "Photography",
                            "Videography",
                            "Digital Art",
                            "Traditional Art",
                            "Sculpture",
                            "Mixed Media",
                            "Music Production",
                            "Other",
                        ],
                    },
                    {
                        "label": "Experience Level",
                        "type": "select",
                        "required": True,
                        "options": [
                            "Beginner",
                            "Intermediate",
                            "Advanced",
                            "Professional",
                        ],
                    },
                    {"label": "Portfolio Website", "type": "url", "required": False},
                    {"label": "Creative Goals", "type": "textarea", "required": True},
                    {
                        "label": "Preferred Studio Type",
                        "type": "select",
                        "required": False,
                        "options": [
                            "Photography Studio",
                            "Video Production",
                            "Art Studio",
                            "Music Studio",
                            "Co-working Creative Space",
                        ],
                    },
                ],
            },
            "studio_booking": {
                "name": "Studio Session Request",
                "fields": [
                    {"label": "Project Name", "type": "text", "required": True},
                    {
                        "label": "Studio Type",
                        "type": "select",
                        "required": True,
                        "options": [
                            "Photography Studio",
                            "Video Production",
                            "Recording Studio",
                            "Art Studio",
                            "Green Screen Studio",
                        ],
                    },
                    {"label": "Session Date", "type": "date", "required": True},
                    {
                        "label": "Duration",
                        "type": "select",
                        "required": True,
                        "options": [
                            "2 hours",
                            "4 hours",
                            "6 hours",
                            "8 hours",
                            "Full day",
                        ],
                    },
                    {
                        "label": "Equipment Needed",
                        "type": "checkbox",
                        "required": False,
                        "options": [
                            "Lighting Kit",
                            "Camera Equipment",
                            "Audio Equipment",
                            "Backdrop",
                            "Props",
                            "Editing Station",
                        ],
                    },
                    {
                        "label": "Project Description",
                        "type": "textarea",
                        "required": False,
                    },
                ],
            },
        }

    def get_resource_types(self) -> List[Dict[str, Any]]:
        """Creative studio resource types"""
        return [
            {
                "type": "photo_studio",
                "display_name": "Photography Studio",
                "description": "Professional photography space with lighting",
                "pricing_type": "hourly",
                "bookable": True,
                "requires_approval": False,
                "advance_booking_days": 14,
            },
            {
                "type": "video_studio",
                "display_name": "Video Production Studio",
                "description": "Video production space with professional equipment",
                "pricing_type": "hourly",
                "bookable": True,
                "requires_approval": False,
                "advance_booking_days": 21,
            },
            {
                "type": "recording_studio",
                "display_name": "Recording Studio",
                "description": "Sound-proof recording space with audio equipment",
                "pricing_type": "hourly",
                "bookable": True,
                "requires_approval": True,
                "advance_booking_days": 30,
            },
            {
                "type": "art_studio",
                "display_name": "Art Studio",
                "description": "Creative workspace for traditional and digital art",
                "pricing_type": "hourly",
                "bookable": True,
                "requires_approval": False,
                "advance_booking_days": 7,
            },
        ]

    def get_dashboard_metrics(self) -> List[Dict[str, Any]]:
        """Creative studio dashboard metrics"""
        return [
            {
                "name": "active_artists",
                "display_name": "Active Creatives",
                "type": "count",
                "importance": "high",
            },
            {
                "name": "studio_utilization",
                "display_name": "Studio Utilization",
                "type": "percentage",
                "importance": "high",
            },
            {
                "name": "creative_sessions",
                "display_name": "Creative Sessions",
                "type": "count",
                "importance": "high",
            },
            {
                "name": "portfolio_uploads",
                "display_name": "Portfolio Uploads",
                "type": "count",
                "importance": "medium",
            },
            {
                "name": "workshop_attendance",
                "display_name": "Workshop Attendance",
                "type": "count",
                "importance": "medium",
            },
        ]
