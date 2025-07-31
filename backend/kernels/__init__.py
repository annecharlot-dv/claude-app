"""
Universal Kernels for Claude Platform
These kernels provide industry-agnostic core functionality
"""

from kernels.identity_kernel import IdentityKernel
from kernels.booking_kernel import BookingKernel
from kernels.financial_kernel import FinancialKernel
from kernels.cms_kernel import CMSKernel
from kernels.communication_kernel import CommunicationKernel

__all__ = [
    "IdentityKernel",
    "BookingKernel",
    "FinancialKernel",
    "CMSKernel",
    "CommunicationKernel",
]
