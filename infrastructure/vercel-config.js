// Vercel Infrastructure Configuration
const { createHash } = require('crypto');

// Environment-specific configurations
const environments = {
  production: {
    regions: ['iad1', 'sfo1', 'lhr1', 'sin1'],
    functions: {
      maxDuration: 30,
      memory: 1024,
      runtime: 'python3.11'
    },
    caching: {
      static: 'public, max-age=31536000, immutable',
      api: 's-maxage=60, stale-while-revalidate=300',
      dynamic: 'no-cache, no-store, must-revalidate'
    },
    security: {
      headers: {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
        'X-Frame-Options': 'DENY',
        'X-Content-Type-Options': 'nosniff',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'camera=(), microphone=(), geolocation=()'
      }
    }
  },
  staging: {
    regions: ['iad1'],
    functions: {
      maxDuration: 30,
      memory: 512,
      runtime: 'python3.11'
    },
    caching: {
      static: 'public, max-age=3600',
      api: 's-maxage=30, stale-while-revalidate=60',
      dynamic: 'no-cache'
    }
  },
  preview: {
    regions: ['iad1'],
    functions: {
      maxDuration: 15,
      memory: 256,
      runtime: 'python3.11'
    },
    caching: {
      static: 'public, max-age=300',
      api: 'no-cache',
      dynamic: 'no-cache'
    }
  }
};

// Multi-tenant routing configuration
const generateTenantRoutes = (tenants) => {
  const routes = [];
  
  // API routes for each tenant
  tenants.forEach(tenant => {
    routes.push({
      src: `^https://${tenant}\\.([^.]+\\.[^.]+)/api/(.*)$`,
      dest: `/backend/server.py?tenant=${tenant}&path=$2`,
      headers: {
        'X-Tenant-ID': tenant,
        'X-Forwarded-Host': `${tenant}.$1`
      }
    });
  });
  
  // Static routes for each tenant
  tenants.forEach(tenant => {
    routes.push({
      src: `^https://${tenant}\\.([^.]+\\.[^.]+)/(.*)$`,
      dest: `/frontend/build/$2?tenant=${tenant}`,
      headers: {
        'X-Tenant-ID': tenant
      }
    });
  });
  
  return routes;
};

// Performance optimization configuration
const performanceConfig = {
  webpack: {
    optimization: {
      splitChunks: {
        chunks: 'all',
        cacheGroups: {
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendors',
            chunks: 'all',
            priority: 10,
          },
          react: {
            test: /[\\/]node_modules[\\/](react|react-dom)[\\/]/,
            name: 'react',
            chunks: 'all',
            priority: 20,
          },
          common: {
            name: 'common',
            minChunks: 2,
            chunks: 'all',
            priority: 5,
            reuseExistingChunk: true,
          },
        },
      },
      runtimeChunk: 'single',
      moduleIds: 'deterministic',
      chunkIds: 'deterministic',
    }
  },
  compression: {
    brotli: true,
    gzip: true
  },
  images: {
    formats: ['image/webp', 'image/avif'],
    minimumCacheTTL: 31536000,
    dangerouslyAllowSVG: false
  }
};

// Database migration configuration
const migrationConfig = {
  mongodb: {
    connectionPoolSize: 10,
    maxIdleTimeMS: 30000,
    serverSelectionTimeoutMS: 5000,
    indexes: [
      // Multi-tenant indexes
      { collection: 'users', index: { tenant_id: 1, email: 1 }, unique: true },
      { collection: 'bookings', index: { tenant_id: 1, start_time: 1 } },
      { collection: 'spaces', index: { tenant_id: 1, active: 1 } },
      { collection: 'audit_logs', index: { tenant_id: 1, timestamp: -1 } },
      
      // Performance indexes
      { collection: 'bookings', index: { tenant_id: 1, space_id: 1, start_time: 1 } },
      { collection: 'users', index: { tenant_id: 1, role: 1 } },
      { collection: 'cms_pages', index: { tenant_id: 1, slug: 1 }, unique: true }
    ]
  }
};

// Backup and disaster recovery configuration
const backupConfig = {
  mongodb: {
    schedule: '0 2 * * *', // Daily at 2 AM
    retention: {
      daily: 7,
      weekly: 4,
      monthly: 12
    },
    encryption: true,
    compression: true
  },
  files: {
    schedule: '0 3 * * *', // Daily at 3 AM
    retention: 30,
    destinations: ['s3', 'gcs']
  }
};

// Monitoring and alerting configuration
const monitoringConfig = {
  healthChecks: {
    endpoints: [
      '/api/health',
      '/api/auth/verify',
      '/api/bookings/availability'
    ],
    interval: 60, // seconds
    timeout: 10,  // seconds
    retries: 3
  },
  alerts: {
    responseTime: {
      warning: 2000,  // ms
      critical: 5000  // ms
    },
    errorRate: {
      warning: 1,   // %
      critical: 5   // %
    },
    availability: {
      warning: 99.5,  // %
      critical: 99.0  // %
    }
  },
  metrics: {
    retention: '30d',
    aggregation: '1m',
    exporters: ['prometheus', 'datadog']
  }
};

// Generate Vercel configuration
function generateVercelConfig(environment = 'production') {
  const env = environments[environment];
  const tenants = ['demo', 'coworking', 'university', 'hotel', 'creative', 'residential'];
  
  const config = {
    version: 2,
    name: `claude-platform-${environment}`,
    
    builds: [
      {
        src: 'frontend/package.json',
        use: '@vercel/static-build',
        config: {
          distDir: 'build',
          framework: 'create-react-app',
          buildCommand: 'yarn build'
        }
      },
      {
        src: 'backend/server.py',
        use: '@vercel/python',
        config: {
          maxLambdaSize: '50mb',
          runtime: env.functions.runtime
        }
      }
    ],
    
    routes: [
      // Health check route
      {
        src: '/health',
        dest: '/backend/server.py'
      },
      
      // API routes with tenant context
      {
        src: '/api/(.*)',
        dest: '/backend/server.py',
        headers: {
          'Cache-Control': env.caching.api
        }
      },
      
      // Multi-tenant routes
      ...generateTenantRoutes(tenants),
      
      // Static file routes
      {
        src: '/static/(.*)',
        dest: '/frontend/build/static/$1',
        headers: {
          'Cache-Control': env.caching.static
        }
      },
      
      // Fallback to frontend
      {
        src: '/(.*)',
        dest: '/frontend/build/index.html',
        headers: {
          'Cache-Control': env.caching.dynamic
        }
      }
    ],
    
    functions: {
      'backend/server.py': {
        maxDuration: env.functions.maxDuration,
        memory: env.functions.memory,
        runtime: env.functions.runtime
      }
    },
    
    regions: env.regions,
    
    headers: Object.entries(env.security?.headers || {}).map(([key, value]) => ({
      source: '/(.*)',
      headers: [{ key, value }]
    })),
    
    env: {
      NODE_ENV: environment,
      VERCEL_ENV: environment,
      REACT_APP_API_URL: '@api_url',
      SECRET_KEY: '@secret_key',
      MONGO_URL: '@mongo_url',
      DB_NAME: '@db_name',
      REDIS_URL: '@redis_url'
    },
    
    build: {
      env: {
        SKIP_PREFLIGHT_CHECK: 'true',
        GENERATE_SOURCEMAP: environment !== 'production' ? 'true' : 'false',
        INLINE_RUNTIME_CHUNK: 'false'
      }
    }
  };
  
  return config;
}

// Export configurations
module.exports = {
  generateVercelConfig,
  environments,
  performanceConfig,
  migrationConfig,
  backupConfig,
  monitoringConfig
};