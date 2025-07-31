"""
Content & CMS Kernel
Universal content management and website building engine
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from kernels.base_kernel import BaseKernel
from backend.models.postgresql_models import Page, Template, Widget, User
from sqlalchemy import select, update, delete


class CMSKernel(BaseKernel):
    """Universal content management system"""
    
    async def _initialize_kernel(self):
        """Initialize CMS kernel"""
        pass
    
    async def validate_tenant_access(self, tenant_id: str, user_id: str) -> bool:
        """Validate user belongs to tenant"""
        async with self.connection_manager.get_session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id, User.tenant_id == tenant_id)
            )
            user = result.scalar_one_or_none()
            return user is not None
    
    # Page Management
    async def create_page(self, tenant_id: str, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new page"""
        async with self.connection_manager.get_session() as session:
            # Check slug uniqueness
            result = await session.execute(
                select(Page).where(
                    Page.tenant_id == tenant_id,
                    Page.slug == page_data["slug"]
                )
            )
            existing_page = result.scalar_one_or_none()
            if existing_page:
                raise ValueError(f"Page with slug '{page_data['slug']}' already exists")
            
            # Handle homepage setting
            if page_data.get("is_homepage"):
                await session.execute(
                    update(Page).where(
                        Page.tenant_id == tenant_id,
                        Page.is_homepage == True
                    ).values(is_homepage=False)
                )
            
            page_data.update({
                "tenant_id": tenant_id,
                "status": page_data.get("status", "draft"),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
            
            page_obj = Page(**page_data)
            session.add(page_obj)
            await session.commit()
            return page_data
    
    async def get_pages(self, tenant_id: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get pages for tenant"""
        async with self.connection_manager.get_session() as session:
            query_conditions = [Page.tenant_id == tenant_id]
            
            if filters:
                for key, value in filters.items():
                    if hasattr(Page, key):
                        query_conditions.append(getattr(Page, key) == value)
            
            result = await session.execute(
                select(Page).where(*query_conditions).order_by(Page.created_at.desc())
            )
            pages = result.scalars().all()
            return [page.__dict__ for page in pages]
    
    async def get_page_by_slug(self, tenant_id: str, slug: str) -> Optional[Dict[str, Any]]:
        """Get page by slug"""
        async with self.connection_manager.get_session() as session:
            result = await session.execute(
                select(Page).where(Page.tenant_id == tenant_id, Page.slug == slug)
            )
            page = result.scalar_one_or_none()
            return page.__dict__ if page else None
    
    async def update_page(self, page_id: str, tenant_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update page"""
        async with self.connection_manager.get_session() as session:
            update_data["updated_at"] = datetime.utcnow()
            
            result = await session.execute(
                update(Page).where(
                    Page.id == page_id, 
                    Page.tenant_id == tenant_id
                ).values(**update_data)
            )
            
            if result.rowcount == 0:
                raise ValueError("Page not found or not updated")
            
            await session.commit()
            
            result = await session.execute(select(Page).where(Page.id == page_id))
            page = result.scalar_one_or_none()
            return page.__dict__ if page else None
    
    async def delete_page(self, page_id: str, tenant_id: str) -> bool:
        """Delete page"""
        async with self.connection_manager.get_session() as session:
            # Check if it's homepage
            result = await session.execute(
                select(Page).where(Page.id == page_id, Page.tenant_id == tenant_id)
            )
            page = result.scalar_one_or_none()
            if not page:
                return False
            
            if page.is_homepage:
                raise ValueError("Cannot delete homepage")
            
            result = await session.execute(
                delete(Page).where(Page.id == page_id, Page.tenant_id == tenant_id)
            )
            await session.commit()
            return result.rowcount > 0
    
    # Template Management
    async def get_templates(self, industry_module: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get templates, optionally filtered by industry"""
        query = {"is_active": True}
        if industry_module:
            query["$or"] = [
                {"industry_module": industry_module},
                {"industry_module": None}  # Universal templates
            ]
        
        templates = await self.db.templates.find(query).to_list(1000)
        return templates
    
    async def create_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new template"""
        template_doc = {
            **template_data,
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        await self.db.templates.insert_one(template_doc)
        return template_doc
    
    # Widget Management
    async def create_widget(self, tenant_id: str, widget_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new widget"""
        widget_doc = {
            **widget_data,
            "tenant_id": tenant_id,
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        await self.db.widgets.insert_one(widget_doc)
        return widget_doc
    
    async def get_widgets(self, tenant_id: str, widget_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get widgets for tenant"""
        query = {"tenant_id": tenant_id, "is_active": True}
        if widget_type:
            query["type"] = widget_type
        
        widgets = await self.db.widgets.find(query).to_list(1000)
        return widgets
    
    # Media Library
    async def upload_media(self, tenant_id: str, media_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add media to library"""
        media_doc = {
            **media_data,
            "tenant_id": tenant_id,
            "uploaded_at": datetime.utcnow()
        }
        await self.db.media_library.insert_one(media_doc)
        return media_doc
    
    async def get_media_library(self, tenant_id: str, file_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get media library items"""
        query = {"tenant_id": tenant_id}
        if file_type:
            query["file_type"] = file_type
        
        media = await self.db.media_library.find(query).sort("uploaded_at", -1).to_list(1000)
        return media
    
    # Public API
    async def get_published_page(self, tenant_id: str, slug: str) -> Optional[Dict[str, Any]]:
        """Get published page for public viewing"""
        return await self.db.pages.find_one({
            "tenant_id": tenant_id,
            "slug": slug,
            "status": "published"
        })
    
    async def get_homepage(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get homepage for tenant"""
        return await self.db.pages.find_one({
            "tenant_id": tenant_id,
            "is_homepage": True,
            "status": "published"
        })
