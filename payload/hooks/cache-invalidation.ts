import { CollectionAfterChangeHook, CollectionAfterDeleteHook } from 'payload/types';

/**
 * Cache Invalidation Hooks
 * Automatically invalidate cache when content changes
 */

// Cache invalidation patterns for different collections
const CACHE_PATTERNS = {
  pages: ['pages', 'navigation', 'sitemap'],
  users: ['users', 'auth'],
  leads: ['leads', 'analytics'],
  forms: ['forms', 'submissions'],
  tenants: ['tenants', 'config'],
};

// Generic cache invalidation function
const invalidateCache = async (
  collection: string,
  tenantId: string,
  operation: 'create' | 'update' | 'delete',
  doc?: any
) => {
  const patterns = (CACHE_PATTERNS as any)[collection] || [collection];
  
  try {
    // Call your cache invalidation API
    await fetch('/api/cache/invalidate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Internal-API': 'true',
      },
      body: JSON.stringify({
        patterns,
        tenantId,
        operation,
        collection,
        documentId: doc?.id,
      }),
    });
  } catch (error) {
    console.error('Cache invalidation failed:', error);
    // Don't throw - cache invalidation shouldn't break the operation
  }
};

// Hook for after document changes
export const invalidateCacheAfterChange: CollectionAfterChangeHook = async ({
  doc,
  req,
  operation,
  collection,
}) => {
  const tenantId = doc.tenantId || req.user?.tenantId;
  
  if (tenantId) {
    await invalidateCache(collection.slug, tenantId, operation, doc);
  }
};

// Hook for after document deletion
export const invalidateCacheAfterDelete: CollectionAfterDeleteHook = async ({
  doc,
  req,
  collection,
}) => {
  const tenantId = doc.tenantId || req.user?.tenantId;
  
  if (tenantId) {
    await invalidateCache(collection.slug, tenantId, 'delete', doc);
  }
};

// Specific cache invalidation for pages
export const invalidatePageCache: CollectionAfterChangeHook = async ({
  doc,
  req,
  operation,
}) => {
  const tenantId = doc.tenantId;
  
  if (!tenantId) return;

  // Invalidate specific page patterns
  const patterns = [
    `pages:${tenantId}`,
    `page:${tenantId}:${doc.slug}`,
    `navigation:${tenantId}`,
  ];

  // If homepage changed, invalidate homepage cache
  if (doc.isHomepage) {
    patterns.push(`homepage:${tenantId}`);
  }

  // If page status changed to published, invalidate sitemap
  if (doc.status === 'published') {
    patterns.push(`sitemap:${tenantId}`);
  }

  try {
    await fetch('/api/cache/invalidate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Internal-API': 'true',
      },
      body: JSON.stringify({
        patterns,
        tenantId,
        operation,
        collection: 'pages',
        documentId: doc.id,
      }),
    });
  } catch (error) {
    console.error('Page cache invalidation failed:', error);
  }
};

// Lead cache invalidation with analytics impact
export const invalidateLeadCache: CollectionAfterChangeHook = async ({
  doc,
  req,
  operation,
}) => {
  const tenantId = doc.tenantId;
  
  if (!tenantId) return;

  const patterns = [
    `leads:${tenantId}`,
    `lead:${tenantId}:${doc.id}`,
    `analytics:${tenantId}:leads`,
  ];

  // If lead status changed, invalidate conversion funnel cache
  if (doc.status) {
    patterns.push(`funnel:${tenantId}`);
  }

  try {
    await fetch('/api/cache/invalidate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Internal-API': 'true',
      },
      body: JSON.stringify({
        patterns,
        tenantId,
        operation,
        collection: 'leads',
        documentId: doc.id,
      }),
    });
  } catch (error) {
    console.error('Lead cache invalidation failed:', error);
  }
};
