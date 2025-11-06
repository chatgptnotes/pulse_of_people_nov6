"""
Custom database managers for tenant-scoped queries
"""

from .tenant_manager import TenantManager, TenantQuerySet

__all__ = ['TenantManager', 'TenantQuerySet']
