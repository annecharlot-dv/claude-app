/**
 * PostgreSQL Integration Layer for Payload CMS
 * Bridges Payload CMS with the existing PostgreSQL performance optimizations
 */

import { PostgreSQLAdapter } from '../../backend/postgresql_adapter';
import { get_cache_manager } from '../../backend/performance/cache_manager';
import { get_performance_monitor } from '../../backend/performance/monitor';

class PayloadPostgreSQLIntegration {
  private pgAdapter: PostgreSQLAdapter;
  private cacheManager: any;
  private performanceMonitor: any;

  constructor() {
    this.pgAdapter = new PostgreSQLAdapter();
  }

  async initialize() {
    await this.pgAdapter.initialize();
    this.cacheManager = await get_cache_manager();
    this.performanceMonitor = await get_performance_monitor();
  }

  // Payload hook integration for PostgreSQL operations
  async beforeChange(args: any) {
    const { data, req, operation, collection } = args;
    
    // Set tenant context for PostgreSQL operations
    if (req.user?.tenantId) {
      await this.pgAdapter.set_tenant_context(req.user.tenantId);
    }

    // Track operation start time
    req.pgOperationStart = Date.now();

    return data;
  }

  async afterChange(args: any) {
    const { doc, req, operation, collection } = args;
    
    // Record performance metrics
    if (req.pgOperationStart) {
      const duration = Date.now() - req.pgOperationStart;
      await this.performanceMonitor.record_metric(
        `payload_${operation}`,
        duration,
        {
          collection: collection.slug,
          documentId: doc.id,
        },
        doc.tenantId
      );
    }

    // Invalidate cache
    if (doc.tenantId) {
      await this.cacheManager.invalidate(
        `${collection.slug}:${doc.tenantId}`,
        [`tenant:${doc.tenantId}`, collection.slug]
      );
    }

    return doc;
  }

  // Custom database operations that leverage PostgreSQL optimizations
  async optimizedFind(collection: string, query: any, options: any = {}) {
    const startTime = Date.now();
    
    try {
      // Use PostgreSQL adapter's optimized query method
      const results = await this.pgAdapter.query_builder.find_many(
        collection,
        query,
        options.tenantId,
        options.limit || 25,
        options.skip || 0,
        options.orderBy
      );

      // Record performance
      const duration = Date.now() - startTime;
      await this.performanceMonitor.record_metric(
        'payload_optimized_find',
        duration,
        { collection, queryComplexity: Object.keys(query).length },
        options.tenantId
      );

      return results;
    } catch (error) {
      const duration = Date.now() - startTime;
      await this.performanceMonitor.record_metric(
        'payload_query_error',
        duration,
        { collection, error: error.message },
        options.tenantId
      );
      throw error;
    }
  }

  // Cached query method
  async cachedFind(collection: string, query: any, options: any = {}) {
    const cacheKey = `payload:${collection}:${JSON.stringify(query)}:${options.tenantId}`;
    
    // Try cache first
    const cached = await this.cacheManager.get(cacheKey);
    if (cached) {
      await this.performanceMonitor.record_metric(
        'payload_cache_hit',
        0,
        { collection },
        options.tenantId
      );
      return cached;
    }

    // Fetch from database
    const results = await this.optimizedFind(collection, query, options);
    
    // Cache results
    const ttl = this.getCacheTTL(collection);
    await this.cacheManager.set(
      cacheKey,
      results,
      ttl,
      [`tenant:${options.tenantId}`, collection]
    );

    return results;
  }

  private getCacheTTL(collection: string): number {
    const ttlMap = {
      pages: 1800,      // 30 minutes
      users: 900,       // 15 minutes
      leads: 300,       // 5 minutes
      forms: 1800,      // 30 minutes
      tenants: 3600,    // 1 hour
    };

    return ttlMap[collection] || 600; // Default 10 minutes
  }

  // Bulk operations with performance optimization
  async bulkCreate(collection: string, documents: any[], tenantId: string) {
    const startTime = Date.now();
    
    try {
      // Use PostgreSQL's bulk insert capabilities
      const results = [];
      
      // Process in batches for better performance
      const batchSize = 100;
      for (let i = 0; i < documents.length; i += batchSize) {
        const batch = documents.slice(i, i + batchSize);
        
        // Add tenant_id to all documents
        const tenantBatch = batch.map(doc => ({
          ...doc,
          tenant_id: tenantId,
          created_at: new Date(),
          updated_at: new Date(),
        }));

        // Execute batch insert
        const batchResults = await this.pgAdapter.conn_manager.execute_transaction([
          ...tenantBatch.map(doc => [
            `INSERT INTO ${collection} (${Object.keys(doc).join(', ')}) VALUES (${Object.keys(doc).map((_, idx) => `$${idx + 1}`).join(', ')}) RETURNING *`,
            Object.values(doc)
          ])
        ], 'main', tenantId);

        results.push(...batchResults.flat());
      }

      // Record performance
      const duration = Date.now() - startTime;
      await this.performanceMonitor.record_metric(
        'payload_bulk_create',
        duration,
        { collection, count: documents.length },
        tenantId
      );

      // Invalidate cache
      await this.cacheManager.invalidate(
        `${collection}:${tenantId}`,
        [`tenant:${tenantId}`, collection]
      );

      return results;
    } catch (error) {
      const duration = Date.now() - startTime;
      await this.performanceMonitor.record_metric(
        'payload_bulk_error',
        duration,
        { collection, error: error.message },
        tenantId
      );
      throw error;
    }
  }

