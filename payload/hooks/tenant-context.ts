import { FieldHook, CollectionBeforeChangeHook, CollectionBeforeReadHook } from 'payload/types';

/**
 * Tenant Context Hook
 * Automatically injects tenant context and ensures tenant isolation
 */

// Hook to automatically set tenant_id on document creation/update
export const setTenantContext: CollectionBeforeChangeHook = async ({
  data,
  req,
  operation,
}) => {
  // Skip for platform admin operations
  if (req.user?.role === 'platform_admin') {
    return data;
  }

  // Set tenant_id from authenticated user
  if (req.user?.tenantId && operation === 'create') {
    data.tenantId = req.user.tenantId;
  }

  // Prevent tenant_id modification for non-platform admins
  if (operation === 'update' && req.user?.role !== 'platform_admin') {
    delete data.tenantId;
  }

  return data;
};

// Hook to filter queries by tenant
export const filterByTenant: CollectionBeforeReadHook = async ({
  req,
  query,
}) => {
  // Skip filtering for platform admins
  if (req.user?.role === 'platform_admin') {
    return query;
  }

  // Add tenant filter for all other users
  if (req.user?.tenantId) {
    query.where = {
      ...query.where,
      tenantId: {
        equals: req.user.tenantId,
      },
    };
  }

  return query;
};

// Field hook for tenant validation
export const validateTenantAccess: FieldHook = async ({
  value,
  req,
  operation,
}) => {
  // Allow platform admins to set any tenant
  if (req.user?.role === 'platform_admin') {
    return value;
  }

  // For other users, ensure they can only access their tenant
  if (value && value !== req.user?.tenantId) {
    throw new Error('Access denied: Cannot access resources from other tenants');
  }

  return value || req.user?.tenantId;
};

// Utility function to get tenant from subdomain
export const getTenantFromSubdomain = (req: any): string | null => {
  const host = req.headers?.host || req.headers?.['x-forwarded-host'];
  if (!host) return null;

  const subdomain = host.split('.')[0];
  
  // Skip common subdomains
  if (['www', 'api', 'admin', 'app'].includes(subdomain)) {
    return null;
  }

  return subdomain;
};

// Hook to set tenant context from subdomain
export const setTenantFromSubdomain: CollectionBeforeChangeHook = async ({
  data,
  req,
  operation,
}) => {
  if (operation === 'create' && !data.tenantId) {
    const subdomain = getTenantFromSubdomain(req);
    if (subdomain) {
      // Look up tenant by subdomain
      const tenant = await req.payload.find({
        collection: 'tenants',
        where: {
          subdomain: {
            equals: subdomain,
          },
        },
        limit: 1,
      });

      if (tenant.docs.length > 0) {
        data.tenantId = tenant.docs[0].id;
      }
    }
  }

  return data;
};