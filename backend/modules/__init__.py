"""
Industry-specific modules for Claude Platform
These modules orchestrate kernel functionality for specific industries
"""
from modules.base_module import BaseModule
from modules.coworking_module import CoworkingModule
from modules.government_module import GovernmentModule
from modules.hotel_module import HotelModule
from modules.university_module import UniversityModule
from modules.creative_studio_module import CreativeStudioModule
from modules.residential_module import ResidentialModule

__all__ = [
    'BaseModule',
    'CoworkingModule',
    'GovernmentModule',
    'HotelModule',
    'UniversityModule',
    'CreativeStudioModule',
    'ResidentialModule'
]