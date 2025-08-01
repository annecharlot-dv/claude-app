"""
Universal Kernels for Claude Platform
These kernels provide industry-agnostic core functionality
"""

from kernels.booking_kernel import BookingKernel
from kernels.cms_kernel import CMSKernel
from kernels.communication_kernel import CommunicationKernel
from kernels.financial_kernel import FinancialKernel
from kernels.identity_kernel import IdentityKernel

__all__ = [
    "IdentityKernel",
    "BookingKernel",
    "FinancialKernel",
    "CMSKernel",
    "CommunicationKernel",
]