  // Analytics queries with materialized view support
  async getAnalytics(tenantId: string, type: string, timeRange: number = 24) {
    const cacheKey = `analytics:${tenantId}:${type}:${timeRange}`;
    
    // Check cache first
    const cached = await this.cacheManager.get(cacheKey);
    if (cached) {
      return cached;
    }

    let results;
    
    switch (type) {
      case 'performance':
        results = await this.pgAdapter.get_performance_metrics(tenantId, timeRange);
        break;
      case 'leads':
        results = await this.getLeadAnalytics(tenantId, timeRange);
        break;
      case 'pages':
        results = await this.getPageAnalytics(tenantId, timeRange);
        break;
      default:
        throw new Error(`Unknown analytics type: ${type}`);
    }

    // Cache for 15 minutes
    await this.cacheManager.set(cacheKey, results, 900, [`tenant:${tenantId}`, 'analytics']);
    
    return results;
  }

  private async getLeadAnalytics(tenantId: string, hours: number) {
    // Use materialized view for better performance
    const query = `
      SELECT 
        date,
        total_leads,
        engaged_leads,
        tours_scheduled,
        tours_completed,
        converted_leads,
        engagement_rate,
        tour_scheduling_rate,
        conversion_rate,
        source_breakdown
      FROM lead_conversion_funnel
      WHERE tenant_id = $1 
      AND date > NOW() - INTERVAL '${hours} hours'
      ORDER BY date DESC
    `;

    return await this.pgAdapter.conn_manager.execute_query(
      query,
      tenantId,
      'analytics',
      tenantId
    );
  }

  private async getPageAnalytics(tenantId: string, hours: number) {
    const query = `
      SELECT 
        COUNT(*) as total_pages,
        COUNT(CASE WHEN status = 'published' THEN 1 END) as published_pages,
        COUNT(CASE WHEN updated_at > NOW() - INTERVAL '${hours} hours' THEN 1 END) as recently_updated,
        AVG(CASE WHEN search_keywords IS NOT NULL THEN LENGTH(search_keywords) END) as avg_content_length
      FROM pages
      WHERE tenant_id = $1
    `;

    const results = await this.pgAdapter.conn_manager.execute_query(
      query,
      tenantId,
      'analytics',
      tenantId
    );

    return results[0] || {};
  }

  // Health check integration
  async healthCheck() {
    return await this.pgAdapter.health_check();
  }

  // Performance metrics for Payload operations
  async getPayloadMetrics(tenantId?: string) {
    return await this.pgAdapter.get_performance_metrics(tenantId);
  }
}

// Export singleton instance
export const payloadPgIntegration = new PayloadPostgreSQLIntegration();

// Payload plugin to integrate PostgreSQL optimizations
export const postgresqlOptimizationPlugin = () => ({
  name: 'postgresql-optimization',
  
  // Initialize the integration
  init: async (payload: any) => {
    await payloadPgIntegration.initialize();
    
    // Add custom endpoints
    payload.router.get('/api/analytics/:type', async (req: any, res: any) => {
      try {
        const { type } = req.params;
        const { timeRange = 24 } = req.query;
        const tenantId = req.user?.tenantId;
        
        if (!tenantId) {
          return res.status(400).json({ error: 'Tenant ID required' });
        }

        const analytics = await payloadPgIntegration.getAnalytics(tenantId, type, parseInt(timeRange));
        res.json(analytics);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    payload.router.get('/api/health/postgresql', async (req: any, res: any) => {
      try {
        const health = await payloadPgIntegration.healthCheck();
        res.json(health);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });
  },
  
  // Add hooks to all collections
  extendCollectionConfig: (config: any) => {
    return {
      ...config,
      hooks: {
        ...config.hooks,
        beforeChange: [
          ...(config.hooks?.beforeChange || []),
          payloadPgIntegration.beforeChange.bind(payloadPgIntegration),
        ],
        afterChange: [
          ...(config.hooks?.afterChange || []),
          payloadPgIntegration.afterChange.bind(payloadPgIntegration),
        ],
      },
    };
  },
});