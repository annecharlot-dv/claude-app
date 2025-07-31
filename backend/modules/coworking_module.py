"""
Coworking Module - Industry-specific experience for coworking spaces
Transforms the universal platform into a coworking-focused solution
"""

from typing import Dict, Any, List
from modules.base_module import BaseModule


class CoworkingModule(BaseModule):
    """Coworking industry module - collaborative workspace management"""

    def get_module_name(self) -> str:
        return "Coworking Community Platform"

    def get_module_version(self) -> str:
        return "1.0.0"

    def get_terminology_dictionary(self) -> Dict[str, str]:
        """Coworking-specific terminology"""
        return {
            # Core platform terms -> Coworking terms
            "users": "members",
            "user": "member",
            "customers": "members",
            "customer": "member",
            "clients": "members",
            "client": "member",
            "bookings": "reservations",
            "booking": "reservation",
            "resources": "spaces",
            "resource": "space",
            "spaces": "workspaces",
            "space": "workspace",
            "tours": "space tours",
            "tour": "space tour",
            "leads": "prospects",
            "lead": "prospect",
            "staff": "community managers",
            "administrator": "space manager",
            "front_desk": "community host",
            "revenue": "membership revenue",
            "payments": "membership fees",
            "subscription": "membership",
            "subscriptions": "memberships",
            "invoices": "membership bills",
            "invoice": "membership bill",
        }

    def get_enabled_features(self) -> List[str]:
        """Features enabled for coworking spaces"""
        return [
            "website_builder",
            "lead_management",
            "community_platform",
            "events_system",
            "member_directory",
            "booking_system",
            "membership_management",
            "hot_desking",
            "meeting_rooms",
            "event_hosting",
            "networking_tools",
            "member_benefits",
            "flexible_pricing",
            "day_passes",
            "member_app",
            "community_board",
            "skill_sharing",
            "mentor_matching",
        ]

    def get_active_workflows(self) -> List[Dict[str, Any]]:
        """Coworking-specific automation workflows"""
        return [
            {
                "name": "member_onboarding",
                "trigger_event": "user_created",
                "actions": [
                    {
                        "type": "send_message",
                        "template_id": "coworking_welcome_email",
                        "delay_minutes": 0,
                    },
                    {
                        "type": "send_message",
                        "template_id": "community_guidelines",
                        "delay_minutes": 60,
                    },
                    {
                        "type": "update_status",
                        "entity_type": "user",
                        "status": "onboarded",
                    },
                ],
            },
            {
                "name": "tour_follow_up",
                "trigger_event": "tour_completed",
                "actions": [
                    {
                        "type": "send_message",
                        "template_id": "tour_thank_you",
                        "delay_minutes": 30,
                    },
                    {
                        "type": "send_message",
                        "template_id": "membership_offer",
                        "delay_minutes": 1440,  # 24 hours
                    },
                ],
            },
            {
                "name": "member_engagement",
                "trigger_event": "booking_created",
                "conditions": [{"field": "member_type", "value": "new"}],
                "actions": [
                    {
                        "type": "send_message",
                        "template_id": "first_booking_tips",
                        "delay_minutes": 15,
                    }
                ],
            },
            {
                "name": "community_events",
                "trigger_event": "event_published",
                "actions": [
                    {
                        "type": "send_message",
                        "template_id": "event_announcement",
                        "recipient": "all_members",
                    }
                ],
            },
        ]

    def get_role_hierarchy(self) -> Dict[str, Dict[str, Any]]:
        """Coworking role structure"""
        return {
            "account_owner": {
                "display_name": "Space Owner",
                "description": "Owns and operates the coworking space",
                "permissions": ["*"],
                "level": 5,
            },
            "administrator": {
                "display_name": "Space Manager",
                "description": "Manages day-to-day operations",
                "permissions": [
                    "members.manage",
                    "spaces.manage",
                    "events.manage",
                    "bookings.manage",
                    "finances.view",
                    "reports.view",
                ],
                "level": 4,
            },
            "front_desk": {
                "display_name": "Community Host",
                "description": "Welcomes members and manages front desk",
                "permissions": [
                    "members.view",
                    "members.checkin",
                    "bookings.view",
                    "bookings.create",
                    "tours.manage",
                    "events.view",
                ],
                "level": 3,
            },
            "maintenance": {
                "display_name": "Facilities Manager",
                "description": "Maintains spaces and equipment",
                "permissions": ["spaces.view", "spaces.update", "maintenance.manage"],
                "level": 2,
            },
            "member": {
                "display_name": "Community Member",
                "description": "Active member of the coworking community",
                "permissions": [
                    "bookings.create",
                    "bookings.view_own",
                    "events.view",
                    "events.register",
                    "community.participate",
                    "profile.manage",
                ],
                "level": 1,
            },
            "company_admin": {
                "display_name": "Team Lead",
                "description": "Manages team membership and bookings",
                "permissions": [
                    "team.manage",
                    "bookings.create_team",
                    "billing.view_team",
                ],
                "level": 1,
            },
        }

    def get_navigation_structure(self) -> List[Dict[str, Any]]:
        """Coworking navigation menu"""
        return [
            {
                "name": "Community Dashboard",
                "path": "/dashboard",
                "icon": "home",
                "roles": ["*"],
            },
            {
                "name": "My Workspace",
                "path": "/workspace",
                "icon": "briefcase",
                "roles": ["member", "company_admin", "company_user"],
            },
            {
                "name": "Book Spaces",
                "path": "/booking",
                "icon": "calendar",
                "roles": ["member", "company_admin", "company_user"],
            },
            {
                "name": "Community Events",
                "path": "/events",
                "icon": "users",
                "roles": ["*"],
            },
            {
                "name": "Member Directory",
                "path": "/members",
                "icon": "user-group",
                "roles": [
                    "member",
                    "company_admin",
                    "front_desk",
                    "administrator",
                    "account_owner",
                ],
            },
            {
                "name": "Community Board",
                "path": "/community",
                "icon": "message-square",
                "roles": ["member", "company_admin", "company_user"],
            },
            {
                "name": "Space Management",
                "path": "/admin/spaces",
                "icon": "building",
                "roles": ["administrator", "account_owner"],
            },
            {
                "name": "Member Management",
                "path": "/admin/members",
                "icon": "users",
                "roles": ["front_desk", "administrator", "account_owner"],
            },
            {
                "name": "Tours & Leads",
                "path": "/leads",
                "icon": "user-plus",
                "roles": ["front_desk", "administrator", "account_owner"],
            },
            {
                "name": "Website Builder",
                "path": "/cms/pages",
                "icon": "globe",
                "roles": ["administrator", "account_owner"],
            },
            {
                "name": "Community Analytics",
                "path": "/analytics",
                "icon": "bar-chart",
                "roles": ["administrator", "account_owner"],
            },
        ]

    def get_dashboard_layout(self) -> Dict[str, Any]:
        """Coworking dashboard configuration"""
        return {
            "widgets": [
                {
                    "type": "community_stats",
                    "title": "Community Health",
                    "position": {"row": 1, "col": 1, "span": 2},
                    "metrics": [
                        "active_members",
                        "daily_checkins",
                        "community_engagement",
                    ],
                },
                {
                    "type": "booking_overview",
                    "title": "Space Utilization",
                    "position": {"row": 1, "col": 3, "span": 2},
                    "metrics": ["today_bookings", "utilization_rate", "popular_spaces"],
                },
                {
                    "type": "revenue_summary",
                    "title": "Membership Revenue",
                    "position": {"row": 2, "col": 1, "span": 1},
                    "metrics": ["monthly_revenue", "new_memberships", "churn_rate"],
                },
                {
                    "type": "events_calendar",
                    "title": "Upcoming Events",
                    "position": {"row": 2, "col": 2, "span": 2},
                },
                {
                    "type": "member_activity",
                    "title": "Recent Member Activity",
                    "position": {"row": 3, "col": 1, "span": 3},
                },
                {
                    "type": "leads_pipeline",
                    "title": "Prospect Pipeline",
                    "position": {"row": 2, "col": 4, "span": 1},
                    "roles": ["front_desk", "administrator", "account_owner"],
                },
            ],
            "quick_actions": [
                {
                    "name": "Check In Member",
                    "action": "member_checkin",
                    "icon": "user-check",
                },
                {
                    "name": "Book Meeting Room",
                    "action": "quick_booking",
                    "icon": "calendar-plus",
                },
                {
                    "name": "Add New Member",
                    "action": "member_signup",
                    "icon": "user-plus",
                },
                {"name": "Schedule Tour", "action": "tour_booking", "icon": "clock"},
            ],
        }

    def get_default_page_templates(self) -> Dict[str, Dict[str, Any]]:
        """Coworking page templates"""
        return {
            "homepage": {
                "name": "Coworking Homepage",
                "blocks": [
                    {
                        "type": "hero_banner",
                        "config": {
                            "title": "Where Innovation Meets Collaboration",
                            "subtitle": "Join our vibrant coworking community and grow your business",
                            "cta_text": "Tour Our Space",
                            "cta_action": "schedule_tour",
                        },
                    },
                    {
                        "type": "membership_plans",
                        "config": {
                            "title": "Choose Your Membership",
                            "show_pricing": True,
                            "highlight_popular": True,
                        },
                    },
                    {
                        "type": "community_testimonials",
                        "config": {
                            "title": "What Our Members Say",
                            "show_photos": True,
                            "auto_rotate": True,
                        },
                    },
                    {
                        "type": "space_gallery",
                        "config": {
                            "title": "Explore Our Spaces",
                            "show_360_tour": True,
                        },
                    },
                ],
            },
            "membership": {
                "name": "Membership Plans",
                "blocks": [
                    {
                        "type": "pricing_comparison",
                        "config": {"show_features": True, "allow_online_signup": True},
                    },
                    {
                        "type": "member_benefits",
                        "config": {"highlight_community": True},
                    },
                ],
            },
        }

    def get_form_templates(self) -> Dict[str, Dict[str, Any]]:
        """Coworking form templates"""
        return {
            "membership_inquiry": {
                "name": "Membership Interest Form",
                "fields": [
                    {"label": "Full Name", "type": "text", "required": True},
                    {"label": "Email", "type": "email", "required": True},
                    {"label": "Company", "type": "text", "required": False},
                    {"label": "Phone", "type": "phone", "required": False},
                    {
                        "label": "Membership Type",
                        "type": "select",
                        "required": True,
                        "options": [
                            "Hot Desk",
                            "Dedicated Desk",
                            "Private Office",
                            "Team Space",
                        ],
                    },
                    {
                        "label": "How did you hear about us?",
                        "type": "select",
                        "required": False,
                        "options": [
                            "Google Search",
                            "Social Media",
                            "Referral",
                            "Walking By",
                            "Event",
                            "Other",
                        ],
                    },
                    {
                        "label": "Tell us about your business",
                        "type": "textarea",
                        "required": False,
                    },
                ],
            },
            "tour_request": {
                "name": "Schedule a Tour",
                "fields": [
                    {"label": "Name", "type": "text", "required": True},
                    {"label": "Email", "type": "email", "required": True},
                    {"label": "Phone", "type": "phone", "required": False},
                    {"label": "Preferred Date", "type": "date", "required": True},
                    {
                        "label": "Preferred Time",
                        "type": "select",
                        "required": True,
                        "options": [
                            "9:00 AM",
                            "10:00 AM",
                            "11:00 AM",
                            "2:00 PM",
                            "3:00 PM",
                            "4:00 PM",
                        ],
                    },
                    {
                        "label": "What type of workspace interests you?",
                        "type": "select",
                        "required": False,
                        "options": [
                            "Hot Desk",
                            "Dedicated Desk",
                            "Private Office",
                            "Meeting Rooms",
                            "Event Space",
                        ],
                    },
                ],
            },
            "event_registration": {
                "name": "Event Registration",
                "fields": [
                    {"label": "Name", "type": "text", "required": True},
                    {"label": "Email", "type": "email", "required": True},
                    {
                        "label": "Member Status",
                        "type": "select",
                        "required": True,
                        "options": ["Current Member", "Former Member", "Not a Member"],
                    },
                    {
                        "label": "Dietary Restrictions",
                        "type": "textarea",
                        "required": False,
                    },
                    {
                        "label": "How did you hear about this event?",
                        "type": "select",
                        "required": False,
                        "options": [
                            "Email Newsletter",
                            "Community Board",
                            "Social Media",
                            "Word of Mouth",
                        ],
                    },
                ],
            },
        }

    def get_resource_types(self) -> List[Dict[str, Any]]:
        """Coworking resource types"""
        return [
            {
                "type": "hot_desk",
                "display_name": "Hot Desk",
                "description": "Flexible seating at shared tables",
                "pricing_type": "hourly",
                "bookable": True,
                "requires_approval": False,
                "advance_booking_days": 7,
            },
            {
                "type": "dedicated_desk",
                "display_name": "Dedicated Desk",
                "description": "Your own desk with storage",
                "pricing_type": "monthly",
                "bookable": False,
                "requires_approval": True,
                "advance_booking_days": 0,
            },
            {
                "type": "meeting_room",
                "display_name": "Meeting Room",
                "description": "Private rooms for meetings and calls",
                "pricing_type": "hourly",
                "bookable": True,
                "requires_approval": False,
                "advance_booking_days": 14,
            },
            {
                "type": "private_office",
                "display_name": "Private Office",
                "description": "Fully private office space",
                "pricing_type": "monthly",
                "bookable": False,
                "requires_approval": True,
                "advance_booking_days": 0,
            },
            {
                "type": "event_space",
                "display_name": "Event Space",
                "description": "Large space for events and workshops",
                "pricing_type": "daily",
                "bookable": True,
                "requires_approval": True,
                "advance_booking_days": 30,
            },
            {
                "type": "phone_booth",
                "display_name": "Phone Booth",
                "description": "Private space for calls",
                "pricing_type": "hourly",
                "bookable": True,
                "requires_approval": False,
                "advance_booking_days": 1,
            },
        ]

    def get_booking_rules(self) -> Dict[str, Any]:
        """Coworking booking rules"""
        return {
            "advance_booking_days": 14,
            "min_booking_duration": 30,  # 30 minutes
            "max_booking_duration": 480,  # 8 hours
            "allow_recurring": True,
            "require_approval": False,
            "cancellation_policy": {
                "free_cancellation_hours": 2,
                "penalty_percentage": 50,
            },
            "member_benefits": {
                "booking_credits": True,
                "priority_booking": True,
                "extended_hours": True,
            },
            "no_show_policy": {"mark_no_show_minutes": 15, "penalty_for_no_show": True},
        }

    def get_dashboard_metrics(self) -> List[Dict[str, Any]]:
        """Coworking dashboard metrics"""
        return [
            {
                "name": "active_members",
                "display_name": "Active Members",
                "type": "count",
                "importance": "high",
                "description": "Members who visited this month",
            },
            {
                "name": "space_utilization",
                "display_name": "Space Utilization",
                "type": "percentage",
                "importance": "high",
                "description": "Percentage of time spaces are booked",
            },
            {
                "name": "member_satisfaction",
                "display_name": "Member Satisfaction",
                "type": "rating",
                "importance": "high",
                "description": "Average member satisfaction score",
            },
            {
                "name": "monthly_revenue",
                "display_name": "Monthly Revenue",
                "type": "currency",
                "importance": "high",
                "description": "Total membership and booking revenue",
            },
            {
                "name": "new_members",
                "display_name": "New Members",
                "type": "count",
                "importance": "medium",
                "description": "Members who joined this month",
            },
            {
                "name": "event_attendance",
                "display_name": "Event Attendance",
                "type": "count",
                "importance": "medium",
                "description": "Total event attendance this month",
            },
            {
                "name": "community_engagement",
                "display_name": "Community Engagement",
                "type": "score",
                "importance": "medium",
                "description": "Member interaction and participation score",
            },
        ]
