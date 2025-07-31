"""
Hotel Module - Industry-specific experience for hotel meeting spaces
Transforms the universal platform into a hospitality venue management solution
"""

from typing import Any, Dict, List

from modules.base_module import BaseModule


class HotelModule(BaseModule):
    """Hotel industry module - hospitality venue management"""

    def get_module_name(self) -> str:
        return "Executive Venue Management System"

    def get_module_version(self) -> str:
        return "1.0.0"

    def get_terminology_dictionary(self) -> Dict[str, str]:
        """Hotel-specific terminology"""
        return {
            # Core platform terms -> Hotel terms
            "users": "guests",
            "user": "guest",
            "customers": "clients",
            "customer": "client",
            "members": "valued clients",
            "member": "valued client",
            "bookings": "reservations",
            "booking": "reservation",
            "resources": "venues",
            "resource": "venue",
            "spaces": "event spaces",
            "space": "event space",
            "tours": "venue tours",
            "tour": "venue tour",
            "leads": "event inquiries",
            "lead": "event inquiry",
            "staff": "event coordinators",
            "administrator": "venue manager",
            "front_desk": "concierge",
            "revenue": "venue revenue",
            "payments": "event fees",
            "subscription": "corporate contract",
            "subscriptions": "corporate contracts",
            "invoices": "event invoices",
            "invoice": "event invoice",
        }

    def get_enabled_features(self) -> List[str]:
        """Features enabled for hotel venues"""
        return [
            "website_builder",
            "lead_management",
            "complex_resource_booking",
            "guest_management",
            "booking_system",
            "catering_management",
            "av_equipment",
            "concierge_services",
            "vip_services",
            "corporate_contracts",
            "event_planning",
            "room_service",
            "loyalty_program",
            "revenue_optimization",
            "seasonal_pricing",
            "package_deals",
            "corporate_rates",
            "event_coordination",
            "luxury_amenities",
        ]

    def get_active_workflows(self) -> List[Dict[str, Any]]:
        """Hotel-specific automation workflows"""
        return [
            {
                "name": "luxury_welcome",
                "trigger_event": "booking_created",
                "actions": [
                    {
                        "type": "send_message",
                        "template_id": "luxury_confirmation",
                        "recipient": "client",
                    },
                    {
                        "type": "send_message",
                        "template_id": "concierge_introduction",
                        "recipient": "client",
                        "delay_minutes": 30,
                    },
                    {
                        "type": "send_message",
                        "template_id": "event_coordinator_assignment",
                        "recipient": "event_coordinator",
                    },
                ],
            },
            {
                "name": "premium_follow_up",
                "trigger_event": "tour_completed",
                "actions": [
                    {
                        "type": "send_message",
                        "template_id": "personalized_proposal",
                        "recipient": "client",
                        "delay_minutes": 60,
                    },
                    {
                        "type": "send_message",
                        "template_id": "exclusive_packages",
                        "recipient": "client",
                        "delay_minutes": 1440,  # 24 hours
                    },
                    {
                        "type": "update_status",
                        "entity_type": "lead",
                        "status": "premium_follow_up",
                    },
                ],
            },
            {
                "name": "event_preparation",
                "trigger_event": "booking_confirmed",
                "actions": [
                    {
                        "type": "send_message",
                        "template_id": "pre_event_checklist",
                        "recipient": "event_coordinator",
                    },
                    {
                        "type": "send_message",
                        "template_id": "catering_coordination",
                        "recipient": "catering_manager",
                    },
                    {
                        "type": "send_message",
                        "template_id": "av_setup_request",
                        "recipient": "av_technician",
                    },
                ],
            },
            {
                "name": "vip_treatment",
                "trigger_event": "high_value_booking",
                "conditions": [
                    {"field": "booking_value", "operator": ">", "value": 5000}
                ],
                "actions": [
                    {
                        "type": "send_message",
                        "template_id": "vip_welcome",
                        "recipient": "client",
                    },
                    {
                        "type": "send_message",
                        "template_id": "manager_notification",
                        "recipient": "venue_manager",
                    },
                    {
                        "type": "update_status",
                        "entity_type": "booking",
                        "status": "vip_service",
                    },
                ],
            },
        ]

    def get_role_hierarchy(self) -> Dict[str, Dict[str, Any]]:
        """Hotel role structure"""
        return {
            "account_owner": {
                "display_name": "General Manager",
                "description": "Overall hotel operations and venue management",
                "permissions": ["*"],
                "level": 5,
            },
            "administrator": {
                "display_name": "Venue Manager",
                "description": "Manages event venues and client relationships",
                "permissions": [
                    "guests.manage",
                    "venues.manage",
                    "events.manage",
                    "reservations.manage",
                    "revenue.manage",
                    "reports.view",
                ],
                "level": 4,
            },
            "front_desk": {
                "display_name": "Concierge",
                "description": "Provides luxury service and guest assistance",
                "permissions": [
                    "guests.view",
                    "guests.assist",
                    "reservations.view",
                    "reservations.create",
                    "services.coordinate",
                    "amenities.manage",
                ],
                "level": 3,
            },
            "property_manager": {
                "display_name": "Event Coordinator",
                "description": "Coordinates events and client services",
                "permissions": [
                    "events.coordinate",
                    "catering.manage",
                    "av.coordinate",
                    "vendors.manage",
                    "setup.coordinate",
                ],
                "level": 3,
            },
            "maintenance": {
                "display_name": "Facilities Manager",
                "description": "Maintains venue quality and luxury standards",
                "permissions": [
                    "venues.maintain",
                    "equipment.manage",
                    "quality.ensure",
                ],
                "level": 2,
            },
            "member": {
                "display_name": "Corporate Client",
                "description": "Regular corporate client with booking privileges",
                "permissions": [
                    "reservations.create",
                    "reservations.view_own",
                    "venues.view",
                    "services.request",
                    "billing.view_own",
                ],
                "level": 1,
            },
        }

    def get_navigation_structure(self) -> List[Dict[str, Any]]:
        """Hotel navigation menu"""
        return [
            {
                "name": "Executive Dashboard",
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
                "name": "Book Venue",
                "path": "/booking",
                "icon": "calendar-plus",
                "roles": ["member"],
            },
            {
                "name": "Venue Gallery",
                "path": "/venues",
                "icon": "image",
                "roles": ["*"],
            },
            {
                "name": "Concierge Services",
                "path": "/services",
                "icon": "bell",
                "roles": ["member"],
            },
            {
                "name": "Event Planning",
                "path": "/planning",
                "icon": "clipboard",
                "roles": ["member"],
            },
            {
                "name": "Venue Management",
                "path": "/admin/venues",
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
                "name": "Client Relations",
                "path": "/leads",
                "icon": "user-plus",
                "roles": ["front_desk", "administrator", "account_owner"],
            },
            {
                "name": "Event Coordination",
                "path": "/admin/events",
                "icon": "users",
                "roles": ["property_manager", "administrator", "account_owner"],
            },
            {
                "name": "Venue Website",
                "path": "/cms/pages",
                "icon": "globe",
                "roles": ["administrator", "account_owner"],
            },
            {
                "name": "Revenue Analytics",
                "path": "/analytics",
                "icon": "trending-up",
                "roles": ["administrator", "account_owner"],
            },
        ]

    def get_dashboard_layout(self) -> Dict[str, Any]:
        """Hotel dashboard configuration"""
        return {
            "widgets": [
                {
                    "type": "revenue_summary",
                    "title": "Revenue Performance",
                    "position": {"row": 1, "col": 1, "span": 2},
                    "metrics": [
                        "daily_revenue",
                        "monthly_revenue",
                        "average_booking_value",
                    ],
                },
                {
                    "type": "booking_overview",
                    "title": "Today's Events",
                    "position": {"row": 1, "col": 3, "span": 2},
                    "metrics": ["today_events", "venue_utilization", "vip_bookings"],
                },
                {
                    "type": "client_satisfaction",
                    "title": "Guest Experience",
                    "position": {"row": 2, "col": 1, "span": 1},
                    "metrics": ["satisfaction_score", "repeat_clients", "referrals"],
                },
                {
                    "type": "venue_status",
                    "title": "Venue Status",
                    "position": {"row": 2, "col": 2, "span": 1},
                    "metrics": [
                        "venues_available",
                        "maintenance_scheduled",
                        "setup_in_progress",
                    ],
                },
                {
                    "type": "upcoming_events",
                    "title": "Upcoming Events",
                    "position": {"row": 2, "col": 3, "span": 2},
                },
                {
                    "type": "inquiry_pipeline",
                    "title": "Sales Pipeline",
                    "position": {"row": 3, "col": 1, "span": 2},
                    "roles": ["administrator", "account_owner"],
                },
                {
                    "type": "service_requests",
                    "title": "Service Requests",
                    "position": {"row": 3, "col": 3, "span": 1},
                    "roles": ["front_desk", "administrator", "account_owner"],
                },
            ],
            "quick_actions": [
                {
                    "name": "New Reservation",
                    "action": "create_reservation",
                    "icon": "plus",
                },
                {
                    "name": "Check Event Setup",
                    "action": "verify_setup",
                    "icon": "check-circle",
                },
                {
                    "name": "VIP Service Request",
                    "action": "vip_service",
                    "icon": "star",
                },
                {
                    "name": "Revenue Report",
                    "action": "revenue_report",
                    "icon": "dollar-sign",
                },
            ],
        }

    def get_default_page_templates(self) -> Dict[str, Dict[str, Any]]:
        """Hotel page templates"""
        return {
            "homepage": {
                "name": "Executive Venue Homepage",
                "blocks": [
                    {
                        "type": "luxury_hero",
                        "config": {
                            "title": "Executive Meeting Venues",
                            "subtitle": "Where business meets luxury in sophisticated surroundings",
                            "cta_text": "Schedule Private Tour",
                            "cta_action": "schedule_tour",
                            "background_video": "/videos/luxury-venue.mp4",
                        },
                    },
                    {
                        "type": "venue_showcase",
                        "config": {
                            "title": "Premium Event Spaces",
                            "show_capacity": True,
                            "show_amenities": True,
                            "luxury_focus": True,
                        },
                    },
                    {
                        "type": "service_highlights",
                        "config": {
                            "title": "Exceptional Services",
                            "services": [
                                "Dedicated Event Coordinator",
                                "Premium Catering",
                                "State-of-the-Art AV",
                                "Concierge Services",
                            ],
                        },
                    },
                    {
                        "type": "client_testimonials",
                        "config": {
                            "title": "What Our Clients Say",
                            "focus": "corporate_clients",
                            "show_company_logos": True,
                        },
                    },
                ],
            },
            "venues": {
                "name": "Venue Portfolio",
                "blocks": [
                    {
                        "type": "venue_gallery",
                        "config": {
                            "high_resolution": True,
                            "virtual_tour": True,
                            "capacity_info": True,
                        },
                    },
                    {
                        "type": "booking_calendar",
                        "config": {
                            "real_time_availability": True,
                            "premium_view": True,
                        },
                    },
                ],
            },
        }

    def get_form_templates(self) -> Dict[str, Dict[str, Any]]:
        """Hotel form templates"""
        return {
            "event_inquiry": {
                "name": "Executive Event Inquiry",
                "fields": [
                    {"label": "Company Name", "type": "text", "required": True},
                    {"label": "Contact Name", "type": "text", "required": True},
                    {"label": "Title/Position", "type": "text", "required": False},
                    {"label": "Email Address", "type": "email", "required": True},
                    {"label": "Phone Number", "type": "phone", "required": True},
                    {
                        "label": "Event Type",
                        "type": "select",
                        "required": True,
                        "options": [
                            "Board Meeting",
                            "Executive Retreat",
                            "Product Launch",
                            "Training Session",
                            "Corporate Conference",
                            "Private Dining",
                        ],
                    },
                    {
                        "label": "Preferred Venue",
                        "type": "select",
                        "required": False,
                        "options": [
                            "Executive Boardroom",
                            "Grand Ballroom",
                            "Terrace Suite",
                            "Private Dining Room",
                            "Conference Center",
                        ],
                    },
                    {"label": "Event Date", "type": "date", "required": True},
                    {"label": "Start Time", "type": "time", "required": True},
                    {"label": "End Time", "type": "time", "required": True},
                    {
                        "label": "Number of Attendees",
                        "type": "number",
                        "required": True,
                    },
                    {
                        "label": "Catering Requirements",
                        "type": "select",
                        "required": False,
                        "options": [
                            "None",
                            "Continental Breakfast",
                            "Working Lunch",
                            "Cocktail Reception",
                            "Full Dinner Service",
                            "Custom Menu",
                        ],
                    },
                    {
                        "label": "AV Equipment Needed",
                        "type": "checkbox",
                        "required": False,
                        "options": [
                            "Projector & Screen",
                            "Sound System",
                            "Video Conferencing",
                            "Wireless Microphones",
                            "Live Streaming",
                            "Recording Equipment",
                        ],
                    },
                    {
                        "label": "Special Requirements",
                        "type": "textarea",
                        "required": False,
                    },
                    {
                        "label": "Estimated Budget Range",
                        "type": "select",
                        "required": False,
                        "options": [
                            "Under $2,500",
                            "$2,500-$5,000",
                            "$5,000-$10,000",
                            "$10,000-$25,000",
                            "$25,000+",
                            "Prefer to discuss",
                        ],
                    },
                ],
            },
            "venue_tour": {
                "name": "Private Venue Tour Request",
                "fields": [
                    {"label": "Name", "type": "text", "required": True},
                    {"label": "Company", "type": "text", "required": True},
                    {"label": "Email", "type": "email", "required": True},
                    {"label": "Phone", "type": "phone", "required": True},
                    {"label": "Preferred Date", "type": "date", "required": True},
                    {
                        "label": "Preferred Time",
                        "type": "select",
                        "required": True,
                        "options": [
                            "9:00 AM",
                            "10:30 AM",
                            "12:00 PM",
                            "2:00 PM",
                            "3:30 PM",
                            "5:00 PM",
                        ],
                    },
                    {
                        "label": "Event Type Considering",
                        "type": "select",
                        "required": False,
                        "options": [
                            "Corporate Meeting",
                            "Executive Retreat",
                            "Product Launch",
                            "Training Event",
                            "Social Function",
                            "Multiple Events",
                        ],
                    },
                    {
                        "label": "Number of People",
                        "type": "select",
                        "required": False,
                        "options": ["1-10", "11-25", "26-50", "51-100", "100+"],
                    },
                    {
                        "label": "Special Interests",
                        "type": "textarea",
                        "required": False,
                    },
                ],
            },
            "corporate_contract": {
                "name": "Corporate Partnership Inquiry",
                "fields": [
                    {"label": "Company Name", "type": "text", "required": True},
                    {"label": "Primary Contact", "type": "text", "required": True},
                    {"label": "Title", "type": "text", "required": True},
                    {"label": "Email", "type": "email", "required": True},
                    {"label": "Phone", "type": "phone", "required": True},
                    {
                        "label": "Company Size",
                        "type": "select",
                        "required": False,
                        "options": [
                            "1-50 employees",
                            "51-200 employees",
                            "201-1000 employees",
                            "1000+ employees",
                        ],
                    },
                    {
                        "label": "Annual Event Volume",
                        "type": "select",
                        "required": True,
                        "options": [
                            "1-5 events",
                            "6-12 events",
                            "13-24 events",
                            "25+ events",
                        ],
                    },
                    {
                        "label": "Typical Event Types",
                        "type": "checkbox",
                        "required": True,
                        "options": [
                            "Board Meetings",
                            "Client Meetings",
                            "Training Sessions",
                            "Corporate Events",
                            "Product Launches",
                            "Conferences",
                        ],
                    },
                    {
                        "label": "Preferred Partnership Benefits",
                        "type": "checkbox",
                        "required": False,
                        "options": [
                            "Volume Discounts",
                            "Priority Booking",
                            "Dedicated Coordinator",
                            "Custom Catering Options",
                            "Flexible Cancellation",
                            "Billing Terms",
                        ],
                    },
                    {
                        "label": "Additional Information",
                        "type": "textarea",
                        "required": False,
                    },
                ],
            },
        }

    def get_resource_types(self) -> List[Dict[str, Any]]:
        """Hotel venue types"""
        return [
            {
                "type": "executive_boardroom",
                "display_name": "Executive Boardroom",
                "description": "Intimate luxury setting for high-level meetings",
                "pricing_type": "premium",
                "bookable": True,
                "requires_approval": False,
                "advance_booking_days": 90,
            },
            {
                "type": "grand_ballroom",
                "display_name": "Grand Ballroom",
                "description": "Elegant space for large corporate events",
                "pricing_type": "luxury",
                "bookable": True,
                "requires_approval": True,
                "advance_booking_days": 180,
            },
            {
                "type": "conference_center",
                "display_name": "Conference Center",
                "description": "State-of-the-art facility for conferences and training",
                "pricing_type": "standard",
                "bookable": True,
                "requires_approval": False,
                "advance_booking_days": 60,
            },
            {
                "type": "private_dining",
                "display_name": "Private Dining Room",
                "description": "Exclusive dining experience for business entertaining",
                "pricing_type": "premium",
                "bookable": True,
                "requires_approval": False,
                "advance_booking_days": 30,
            },
            {
                "type": "terrace_suite",
                "display_name": "Terrace Suite",
                "description": "Outdoor luxury space with city views",
                "pricing_type": "luxury",
                "bookable": True,
                "requires_approval": True,
                "advance_booking_days": 120,
            },
            {
                "type": "breakout_rooms",
                "display_name": "Breakout Rooms",
                "description": "Smaller spaces for workshops and team meetings",
                "pricing_type": "standard",
                "bookable": True,
                "requires_approval": False,
                "advance_booking_days": 14,
            },
        ]

    def get_booking_rules(self) -> Dict[str, Any]:
        """Hotel booking rules"""
        return {
            "advance_booking_days": 180,
            "min_booking_duration": 120,  # 2 hours
            "max_booking_duration": 720,  # 12 hours
            "allow_recurring": True,
            "require_approval": False,
            "luxury_service_rules": {
                "dedicated_coordinator": True,
                "pre_event_consultation": True,
                "post_event_follow_up": True,
            },
            "pricing_tiers": {
                "standard": 1.0,
                "premium": 1.5,
                "luxury": 2.0,
                "vip": 2.5,
            },
            "cancellation_policy": {
                "free_cancellation_hours": 48,
                "partial_refund_hours": 24,
                "penalty_percentage": 25,
            },
            "add_on_services": {
                "catering": True,
                "av_equipment": True,
                "concierge": True,
                "valet_parking": True,
                "floral_arrangements": True,
                "photography": True,
            },
        }

    def get_dashboard_metrics(self) -> List[Dict[str, Any]]:
        """Hotel dashboard metrics"""
        return [
            {
                "name": "venue_revenue",
                "display_name": "Venue Revenue",
                "type": "currency",
                "importance": "high",
                "description": "Total revenue from venue bookings",
            },
            {
                "name": "average_booking_value",
                "display_name": "Average Booking Value",
                "type": "currency",
                "importance": "high",
                "description": "Average revenue per booking",
            },
            {
                "name": "client_satisfaction",
                "display_name": "Client Satisfaction",
                "type": "rating",
                "importance": "high",
                "description": "Average satisfaction score from clients",
            },
            {
                "name": "venue_utilization",
                "display_name": "Venue Utilization",
                "type": "percentage",
                "importance": "high",
                "description": "Percentage of time venues are booked",
            },
            {
                "name": "repeat_clients",
                "display_name": "Repeat Clients",
                "type": "percentage",
                "importance": "medium",
                "description": "Percentage of bookings from repeat clients",
            },
            {
                "name": "corporate_contracts",
                "display_name": "Corporate Contracts",
                "type": "count",
                "importance": "medium",
                "description": "Active corporate partnership contracts",
            },
            {
                "name": "premium_bookings",
                "display_name": "Premium Bookings",
                "type": "percentage",
                "importance": "medium",
                "description": "Percentage of premium/luxury tier bookings",
            },
            {
                "name": "service_upsells",
                "display_name": "Service Upsells",
                "type": "currency",
                "importance": "medium",
                "description": "Revenue from additional services",
            },
        ]
