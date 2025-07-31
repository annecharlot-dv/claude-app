import { CollectionBeforeChangeHook, CollectionAfterChangeHook } from 'payload/types';

/**
 * Performance Tracking Hooks
 * Monitor and optimize Payload CMS operations
 */

// Performance metrics tracking
const trackOperation = async (
  operation: string,
  collection: string,
  duration: number,
  tenantId?: string,
  metadata?: any
) => {
  try {
    await fetch('/api/performance/metrics', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Internal-API': 'true',
      },
      body: JSON.stringify({
        metric_type: `payload_${operation}`,
        value: duration,
        metadata: {
          collection,
          ...metadata,
        },
        tenant_id: tenantId,
      }),
    });
  } catch (error) {
    console.error('Performance tracking failed:', error);
  }
};

// Hook to track operation start time
export const trackOperationStart: CollectionBeforeChangeHook = async ({
  req,
  operation,
  collection,
}) => {
  // Store start time in request context
  if (!req.payloadPerformance) {
    req.payloadPerformance = {};
  }
  
  req.payloadPerformance.startTime = Date.now();
  req.payloadPerformance.operation = operation;
  req.payloadPerformance.collection = collection.slug;
  
  return;
};

// Hook to track operation completion
export const trackOperationEnd: CollectionAfterChangeHook = async ({
  req,
  doc,
  operation,
  collection,
}) => {
  if (!req.payloadPerformance?.startTime) return;
  
  const duration = Date.now() - req.payloadPerformance.startTime;
  const tenantId = doc.tenantId || req.user?.tenantId;
  
  await trackOperation(
    operation,
    collection.slug,
    duration,
    tenantId,
    {
      documentId: doc.id,
      userId: req.user?.id,
    }
  );
  
  // Log slow operations
  if (duration > 1000) { // 1 second threshold
    console.warn(`Slow Payload operation: ${operation} on ${collection.slug} took ${duration}ms`);
  }
};

// Hook to track query performance
export const trackQueryPerformance = async (
  req: any,
  collection: string,
  query: any,
  startTime: number
) => {
  const duration = Date.now() - startTime;
  const tenantId = req.user?.tenantId;
  
  await trackOperation(
    'query',
    collection,
    duration,
    tenantId,
    {
      queryType: 'find',
      hasWhere: !!query.where,
      hasSort: !!query.sort,
      limit: query.limit,
    }
  );
  
  // Log slow queries
  if (duration > 500) { // 500ms threshold for queries
    console.warn(`Slow Payload query on ${collection} took ${duration}ms`, {
      query: JSON.stringify(query, null, 2),
    });
  }
};

// Middleware to track all database operations
export const performanceMiddleware = (req: any, res: any, next: any) => {
  const originalFind = req.payload.find;
  const originalFindByID = req.payload.findByID;
  const originalCreate = req.payload.create;
  const originalUpdate = req.payload.update;
  const originalDelete = req.payload.delete;
  
  // Wrap find operations
  req.payload.find = async (args: any) => {
    const startTime = Date.now();
    const result = await originalFind.call(req.payload, args);
    
    await trackQueryPerformance(req, args.collection, args, startTime);
    return result;
  };
  
  // Wrap findByID operations
  req.payload.findByID = async (args: any) => {
    const startTime = Date.now();
    const result = await originalFindByID.call(req.payload, args);
    
    await trackOperation(
      'findByID',
      args.collection,
      Date.now() - startTime,
      req.user?.tenantId,
      { documentId: args.id }
    );
    
    return result;
  };
  
  // Wrap create operations
  req.payload.create = async (args: any) => {
    const startTime = Date.now();
    const result = await originalCreate.call(req.payload, args);
    
    await trackOperation(
      'create',
      args.collection,
      Date.now() - startTime,
      result.tenantId || req.user?.tenantId,
      { documentId: result.id }
    );
    
    return result;
  };
  
  // Wrap update operations
  req.payload.update = async (args: any) => {
    const startTime = Date.now();
    const result = await originalUpdate.call(req.payload, args);
    
    await trackOperation(
      'update',
      args.collection,
      Date.now() - startTime,
      req.user?.tenantId,
      { documentId: args.id }
    );
    
    return result;
  };
  
  // Wrap delete operations
  req.payload.delete = async (args: any) => {
    const startTime = Date.now();
    const result = await originalDelete.call(req.payload, args);
    
    await trackOperation(
      'delete',
      args.collection,
      Date.now() - startTime,
      req.user?.tenantId,
      { documentId: args.id }
    );
    
    return result;
  };
  
  next();
};

// Hook to optimize queries based on tenant context
export const optimizeQueryForTenant: CollectionBeforeChangeHook = async ({
  req,
  collection,
}) => {
  // Add database hints for tenant-specific queries
  if (req.user?.tenantId && collection.slug !== 'tenants') {
    // This would add database-specific optimizations
    // For PostgreSQL, we might add index hints or query planning
    req.payloadQueryHints = {
      useIndex: `idx_${collection.slug}_tenant_id`,
      tenantId: req.user.tenantId,
    };
  }
  
  return;
};

// Export performance configuration
export const PERFORMANCE_CONFIG = {
  slowOperationThreshold: 1000, // 1 second
  slowQueryThreshold: 500,      // 500ms
  enableDetailedLogging: process.env.NODE_ENV === 'development',
  trackAllOperations: true,
};