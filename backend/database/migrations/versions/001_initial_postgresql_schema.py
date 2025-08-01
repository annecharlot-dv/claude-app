"""Initial PostgreSQL schema with RLS

Revision ID: 001
Revises:
Create Date: 2025-01-31 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tenants table
    op.create_table(
        "tenants",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("subdomain", sa.String(length=50), nullable=False),
        sa.Column("custom_domain", sa.String(length=255), nullable=True),
        sa.Column("industry_module", sa.String(length=50), nullable=False),
        sa.Column("plan", sa.String(length=20), nullable=True, default="starter"),
        sa.Column("is_active", sa.Boolean(), nullable=True, default=True),
        sa.Column(
            "branding",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "settings",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "feature_toggles",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_tenants_subdomain", "tenants", ["subdomain"], unique=True)
    op.create_index(
        "idx_tenants_industry_active",
        "tenants",
        ["industry_module", "is_active"],
    )
    op.create_index(
        "idx_tenants_branding_gin",
        "tenants",
        ["branding"],
        postgresql_using="gin",
    )
    op.create_index(
        "idx_tenants_settings_gin",
        "tenants",
        ["settings"],
        postgresql_using="gin",
    )

    # Create users table
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True, default=True),
        sa.Column("company_id", sa.String(length=100), nullable=True),
        sa.Column(
            "profile",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", "tenant_id", name="unique_email_per_tenant"),
    )
    op.create_index("idx_users_tenant_email", "users", ["tenant_id", "email"])
    op.create_index("idx_users_role_active", "users", ["role", "is_active"])
    op.create_index(
        "idx_users_profile_gin", "users", ["profile"], postgresql_using="gin"
    )

    # Create user_passwords table
    op.create_table(
        "user_passwords",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    # Create pages table
    op.create_table(
        "pages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("meta_title", sa.String(length=255), nullable=True),
        sa.Column("meta_description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True, default="draft"),
        sa.Column("template_id", sa.String(length=100), nullable=True),
        sa.Column("is_homepage", sa.Boolean(), nullable=True, default=False),
        sa.Column(
            "content_blocks",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("search_keywords", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", "tenant_id", name="unique_slug_per_tenant"),
    )
    op.create_index("idx_pages_tenant_status", "pages", ["tenant_id", "status"])
    op.create_index(
        "idx_pages_content_gin",
        "pages",
        ["content_blocks"],
        postgresql_using="gin",
    )

    # Create leads table
    op.create_table(
        "leads",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("company", sa.String(length=255), nullable=True),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=True,
            default="new_inquiry",
        ),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("assigned_to", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "custom_fields",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("tour_scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tour_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("converted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["assigned_to"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_leads_tenant_email", "leads", ["tenant_id", "email"])
    op.create_index("idx_leads_status_created", "leads", ["status", "created_at"])
    op.create_index(
        "idx_leads_custom_fields_gin",
        "leads",
        ["custom_fields"],
        postgresql_using="gin",
    )

    # Create forms table
    op.create_table(
        "forms",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "success_message",
            sa.Text(),
            nullable=True,
            default="Thank you for your submission!",
        ),
        sa.Column("redirect_url", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True, default=True),
        sa.Column(
            "fields",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "email_notifications",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "tenant_id", name="unique_form_name_per_tenant"),
    )
    op.create_index("idx_forms_tenant_active", "forms", ["tenant_id", "is_active"])
    op.create_index("idx_forms_fields_gin", "forms", ["fields"], postgresql_using="gin")

    # Create form_submissions table
    op.create_table(
        "form_submissions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("form_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["form_id"],
            ["forms.id"],
        ),
        sa.ForeignKeyConstraint(
            ["lead_id"],
            ["leads.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_form_submissions_form_created",
        "form_submissions",
        ["form_id", "created_at"],
    )
    op.create_index(
        "idx_form_submissions_data_gin",
        "form_submissions",
        ["data"],
        postgresql_using="gin",
    )

    # Create templates table
    op.create_table(
        "templates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("industry_module", sa.String(length=50), nullable=False),
        sa.Column("preview_image", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True, default=True),
        sa.Column(
            "layout_config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "default_content",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_templates_industry_active",
        "templates",
        ["industry_module", "is_active"],
    )
    op.create_index(
        "idx_templates_layout_gin",
        "templates",
        ["layout_config"],
        postgresql_using="gin",
    )

    # Create widgets table
    op.create_table(
        "widgets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True, default=True),
        sa.Column(
            "config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_widgets_tenant_type", "widgets", ["tenant_id", "type"])
    op.create_index(
        "idx_widgets_config_gin", "widgets", ["config"], postgresql_using="gin"
    )

    # Create tour_slots table
    op.create_table(
        "tour_slots",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("staff_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=True, default=30),
        sa.Column("max_bookings", sa.Integer(), nullable=True, default=1),
        sa.Column("current_bookings", sa.Integer(), nullable=True, default=0),
        sa.Column("is_available", sa.Boolean(), nullable=True, default=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["staff_user_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_tour_slots_tenant_date", "tour_slots", ["tenant_id", "date"])
    op.create_index(
        "idx_tour_slots_staff_available",
        "tour_slots",
        ["staff_user_id", "is_available"],
    )

    # Create tours table
    op.create_table(
        "tours",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tour_slot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("staff_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=True, default="scheduled"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["lead_id"],
            ["leads.id"],
        ),
        sa.ForeignKeyConstraint(
            ["staff_user_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tour_slot_id"],
            ["tour_slots.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_tours_tenant_scheduled", "tours", ["tenant_id", "scheduled_at"]
    )
    op.create_index("idx_tours_status_created", "tours", ["status", "created_at"])

    # Add full-text search support for pages
    op.execute("ALTER TABLE pages ADD COLUMN search_vector tsvector")
    op.create_index(
        "idx_pages_search_gin",
        "pages",
        ["search_vector"],
        postgresql_using="gin",
    )

    # Create search vector update function
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_page_search_vector()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.search_vector := to_tsvector('english',
                COALESCE(NEW.title, '') || ' ' ||
                COALESCE(NEW.meta_description, '') || ' ' ||
                COALESCE(NEW.search_keywords, '')
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    # Create trigger for automatic search vector updates
    op.execute(
        """
        CREATE TRIGGER update_pages_search_vector
            BEFORE INSERT OR UPDATE ON pages
            FOR EACH ROW EXECUTE FUNCTION update_page_search_vector();
    """
    )

    # Enable Row-Level Security on all tenant-specific tables
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE pages ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE leads ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE forms ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE widgets ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tour_slots ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tours ENABLE ROW LEVEL SECURITY")

    # Create RLS policies for tenant isolation
    op.execute(
        """
        CREATE POLICY tenant_isolation_users ON users
            FOR ALL TO application_role
            USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
    """
    )

    op.execute(
        """
        CREATE POLICY tenant_isolation_pages ON pages
            FOR ALL TO application_role
            USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
    """
    )

    op.execute(
        """
        CREATE POLICY tenant_isolation_leads ON leads
            FOR ALL TO application_role
            USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
    """
    )

    op.execute(
        """
        CREATE POLICY tenant_isolation_forms ON forms
            FOR ALL TO application_role
            USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
    """
    )

    op.execute(
        """
        CREATE POLICY tenant_isolation_widgets ON widgets
            FOR ALL TO application_role
            USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
    """
    )

    op.execute(
        """
        CREATE POLICY tenant_isolation_tour_slots ON tour_slots
            FOR ALL TO application_role
            USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
    """
    )

    op.execute(
        """
        CREATE POLICY tenant_isolation_tours ON tours
            FOR ALL TO application_role
            USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
    """
    )

    # Create application role for RLS
    op.execute("CREATE ROLE application_role")
    op.execute("GRANT USAGE ON SCHEMA public TO application_role")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public "
        "TO application_role"
    )
    op.execute(
        "GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public " "TO application_role"
    )


def downgrade() -> None:
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS tenant_isolation_users ON users")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_pages ON pages")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_leads ON leads")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_forms ON forms")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_widgets ON widgets")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_tour_slots " "ON tour_slots")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_tours ON tours")

    # Drop application role
    op.execute("DROP ROLE IF EXISTS application_role")

    # Drop search function and trigger
    op.execute("DROP TRIGGER IF EXISTS update_pages_search_vector ON pages")
    op.execute("DROP FUNCTION IF EXISTS update_page_search_vector()")

    # Drop tables in reverse order
    op.drop_table("tours")
    op.drop_table("tour_slots")
    op.drop_table("widgets")
    op.drop_table("templates")
    op.drop_table("form_submissions")
    op.drop_table("forms")
    op.drop_table("leads")
    op.drop_table("pages")
    op.drop_table("user_passwords")
    op.drop_table("users")
    op.drop_table("tenants")
