#!/usr/bin/env python3
"""
Seed demo data for Claude Platform - Complete Space-as-a-Service platform
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from passlib.context import CryptContext
from sqlalchemy import delete, select

from database.config.connection_pool import PostgreSQLConnectionManager
from models.postgresql_models import (
    Form,
    Lead,
    Page,
    Template,
    Tenant,
    Tour,
    TourSlot,
    User,
    UserPassword,
)

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# Database connection
connection_manager = PostgreSQLConnectionManager()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed_claude_platform():
    print("🏢 Seeding Claude Platform - Space-as-a-Service " "Demo Data...")

    async with connection_manager.get_session() as session:
        # Clear existing data
        await session.execute(delete(Tour))
        await session.execute(delete(TourSlot))
        await session.execute(delete(Lead))
        await session.execute(delete(Form))
        await session.execute(delete(Page))
        await session.execute(delete(Template))
        await session.execute(delete(UserPassword))
        await session.execute(delete(User))
        await session.execute(delete(Tenant))
        await session.commit()

    # Create industry templates
    templates = [
        {
            "id": str(uuid.uuid4()),
            "name": "Coworking Modern",
            "industry_module": "coworking",
            "preview_image": "/images/templates/coworking-modern.jpg",
            "layout_config": {
                "primary_color": "#3B82F6",
                "secondary_color": "#1E40AF",
                "font_family": "Inter",
            },
            "default_content": {
                "hero_title": "Where Innovation Meets Collaboration",
                "hero_subtitle": "Join our vibrant coworking " "community",
            },
            "is_active": True,
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Government Clean",
            "industry_module": "government",
            "preview_image": "/images/templates/" "government-clean.jpg",
            "layout_config": {
                "primary_color": "#059669",
                "secondary_color": "#047857",
                "font_family": "Inter",
            },
            "default_content": {
                "hero_title": "Public Facility Reservations",
                "hero_subtitle": "Book community spaces for your " "events",
            },
            "is_active": True,
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Hotel Luxury",
            "industry_module": "hotel",
            "preview_image": "/images/templates/hotel-luxury.jpg",
            "layout_config": {
                "primary_color": "#DC2626",
                "secondary_color": "#B91C1C",
                "font_family": "Playfair Display",
            },
            "default_content": {
                "hero_title": "Executive Meeting Venues",
                "hero_subtitle": "Where business meets luxury",
            },
            "is_active": True,
        },
        {
            "id": str(uuid.uuid4()),
            "name": "University Academic",
            "industry_module": "university",
            "preview_image": "/images/templates/university-academic.jpg",
            "layout_config": {
                "primary_color": "#7C3AED",
                "secondary_color": "#6D28D9",
                "font_family": "Source Serif Pro",
            },
            "default_content": {
                "hero_title": "Campus Resource Center",
                "hero_subtitle": "Book study spaces and facilities for "
                "academic success",
            },
            "is_active": True,
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Creative Studio",
            "industry_module": "creative_studio",
            "preview_image": "/images/templates/creative-studio.jpg",
            "layout_config": {
                "primary_color": "#EA580C",
                "secondary_color": "#DC2626",
                "font_family": "Montserrat",
            },
            "default_content": {
                "hero_title": "Unleash Your Creative Potential",
                "hero_subtitle": "Professional studios and creative community",
            },
            "is_active": True,
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Residential Modern",
            "industry_module": "residential",
            "preview_image": "/images/templates/residential-modern.jpg",
            "layout_config": {
                "primary_color": "#0891B2",
                "secondary_color": "#0E7490",
                "font_family": "Inter",
            },
            "default_content": {
                "hero_title": "Your Home, Enhanced by Community",
                "hero_subtitle": "Modern living with premium amenities",
            },
            "is_active": True,
        },
    ]

    for template in templates:
        session.add(template)
        await session.commit()
        print(f"✅ Created template: {template['name']}")

    # Create demo tenants for different industries
    tenants_data = [
        {
            "name": "Downtown Coworking Hub",
            "subdomain": "downtown-hub",
            "industry_module": "coworking",
            "admin_email": "admin@downtownhub.com",
            "admin_password": "password123",
            "branding": {
                "primary_color": "#3B82F6",
                "secondary_color": "#1E40AF",
                "logo_url": "/images/logos/downtown-hub.svg",
                "tagline": "Where innovation meets collaboration",
            },
            "feature_toggles": {
                "website_builder": True,
                "lead_management": True,
                "community_platform": True,
                "events_system": True,
                "member_directory": True,
                "booking_system": True,
            },
        },
        {
            "name": "City Hall Facilities",
            "subdomain": "city-hall",
            "industry_module": "government",
            "admin_email": "facilities@cityhall.gov",
            "admin_password": "password123",
            "branding": {
                "primary_color": "#059669",
                "secondary_color": "#047857",
                "logo_url": "/images/logos/city-hall.svg",
                "tagline": "Serving our community",
            },
            "feature_toggles": {
                "website_builder": True,
                "lead_management": True,
                "approval_workflows": True,
                "public_transparency": True,
                "accessibility_features": True,
                "booking_system": True,
            },
        },
        {
            "name": "Grand Hotel Business Center",
            "subdomain": "grand-hotel",
            "industry_module": "hotel",
            "admin_email": "events@grandhotel.com",
            "admin_password": "password123",
            "branding": {
                "primary_color": "#7C2D12",
                "secondary_color": "#92400E",
                "logo_url": "/images/logos/grand-hotel.svg",
                "tagline": "Luxury meets productivity",
            },
            "feature_toggles": {
                "website_builder": True,
                "lead_management": True,
                "complex_resource_booking": True,
                "guest_management": True,
                "booking_system": True,
            },
        },
        {
            "name": "State University Campus",
            "subdomain": "state-university",
            "industry_module": "university",
            "admin_email": "facilities@stateuniversity.edu",
            "admin_password": "password123",
            "branding": {
                "primary_color": "#7C3AED",
                "secondary_color": "#6D28D9",
                "logo_url": "/images/logos/state-university.svg",
                "tagline": "Academic excellence in every space",
            },
            "feature_toggles": {
                "website_builder": True,
                "lead_management": True,
                "academic_calendar": True,
                "sso_integration": True,
                "research_facilities": True,
                "booking_system": True,
            },
        },
        {
            "name": "Artisan Creative Studios",
            "subdomain": "artisan-studios",
            "industry_module": "creative_studio",
            "admin_email": "studio@artisancreative.com",
            "admin_password": "password123",
            "branding": {
                "primary_color": "#EA580C",
                "secondary_color": "#DC2626",
                "logo_url": "/images/logos/artisan-studios.svg",
                "tagline": "Where creativity comes to life",
            },
            "feature_toggles": {
                "website_builder": True,
                "lead_management": True,
                "portfolio_showcase": True,
                "equipment_rental": True,
                "creative_workshops": True,
                "booking_system": True,
            },
        },
        {
            "name": "Metropolitan Lofts",
            "subdomain": "metro-lofts",
            "industry_module": "residential",
            "admin_email": "management@metrolofts.com",
            "admin_password": "password123",
            "branding": {
                "primary_color": "#0891B2",
                "secondary_color": "#0E7490",
                "logo_url": "/images/logos/metro-lofts.svg",
                "tagline": "Modern living, community focused",
            },
            "feature_toggles": {
                "website_builder": True,
                "lead_management": True,
                "resident_portal": True,
                "maintenance_requests": True,
                "community_events": True,
                "booking_system": True,
            },
        },
    ]

    created_tenants = []
    for tenant_data in tenants_data:
        # Create tenant
        tenant = {
            "id": str(uuid.uuid4()),
            "name": tenant_data["name"],
            "subdomain": tenant_data["subdomain"],
            "industry_module": tenant_data["industry_module"],
            "plan": "professional",
            "is_active": True,
            "branding": tenant_data["branding"],
            "feature_toggles": tenant_data["feature_toggles"],
            "settings": {
                "timezone": "America/New_York",
                "language": "en",
                "currency": "USD",
            },
            "created_at": datetime.utcnow(),
        }
        tenant_obj = Tenant(**tenant)
        session.add(tenant_obj)
        await session.commit()
        created_tenants.append(tenant)

        # Create admin user
        hashed_password = pwd_context.hash(tenant_data["admin_password"])
        admin_user = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant["id"],
            "email": tenant_data["admin_email"],
            "first_name": "Account",
            "last_name": "Owner",
            "role": "account_owner",
            "is_active": True,
            "profile": {
                "bio": f"Managing {tenant['name']} operations",
                "job_title": "Facilities Manager",
            },
            "created_at": datetime.utcnow(),
        }
        admin_user_obj = User(**admin_user)
        session.add(admin_user_obj)

        user_password = UserPassword(
            user_id=admin_user["id"], hashed_password=hashed_password
        )
        session.add(user_password)
        await session.commit()

        # Create additional staff users
        staff_users = [
            {
                "email": f"manager@{tenant['subdomain']}.com",
                "first_name": "Property",
                "last_name": "Manager",
                "role": "property_manager",
            },
            {
                "email": f"front-desk@{tenant['subdomain']}.com",
                "first_name": "Front",
                "last_name": "Desk",
                "role": "front_desk",
            },
        ]

        for staff_data in staff_users:
            staff_user = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant["id"],
                "email": staff_data["email"],
                "first_name": staff_data["first_name"],
                "last_name": staff_data["last_name"],
                "role": staff_data["role"],
                "is_active": True,
                "profile": {},
                "created_at": datetime.utcnow(),
            }
            staff_user_obj = User(**staff_user)
            session.add(staff_user_obj)

            user_password = UserPassword(
                user_id=staff_user["id"],
                hashed_password=pwd_context.hash("password123"),
            )
            session.add(user_password)
            await session.commit()

        print(
            f"✅ Created tenant: {tenant['name']} with " f"{len(staff_users) + 1} users"
        )

    # Create pages for each tenant
    for tenant in created_tenants:
        # Get appropriate template
        result = await session.execute(
            select(Template).where(
                Template.industry_module == tenant["industry_module"]
            )
        )
        template = result.scalar_one_or_none()

        # Create homepage
        if tenant["industry_module"] == "coworking":
            content_blocks = [
                {
                    "id": str(uuid.uuid4()),
                    "type": "hero_banner",
                    "config": {
                        "title": "Welcome to Downtown Coworking Hub",
                        "subtitle": "Where innovation meets collaboration "
                        "in the heart of the city",
                        "background_image": "/images/coworking-hero.jpg",
                        "cta_text": "Join Our Community",
                        "cta_link": "/membership",
                    },
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "pricing_cards",
                    "config": {
                        "title": "Membership Plans",
                        "subtitle": ("Choose the perfect plan for your work style"),
                        "plans": [
                            {
                                "name": "Hot Desk",
                                "price": "$99/month",
                                "features": [
                                    "Flexible seating",
                                    "WiFi & Coffee",
                                    "Community events",
                                ],
                                "popular": False,
                            },
                            {
                                "name": "Dedicated Desk",
                                "price": "$199/month",
                                "features": [
                                    "Your own desk",
                                    "Storage locker",
                                    "24/7 access",
                                ],
                                "popular": True,
                            },
                            {
                                "name": "Private Office",
                                "price": "$399/month",
                                "features": [
                                    "Private space",
                                    "Phone booth access",
                                    "Meeting room credits",
                                ],
                                "popular": False,
                            },
                        ],
                    },
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "lead_form",
                    "config": {
                        "title": "Get Started Today",
                        "subtitle": "Join hundreds of entrepreneurs, "
                        "freelancers, and teams",
                        "form_id": None,  # Will be linked to actual form
                    },
                },
            ]
        elif tenant["industry_module"] == "government":
            content_blocks = [
                {
                    "id": str(uuid.uuid4()),
                    "type": "hero_banner",
                    "config": {
                        "title": "City Hall Public Facilities",
                        "subtitle": "Reserve community spaces for meetings, "
                        "events, and public gatherings",
                        "background_image": "/images/government-hero.jpg",
                        "cta_text": "View Available Spaces",
                        "cta_link": "/spaces",
                    },
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "text_block",
                    "config": {
                        "content": "<h2>Community Meeting Spaces</h2>"
                        "<p>Our public facilities are available to community "
                        "organizations, non-profits, and residents for "
                        "meetings and events. All bookings are subject to "
                        "approval and must comply with city guidelines.</p>"
                    },
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "lead_form",
                    "config": {
                        "title": "Request Space Reservation",
                        "subtitle": "Submit your request and we'll process "
                        "it within 48 hours",
                    },
                },
            ]
        else:  # hotel
            content_blocks = [
                {
                    "id": str(uuid.uuid4()),
                    "type": "hero_banner",
                    "config": {
                        "title": "Grand Hotel Executive Spaces",
                        "subtitle": "Premium meeting rooms and event venues "
                        "for discerning professionals",
                        "background_image": "/images/hotel-hero.jpg",
                        "cta_text": "Book Your Event",
                        "cta_link": "/booking",
                    },
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "text_block",
                    "config": {
                        "content": "<h2>Professional Meeting Venues</h2>"
                        "<p>Experience luxury and sophistication in our "
                        "state-of-the-art meeting rooms and event spaces. "
                        "Perfect for corporate meetings, training sessions, "
                        "and special events.</p>"
                    },
                },
            ]

        homepage = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant["id"],
            "title": "Home",
            "slug": "home",
            "content_blocks": content_blocks,
            "meta_title": f"Welcome to {tenant['name']}",
            "meta_description": f"Discover amazing spaces at {tenant['name']}",
            "status": "published",
            "template_id": template["id"] if template else None,
            "is_homepage": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        homepage_obj = Page(**homepage)
        session.add(homepage_obj)
        await session.commit()

        # Create additional pages
        additional_pages = [
            {
                "title": "About Us",
                "slug": "about",
                "content_blocks": [
                    {
                        "id": str(uuid.uuid4()),
                        "type": "text_block",
                        "config": {
                            "content": f"<h1>About {tenant['name']}</h1>"
                            f"<p>We are dedicated to providing exceptional "
                            f"space solutions for our community.</p>"
                        },
                    }
                ],
            },
            {
                "title": "Contact",
                "slug": "contact",
                "content_blocks": [
                    {
                        "id": str(uuid.uuid4()),
                        "type": "lead_form",
                        "config": {
                            "title": "Get in Touch",
                            "subtitle": "We'd love to hear from you",
                        },
                    }
                ],
            },
        ]

        for page_data in additional_pages:
            page = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant["id"],
                "title": page_data["title"],
                "slug": page_data["slug"],
                "content_blocks": page_data["content_blocks"],
                "meta_title": f"{page_data['title']} - {tenant['name']}",
                "meta_description": f"{page_data['title']} page for "
                f"{tenant['name']}",
                "status": "published",
                "template_id": template["id"] if template else None,
                "is_homepage": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            page_obj = Page(**page)
            session.add(page_obj)
            await session.commit()

        print(f"✅ Created {len(additional_pages) + 1} pages for " f"{tenant['name']}")

    # Create forms for each tenant
    for tenant in created_tenants:
        if tenant["industry_module"] == "coworking":
            forms_data = [
                {
                    "name": "membership_inquiry",
                    "title": "Membership Inquiry",
                    "description": (
                        "Interested in joining our coworking community? "
                        "Tell us about your needs."
                    ),
                    "fields": [
                        {
                            "id": str(uuid.uuid4()),
                            "label": "First Name",
                            "type": "text",
                            "is_required": True,
                            "placeholder": "Enter your first name",
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "label": "Last Name",
                            "type": "text",
                            "is_required": True,
                            "placeholder": "Enter your last name",
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "label": "Email",
                            "type": "email",
                            "is_required": True,
                            "placeholder": "your@email.com",
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "label": "Phone",
                            "type": "phone",
                            "is_required": False,
                            "placeholder": "(555) 123-4567",
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "label": "Company",
                            "type": "text",
                            "is_required": False,
                            "placeholder": "Your company name",
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "label": "Membership Interest",
                            "type": "select",
                            "is_required": True,
                            "options": [
                                "Hot Desk",
                                "Dedicated Desk",
                                "Private Office",
                                "Meeting Rooms Only",
                            ],
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "label": "How did you hear about us?",
                            "type": "select",
                            "is_required": False,
                            "options": [
                                "Google Search",
                                "Social Media",
                                "Referral",
                                "Walking by",
                                "Other",
                            ],
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "label": "Additional Notes",
                            "type": "textarea",
                            "is_required": False,
                            "placeholder": (
                                "Tell us about your needs and preferences..."
                            ),
                        },
                    ],
                    "success_message": (
                        "Thank you for your interest! We'll be in touch "
                        "within 24 hours to schedule a tour."
                    ),
                    "email_notifications": ["admin@downtownhub.com"],
                },
                {
                    "name": "tour_request",
                    "title": "Schedule a Tour",
                    "description": ("See our space in person and meet our community."),
                    "fields": [
                        {
                            "id": str(uuid.uuid4()),
                            "label": "Name",
                            "type": "text",
                            "is_required": True,
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "label": "Email",
                            "type": "email",
                            "is_required": True,
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "label": "Preferred Date",
                            "type": "date",
                            "is_required": True,
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "label": "Preferred Time",
                            "type": "select",
                            "is_required": True,
                            "options": [
                                "9:00 AM",
                                "10:00 AM",
                                "11:00 AM",
                                "2:00 PM",
                                "3:00 PM",
                                "4:00 PM",
                            ],
                        },
                    ],
                    "success_message": (
                        "Tour requested! We'll confirm your appointment " "shortly."
                    ),
                },
            ]
        elif tenant["industry_module"] == "government":
            forms_data = [
                {
                    "name": "facility_request",
                    "title": "Facility Reservation Request",
                    "description": (
                        "Request to reserve public meeting spaces and " "facilities."
                    ),
                    "fields": [
                        {
                            "id": str(uuid.uuid4()),
                            "label": "Organization Name",
                            "type": "text",
                            "is_required": True,
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "label": "Contact Person",
                            "type": "text",
                            "is_required": True,
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "label": "Email",
                            "type": "email",
                            "is_required": True,
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "label": "Phone Number",
                            "type": "phone",
                            "is_required": True,
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "label": "Event Type",
                            "type": "select",
                            "is_required": True,
                            "options": [
                                "Community Meeting",
                                "Non-profit Event",
                                "Educational Workshop",
                                "Public Hearing",
                                "Other",
                            ],
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "label": "Requested Date",
                            "type": "date",
                            "is_required": True,
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "label": "Expected Attendance",
                            "type": "number",
                            "is_required": True,
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "label": "Event Description",
                            "type": "textarea",
                            "is_required": True,
                            "placeholder": (
                                "Please provide details about your event..."
                            ),
                        },
                    ],
                    "success_message": (
                        "Your reservation request has been submitted. "
                        "We will review and respond within 48 hours."
                    ),
                }
            ]
        else:  # hotel
            forms_data = [
                {
                    "name": "event_inquiry",
                    "title": "Event Space Inquiry",
                    "description": (
                        "Planning a corporate event or meeting? "
                        "Let us help you create the perfect experience."
                    ),
                    "fields": [
                        {
                            "id": str(uuid.uuid4()),
                            "label": "Company Name",
                            "type": "text",
                            "is_required": True,
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "label": "Contact Name",
                            "type": "text",
                            "is_required": True,
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "label": "Email",
                            "type": "email",
                            "is_required": True,
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "label": "Phone",
                            "type": "phone",
                            "is_required": True,
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "label": "Event Type",
                            "type": "select",
                            "is_required": True,
                            "options": [
                                "Board Meeting",
                                "Training Session",
                                "Conference",
                                "Product Launch",
                                "Corporate Retreat",
                            ],
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "label": "Event Date",
                            "type": "date",
                            "is_required": True,
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "label": "Number of Attendees",
                            "type": "number",
                            "is_required": True,
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "label": "Catering Required",
                            "type": "select",
                            "is_required": False,
                            "options": [
                                "No",
                                "Continental Breakfast",
                                "Lunch",
                                "Full Service",
                                "Custom",
                            ],
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "label": "Special Requirements",
                            "type": "textarea",
                            "is_required": False,
                            "placeholder": (
                                "Any special setup, equipment, or service "
                                "requirements..."
                            ),
                        },
                    ],
                    "success_message": (
                        "Thank you for your inquiry! Our events team will "
                        "contact you within 4 hours to discuss your "
                        "requirements."
                    ),
                }
            ]

        for form_data in forms_data:
            form = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant["id"],
                **form_data,
                "is_active": True,
                "created_at": datetime.utcnow(),
            }
            form_obj = Form(**form)
            session.add(form_obj)
            await session.commit()

        print(f"✅ Created {len(forms_data)} forms for {tenant['name']}")

    # Create sample leads for each tenant
    for tenant in created_tenants:
        leads_count = 15 if tenant["industry_module"] == "coworking" else 8

        for i in range(leads_count):
            days_ago = i * 2
            created_date = datetime.utcnow() - timedelta(days=days_ago)

            if tenant["industry_module"] == "coworking":
                first_names = [
                    "Alex",
                    "Jordan",
                    "Casey",
                    "Morgan",
                    "Taylor",
                    "Sam",
                    "Riley",
                    "Avery",
                ]
                last_names = [
                    "Johnson",
                    "Smith",
                    "Williams",
                    "Brown",
                    "Davis",
                    "Miller",
                    "Wilson",
                    "Moore",
                ]
                companies = [
                    "TechStart Inc",
                    "Design Studio",
                    "Consulting Group",
                    "Marketing Agency",
                    None,
                    "Law Firm",
                    "Architecture Co",
                    None,
                ]
                sources = [
                    "website_form",
                    "google_search",
                    "referral",
                    "social_media",
                    "walk_in",
                ]
            elif tenant["industry_module"] == "government":
                first_names = [
                    "Maria",
                    "John",
                    "Sarah",
                    "David",
                    "Lisa",
                    "Robert",
                    "Jennifer",
                    "Michael",
                ]
                last_names = [
                    "Garcia",
                    "Martinez",
                    "Rodriguez",
                    "Lopez",
                    "Gonzalez",
                    "Perez",
                    "Sanchez",
                    "Ramirez",
                ]
                companies = [
                    "Community Center",
                    "Non-profit Org",
                    "School District",
                    "Residents Assoc",
                    "Youth Group",
                    "Senior Center",
                    "Cultural Org",
                    "Volunteer Group",
                ]
                sources = [
                    "city_website",
                    "community_board",
                    "referral",
                    "public_notice",
                ]
            else:  # hotel
                first_names = [
                    "Executive",
                    "Senior",
                    "Director",
                    "Manager",
                    "Chief",
                    "Vice",
                    "Head",
                    "Lead",
                ]
                last_names = [
                    "Thompson",
                    "Anderson",
                    "Thomas",
                    "Jackson",
                    "White",
                    "Harris",
                    "Martin",
                    "Clark",
                ]
                companies = [
                    "Fortune Corp",
                    "Global Industries",
                    "Enterprise Solutions",
                    "Business Group",
                    "Corporate Partners",
                    "Executive Associates",
                    "Professional Services",
                    "Strategic Consulting",
                ]
                sources = [
                    "corporate_website",
                    "sales_referral",
                    "event_planner",
                    "repeat_client",
                ]

            # Determine status based on age
            if days_ago == 0:
                status = "new_inquiry"
            elif days_ago <= 3:
                status = (
                    "tour_scheduled"
                    if tenant["industry_module"] == "coworking"
                    else "new_inquiry"
                )
            elif days_ago <= 7:
                status = (
                    "tour_completed"
                    if tenant["industry_module"] == "coworking"
                    else "tour_scheduled"
                )
            elif days_ago <= 14:
                status = "converted" if i % 3 == 0 else "tour_completed"
            else:
                status = "converted" if i % 4 == 0 else "closed"

            lead = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant["id"],
                "first_name": first_names[i % len(first_names)],
                "last_name": last_names[i % len(last_names)],
                "email": (
                    f"{first_names[i % len(first_names)].lower()}."
                    f"{last_names[i % len(last_names)].lower()}@email.com"
                ),
                "phone": f"+1-555-{(i*123) % 1000:03d}-{(i*456) % 10000:04d}",
                "company": companies[i % len(companies)],
                "status": status,
                "source": sources[i % len(sources)],
                "notes": (
                    f"Interested in our services. Initial contact made "
                    f"{days_ago} days ago."
                ),
                "custom_fields": {},
                "assigned_to": None,
                "tour_scheduled_at": (
                    created_date + timedelta(days=2)
                    if status in ["tour_scheduled", "tour_completed", "converted"]
                    else None
                ),
                "tour_completed_at": (
                    created_date + timedelta(days=3)
                    if status in ["tour_completed", "converted"]
                    else None
                ),
                "converted_at": (
                    created_date + timedelta(days=5) if status == "converted" else None
                ),
                "created_at": created_date,
                "updated_at": created_date,
            }
            lead_obj = Lead(**lead)
            session.add(lead_obj)
            await session.commit()

        print(f"✅ Created {leads_count} sample leads for {tenant['name']}")

    print("\n🎉 Claude Platform demo data seeded successfully!")
    print("\n" + "=" * 60)
    print("DEMO TENANTS CREATED:")
    print("=" * 60)

    for tenant in created_tenants:
        print(f"\n🏢 {tenant['name']} ({tenant['industry_module'].upper()})")
        print(f"   URL: https://your-domain.com " f"(subdomain: {tenant['subdomain']})")
        print("   Login: admin user credentials above")
        print(
            f"   Features: "
            f"{', '.join([k for k, v in tenant['feature_toggles'].items()
                          if v])}"
        )

        print("\n📊 PLATFORM STATISTICS:")
        print(
            f"   • {len(created_tenants)} tenants across "
            f"{len(set(t['industry_module'] for t in created_tenants))} "
            f"industries"
        )

        from sqlalchemy import func

        user_count = await session.execute(select(func.count(User.id)))
        page_count = await session.execute(select(func.count(Page.id)))
        form_count = await session.execute(select(func.count(Form.id)))
        lead_count = await session.execute(select(func.count(Lead.id)))

        print(f"   • {user_count.scalar()} total users")
        print(f"   • {page_count.scalar()} website pages")
        print(f"   • {form_count.scalar()} lead capture forms")
        print(f"   • {lead_count.scalar()} leads generated")
        print(f"   • {len(templates)} industry-specific templates")

    print("\n🔑 LOGIN CREDENTIALS:")
    print("   All admin accounts: password123")
    print("   Staff accounts: password123")

    print("\n🚀 Your multi-tenant Space-as-a-Service platform is ready!")


async def main():
    await seed_claude_platform()


if __name__ == "__main__":
    asyncio.run(main())
